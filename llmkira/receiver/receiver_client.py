# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 下午10:48
# @Author  : sudoskys
# @File    : receiver_client.py
# @Software: PyCharm
#####
# This file is not a top-level schematic file!
#####

import os
import ssl
from abc import ABCMeta, abstractmethod
from typing import Optional, Tuple

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from llmkira.error import get_request_error_message
from llmkira.middleware.chain_box import Chain, ChainReloader
from llmkira.middleware.func_reorganize import FunctionReorganize
from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.middleware.service_provider.schema import ProviderException
from llmkira.schema import RawMessage
from llmkira.sdk.error import RateLimitError, ServiceUnavailableError
from llmkira.sdk.openapi.transducer import LoopRunner
from llmkira.task import Task, TaskHeader


class BaseSender(object, metaclass=ABCMeta):

    async def loop_turn_from_openai(self, platform_name, message, locate):
        """
        将 Openai 消息传入 Loop 进行修饰
        此过程将忽略掉其他属性。只留下 content
        """
        loop_runner = LoopRunner()
        trans_loop = loop_runner.get_receiver_loop(platform_name=platform_name)
        _raw_message = RawMessage.from_openai(message=message, locate=locate)
        await loop_runner.exec_loop(
            pipe=trans_loop,
            pipe_arg={
                "message": _raw_message,
            }
        )
        arg: dict = loop_runner.result_pipe_arg
        if not arg.get("message"):
            logger.error("Message Loop Lose Message")
        raw_message: RawMessage = arg.get("message", _raw_message)
        assert isinstance(raw_message, RawMessage), f"message type error {type(raw_message)}"
        return raw_message

    @abstractmethod
    async def file_forward(self, receiver, file_list, **kwargs):
        pass

    @abstractmethod
    async def forward(self, receiver, message, **kwargs):
        """
        插件专用转发，是Task通用类型
        """
        pass

    @abstractmethod
    async def reply(self, receiver, message, **kwargs):
        """
        模型直转发，Message是Openai的类型
        """
        pass

    @abstractmethod
    async def error(self, receiver, text, **kwargs):
        pass

    @abstractmethod
    async def function(self, receiver, task, llm, result, message, **kwargs):
        pass


class BaseReceiver(object):
    def __init__(self):
        self.sender: Optional[BaseSender] = None
        self.task: Optional[Task] = None

    def set_core(self, sender: BaseSender, task: Task):
        self.sender = sender
        self.task = task

    @staticmethod
    async def llm_request(llm_agent: OpenaiMiddleware, auto_write_back: bool = True, disable_function: bool = False):
        """
        Openai请求
        :param llm_agent: Openai中间件
        :param auto_write_back: 是否将task携带的消息回写进消息池中，如果为False则丢弃task携带消息
        :param disable_function: 是否禁用函数，这个参数只是用于
        校验包装，没有其他作用
        """
        try:
            _result = await llm_agent.request_openai(auto_write_back=auto_write_back, disable_function=disable_function)
            _message = _result.default_message
            logger.debug(f"[x] LLM Message Sent \n--message {_message}")
            assert _message, "message is empty"
            return _result
        except ssl.SSLSyscallError as e:
            logger.error(f"[Network ssl error] {e},that maybe caused by bad proxy")
            raise e
        except ServiceUnavailableError as e:
            logger.error(f"[Service Unavailable Error] {e}")
            raise e
        except RateLimitError as e:
            logger.error(f"ApiEndPoint:{e}")
            raise ValueError(f"Authentication expiration, overload or other issues with the Api Endpoint")
        except ProviderException as e:
            logger.error(f"[Service Provider]{e}")
            raise e
        except Exception as e:
            logger.exception(e)
            raise e

    async def _flash(self,
                     task: TaskHeader,
                     llm: OpenaiMiddleware,
                     auto_write_back: bool = True,
                     intercept_function: bool = False,
                     disable_function: bool = False
                     ):
        """
        函数池刷新
        :param intercept_function: 是否拦截函数调用转发到函数处理器
        """
        try:
            try:
                result = await self.llm_request(llm, auto_write_back=auto_write_back, disable_function=disable_function)
            except Exception as e:
                await self.sender.error(
                    receiver=task.receiver,
                    text=get_request_error_message(str(e))
                )
                return
            if intercept_function:
                # 拦截函数调用
                if hasattr(result.default_message, "function_call"):
                    return await self.sender.function(
                        receiver=task.receiver,
                        task=task,
                        llm=llm,  # IMPORTANT
                        message=result.default_message,
                        result=result
                    )
            return await self.sender.reply(
                receiver=task.receiver,
                message=[result.default_message]
            )
        except Exception as e:
            raise e

    async def deal_message(self, message) -> Tuple[
        Optional[TaskHeader], Optional[OpenaiMiddleware], Optional[str], Optional[bool]
    ]:
        """
        处理消息
        """
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        # 函数组建，自动过滤拉黑后的插件和错误过多的插件
        functions = await FunctionReorganize(task=_task).build()
        # 构建通信代理
        _llm = OpenaiMiddleware(task=_task, function=functions)  # 传入函数表
        logger.debug(f"[x] Received Order \n--order {_task.json(indent=2, ensure_ascii=False)}")
        # 回写
        if _task.task_meta.write_back:
            _llm.write_back(
                role=_task.task_meta.callback.role,
                name=_task.task_meta.callback.name,
                message_list=_task.message
            )
        # 没有任何参数
        if _task.task_meta.direct_reply:
            await self.sender.forward(
                receiver=_task.receiver,
                message=_task.message
            )
            return _task, None, "direct_reply", _task.task_meta.release_chain
        # 插件直接转发与重处理
        if _task.task_meta.callback_forward:
            # 插件数据响应到前端
            if _task.task_meta.callback_forward_reprocess:
                # 手动写回则禁用从 Task 数据体自动回写
                # 防止AI去启动其他函数，禁用函数
                await self._flash(
                    llm=_llm,
                    task=_task,
                    intercept_function=True,
                    disable_function=True,
                    auto_write_back=False
                )
                # 同时递交部署点
                return _task, _llm, "callback_forward_reprocess", _task.task_meta.release_chain
            # 转发函数
            await self.sender.forward(
                receiver=_task.receiver,
                message=_task.message
            )
            # 同时递交部署点
            return _task, _llm, "callback_forward", _task.task_meta.release_chain
        await self._flash(llm=_llm, task=_task, intercept_function=True)
        return _task, None, "default", _task.task_meta.release_chain

    async def on_message(self, message: AbstractIncomingMessage):
        if not self.task or not self.sender:
            raise ValueError("receiver not set core")
        try:
            if os.getenv("LLMBOT_STOP_REPLY") == "1":
                return None

            # 处理消息
            task, llm, point, release = await self.deal_message(message)
            # 启动链式函数应答循环
            if release and task:
                chain: Chain = await ChainReloader(uid=task.receiver.uid).get_task()
                if chain:
                    await Task(queue=chain.address).send_task(task=chain.arg)
                    logger.info(f"🧀 Chain point release\n--callback_send_by {point}")

        except Exception as e:
            logger.exception(e)
            await message.reject(requeue=False)
        else:
            await message.ack(multiple=False)
