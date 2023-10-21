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
from typing import Optional

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from llmkira.middleware.chain_box import Chain, ChainReloader
from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.schema import RawMessage
from llmkira.sdk.error import RateLimitError
from llmkira.sdk.func_calling import ToolRegister
from llmkira.task import Task, TaskHeader


class BaseSender(object, metaclass=ABCMeta):
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
    async def llm_request(llm_agent: OpenaiMiddleware, disable_function: bool = False):
        """
        校验包装，没有其他作用
        """
        try:
            _result = await llm_agent.request_openai(disable_function=disable_function)
            _message = _result.default_message
            logger.debug(f"[x] LLM Message Sent \n--message {_message}")
            assert _message, "message is empty"
            return _result
        except ssl.SSLSyscallError as e:
            logger.error(f"Network ssl error: {e},that maybe caused by bad proxy")
            raise e
        except RateLimitError as e:
            logger.error(f"ApiEndPoint:{e}")
            raise ValueError(f"Authentication expiration, overload or other issues with the Api Endpoint")
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
        :param auto_write_back: 是否将task携带的消息回写进消息池中，如果为False则丢弃task携带消息
        :param intercept_function: 是否拦截函数调用转发到函数处理器
        """
        try:
            llm.build(auto_write_back=auto_write_back)
            try:
                result = await self.llm_request(llm, disable_function=disable_function)
            except Exception as e:
                await self.sender.error(
                    receiver=task.receiver,
                    text=f"🦴 Sorry, your request failed because: {e}"
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

    async def deal_message(self, message):
        """
        处理消息
        """
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        # 没有任何参数
        if _task.task_meta.direct_reply:
            await self.sender.forward(
                receiver=_task.receiver,
                message=_task.message
            )
            return None, None, None
        # 函数重整策略
        functions = []
        if _task.task_meta.function_enable:
            # 继承函数
            functions = _task.task_meta.function_list
            if _task.task_meta.sign_as[0] == 0:
                # 复制救赎
                _task.task_meta.function_salvation_list = _task.task_meta.function_list
                functions = []
                # 重整
                for _index, _message in enumerate(_task.message):
                    _message: RawMessage
                    functions.extend(
                        ToolRegister().filter_pair(key_phrases=_message.text, file_list=_message.file)
                    )
                _task.task_meta.function_list = functions
        if _task.task_meta.sign_as[0] == 0:
            # 容错一层旧节点
            functions.extend(_task.task_meta.function_salvation_list)
        # 构建通信代理
        _llm = OpenaiMiddleware(task=_task, function=functions)
        logger.debug(f"[x] Received Order \n--order {_task.json(indent=2)}")
        # 插件直接转发与重处理
        if _task.task_meta.callback_forward:
            # 手动追加插件产生的线索消息
            _llm.write_back(
                role=_task.task_meta.callback.role,
                name=_task.task_meta.callback.name,
                message_list=_task.message
            )
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
                return _task, _llm, "callback_forward_reprocess"
            # 转发函数
            await self.sender.forward(
                receiver=_task.receiver,
                message=_task.message
            )
            # 同时递交部署点
            return _task, _llm, "callback_forward_reprocess"
        await self._flash(llm=_llm, task=_task, intercept_function=True)
        return None, None, None

    async def on_message(self, message: AbstractIncomingMessage):
        if not self.task or not self.sender:
            raise ValueError("receiver not set core")
        try:
            if os.getenv("LLMBOT_STOP_REPLY") == "1":
                return None
            _task, _llm, _point = await self.deal_message(message)
            # 启动链式函数应答循环
            if _task:
                chain: Chain = await ChainReloader(uid=_task.receiver.uid).get_task()
                if chain:
                    logger.info(f"Catch chain callback\n--callback_send_by {_point}")
                    await Task(queue=chain.address).send_task(task=chain.arg)
        except Exception as e:
            logger.exception(e)
            await message.reject(requeue=False)
        finally:
            await message.ack(multiple=False)
