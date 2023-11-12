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
from typing import Optional, Tuple, List

import httpx
import shortuuid
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from telebot import formatting

from llmkira.error import get_request_error_message, ReplyNeededError
from llmkira.middleware.chain_box import Chain, ChainReloader
from llmkira.middleware.env_virtual import EnvManager
from llmkira.middleware.func_reorganize import FunctionReorganize
from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.middleware.service_provider.schema import ProviderException
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.error import RateLimitError, ServiceUnavailableError
from llmkira.sdk.func_calling import ToolRegister
from llmkira.sdk.openapi.transducer import LoopRunner
from llmkira.sdk.schema import AssistantMessage, TaskBatch
from llmkira.task import Task, TaskHeader


class BaseSender(object, metaclass=ABCMeta):
    @staticmethod
    async def loop_turn_from_openai(platform_name, message, locate):
        """
        将 Openai 消息传入 Receiver Loop 进行修饰
        此过程将忽略掉其他属性。只留下 content
        """
        loop_runner = LoopRunner()
        trans_loop = loop_runner.get_receiver_loop(platform_name=platform_name)
        _raw_message = RawMessage.format_openai_message(
            message=message,
            locate=locate
        )
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
    async def file_forward(self, receiver, file_list):
        raise NotImplementedError

    @abstractmethod
    async def forward(self, receiver, message):
        """
        插件专用转发，是Task通用类型
        """
        raise NotImplementedError

    @abstractmethod
    async def reply(self, receiver, message, reply_to_message: bool = True):
        """
        模型直转发，Message是Openai的类型
        """
        raise NotImplementedError

    @abstractmethod
    async def error(self, receiver, text):
        raise NotImplementedError

    async def push_task_create_message(self,
                                       *,
                                       receiver,
                                       task,
                                       llm_result: LlmResult,
                                       task_batch: List[TaskBatch]
                                       ):
        auth_map = {}

        async def _action_block(_task_batch: TaskBatch) -> Tuple[List[str], bool]:
            _tool = ToolRegister().get_tool(_task_batch.get_batch_name())
            if not _tool:
                logger.warning(f"not found function {_task_batch.get_batch_name()}")
                return [
                    formatting.mbold("🍩 [Unknown]") + f" `{_task_batch.get_batch_name()}` "
                ], False
            tool = _tool()
            icon = "🌟"
            if tool.require_auth:
                icon = "🔐"
                auth_map[str(shortuuid.uuid()[0:5]).upper()] = _task_batch
                logger.trace(f"🔐 Auth Map {auth_map}")
            _func_tips = [
                formatting.mbold(f"{icon} [ActionBlock]") + f" `{_task_batch.get_batch_name()}` ",
                f"""```\n{_task_batch.get_batch_args()}\n```""" if not tool.silent else "",
            ]
            if tool.env_required:
                __secret__ = await EnvManager.from_uid(
                    uid=task.receiver.uid
                ).get_env_list(name_list=tool.env_required)
                # 查找是否有空
                _required_env = [
                    name
                    for name in tool.env_required
                    if not __secret__.get(name, None)
                ]
                _need_env_list = [
                    f"`{formatting.escape_markdown(name)}`"
                    for name in _required_env
                ]
                _need_env_str = ",".join(_need_env_list)
                _func_tips.append(formatting.mbold("🦴 Env required:") + f" {_need_env_str} ")
                help_docs = tool.env_help_docs(_required_env)
                _func_tips.append(formatting.mitalic(help_docs))
            return _func_tips, tool.silent

        task_message = [
            formatting.mbold("💫 Plan") + f" `{llm_result.id[-4:]}` ",
        ]
        total_silent = True
        assert isinstance(task_batch, list), f"task batch type error {type(task_batch)}"
        for _task_batch in task_batch:
            _message, _silent = await _action_block(_task_batch=_task_batch)
            if not _silent:
                total_silent = False
            if isinstance(_message, list):
                task_message.extend(_message)
        task_message_str = formatting.format_text(
            *task_message,
            separator="\n"
        )
        if not total_silent:
            await self.forward(receiver=receiver,
                               message=[
                                   RawMessage(
                                       text=task_message_str,
                                       only_send_file=False
                                   )
                               ]
                               )
        return auth_map

    @abstractmethod
    async def function(self,
                       *,
                       receiver,
                       task,
                       llm,
                       llm_result
                       ):
        raise NotImplementedError


class BaseReceiver(object):
    def __init__(self):
        self.sender: Optional[BaseSender] = None
        self.task: Optional[Task] = None

    def set_core(self, sender: BaseSender, task: Task):
        self.sender = sender
        self.task = task

    @staticmethod
    async def llm_request(
            *,
            llm_agent: OpenaiMiddleware,
            auto_write_back: bool = True,
            retrieve_message: bool = False,
            disable_function: bool = False
    ):
        """
        Openai请求
        :param llm_agent: Openai中间件
        :param auto_write_back: 是否将task携带的消息回写进消息池中，如果为False则丢弃task携带消息
        :param disable_function: 是否禁用函数
        :param retrieve_message: 是否检索消息
        :return: OpenaiResult
        校验包装，没有其他作用
        """
        try:
            _result = await llm_agent.request_openai(
                auto_write_back=auto_write_back,
                disable_function=disable_function,
                retrieve_mode=retrieve_message
            )
            return _result
        except ssl.SSLSyscallError as e:
            logger.error(f"[Network ssl error] {e},that maybe caused by bad proxy")
            raise Exception(e)
        except httpx.RemoteProtocolError as e:
            logger.error(f"[Network RemoteProtocolError] {e}")
            raise ReplyNeededError(message=f"Server disconnected without sending a response.")
        except ServiceUnavailableError as e:
            logger.error(f"[Service Unavailable Error] {e}")
            raise ReplyNeededError(message=f"[551721]Service Unavailable {e}")
        except RateLimitError as e:
            logger.error(f"ApiEndPoint:{e}")
            raise ReplyNeededError(message=f"[551580]Rate Limit Error {e}")
        except ProviderException as e:
            logger.info(f"[Service Provider]{e}")
            raise ReplyNeededError(message=f"[551183]Service Provider Error {e}")
        except PydanticValidationError as e:
            logger.exception(e)
            raise ReplyNeededError(message=f"[551684]Request Data ValidationError")
        except Exception as e:
            logger.exception(e)
            raise e

    async def _flash(self,
                     *,
                     task: TaskHeader,
                     llm: OpenaiMiddleware,
                     auto_write_back: bool = True,
                     intercept_function: bool = False,
                     retrieve_message: bool = False,
                     disable_function: bool = False
                     ):
        """
        函数池刷新
        :param intercept_function: 是否拦截函数调用转发到函数处理器
        :param retrieve_message: 是否检索消息
        :param task: 任务
        :param llm: Openai中间件
        :param auto_write_back: 是否自动写回
        :param disable_function: 是否禁用函数
        :return:
        """
        try:
            try:
                _llm_result = await self.llm_request(
                    llm_agent=llm,
                    auto_write_back=auto_write_back,
                    disable_function=disable_function,
                    retrieve_message=retrieve_message
                )
                get_message = _llm_result.default_message
                logger.debug(f"[x] LLM Message Sent \n--message {get_message}")
                if not isinstance(get_message, AssistantMessage):
                    raise ReplyNeededError("[55682]Request Result Not Valid, Must Be `AssistantMessage`")
            except Exception as e:
                if isinstance(e, ReplyNeededError):
                    await self.sender.error(
                        receiver=task.receiver,
                        text=get_request_error_message(str(e))
                    )
                raise e
            if intercept_function:
                if get_message.sign_function:
                    await self.sender.reply(
                        receiver=task.receiver,
                        message=[get_message],
                        reply_to_message=False
                    )
                    await self.sender.function(
                        receiver=task.receiver,
                        task=task,
                        llm=llm,  # IMPORTANT
                        llm_result=_llm_result
                    )
                    return logger.debug("Function loop ended")
            return await self.sender.reply(
                receiver=task.receiver,
                message=[get_message]
            )
        except Exception as e:
            raise e

    async def deal_message(self, message) -> Tuple[
        Optional[TaskHeader], Optional[OpenaiMiddleware], Optional[str], Optional[bool]
    ]:
        """
        处理消息
        """
        logger.debug(f"[x] Received Message \n--message {message.body}")
        _task: TaskHeader = TaskHeader.model_validate_json(message.body.decode("utf-8"))
        # 没有任何参数
        if _task.task_meta.direct_reply:
            await self.sender.forward(
                receiver=_task.receiver,
                message=_task.message
            )
            return _task, None, "direct_reply", _task.task_meta.release_chain

        functions = await FunctionReorganize(task=_task).build_arg()
        """函数组建，自动过滤拉黑后的插件和错误过多的插件"""
        try:
            _llm = OpenaiMiddleware(
                task=_task,
                functions=functions,
                tools=[]
                # 内部会初始化函数工具，这里是其他类型工具
            ).init()
        except ProviderException as e:
            await self.sender.error(
                receiver=_task.receiver,
                text=f"🥞 Auth System Report {formatting.escape_markdown(str(e))}"
            )
            raise e
        """构建通信代理"""
        schema = _llm.get_schema()
        logger.debug(f"[x] Received Order \n--order {_task.model_dump_json()}")
        # function_response write back
        if _task.task_meta.write_back:
            for call in _task.task_meta.callback:
                if schema.func_executor == "tool_call":
                    _func_tool_msg = call.get_tool_message()
                elif schema.func_executor == "function_call":
                    _func_tool_msg = call.get_function_message()
                elif schema.func_executor == "unsupported":
                    _func_tool_msg = None
                else:
                    raise NotImplementedError(f"func_executor {schema.func_executor} not implemented")
                """消息类型是由请求结果决定的。也就是理论不存在预料外的冲突。"""

                _llm.write_back(
                    message=_func_tool_msg
                )
                logger.debug(f"[x] Function Response Write Back \n--callback {call.name}")

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
