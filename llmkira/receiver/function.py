# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import copy
import json
import os
import time

import shortuuid
from aio_pika.abc import AbstractIncomingMessage
from llmkira.middleware.chain_box import Chain, AUTH_MANAGER, CHAIN_MANAGER
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.task import Task, TaskHeader
from loguru import logger


class ChainFunc(object):
    @staticmethod
    async def auth_chain(task: TaskHeader, func_name: str = "Unknown"):
        _task_forward: TaskHeader = task.copy()
        meta = _task_forward.task_meta.child(__receiver__)
        meta.continue_step += 1
        meta.callback_forward = False
        meta.callback_forward_reprocess = False
        meta.verify_uuid = shortuuid.uuid()[0:8]
        # 追加中断
        if meta.limit_child <= 0:
            return None
        _task_forward.task_meta = meta
        # 注册部署点
        task_id = await AUTH_MANAGER.add_auth(
            task=Chain(
                uuid=meta.verify_uuid,
                user_id=str(_task_forward.receiver.user_id),
                address=__receiver__,  # 重要：转发回来这里
                time=int(time.time()),
                arg=TaskHeader(
                    sender=_task_forward.sender,
                    receiver=_task_forward.receiver,
                    task_meta=meta,
                    message=[]
                )
            )
        )
        # 追加任务
        task_meta = copy.deepcopy(meta)
        task_meta.direct_reply = True
        await Task(queue=_task_forward.receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,  # 继承发送者
                receiver=task.receiver,  # 因为可能有转发，所以可以单配
                task_meta=task_meta,
                message=[
                    RawMessage(
                        user_id=_task_forward.receiver.user_id,
                        chat_id=_task_forward.receiver.chat_id,
                        text=f"🔑 Type `/auth {task_id}` to confirm execution of function `{func_name}`"
                    )
                ]
            )
        )
        del task_meta
        return

    @staticmethod
    async def resign_chain(task: TaskHeader, ignore_func):
        _task_forward: TaskHeader = task.copy()
        meta = _task_forward.task_meta.child(__receiver__)
        meta.continue_step += 1
        meta.callback_forward = False
        meta.callback_forward_reprocess = False
        # 追加中断
        if meta.limit_child <= 0:
            return None
        _task_forward.task_meta = meta

        # 禁用子链使用出现过的函数
        try:
            if len(_task_forward.task_meta.function_list) > 2:
                _task_forward.task_meta.function_list = [item for item in _task_forward.task_meta.function_list if
                                                         item.name != ignore_func]
        except Exception as e:
            logger.warning(f"[362211]Remove function {ignore_func} failed")
        # 注册部署点
        await CHAIN_MANAGER.add_task(task=Chain(user_id=str(_task_forward.receiver.user_id),
                                                address=_task_forward.receiver.platform,
                                                time=int(time.time()),
                                                arg=TaskHeader(
                                                    sender=_task_forward.sender,
                                                    receiver=_task_forward.receiver,
                                                    task_meta=meta,
                                                    message=[]
                                                )))  # 追加任务


class FunctionReceiver(object):
    """
    receive message from telegram
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    async def deal_message(self, message: AbstractIncomingMessage):
        if os.getenv("LLMBOT_STOP_REPLY") == "1":
            return None
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        # 没有任何参数
        if not _task.task_meta.parent_call:
            return None

        _function: openai.OpenaiResult = openai.OpenaiResult.parse_obj(_task.task_meta.parent_call)
        func_message = _function.default_message
        if not func_message.function_call:
            return None
        logger.debug(f"[x] Received Function {func_message.function_call.name}")
        # 运行函数
        _arg = json.loads(func_message.function_call.arguments)
        _tool_cls = ToolRegister().get_tool(func_message.function_call.name)
        if not _tool_cls:
            logger.warning(f"Not found function {func_message.function_call.name}")
            return None
        if _tool_cls().require_auth:
            if not _task.task_meta.verify_uuid:
                await ChainFunc.auth_chain(task=_task, func_name=func_message.function_call.name)
                logger.warning(
                    f"[x] Function \n--auth-require {func_message.function_call.name} require."
                )
                return None
            else:
                _task.task_meta.verify_uuid = None

        # 追加步骤
        await ChainFunc.resign_chain(task=_task, ignore_func=func_message.function_call.name)
        # 运行函数
        await _tool_cls().run(task=_task, receiver=_task.receiver, arg=_arg)
        # 注册区域，必须在run之后
        """
        reload_tool = .get_tool(name=message.function_call.name)
        if reload_tool:
            logger.info(f"[875521]Chain child callback sent {message.function_call.name}")
            await reload_tool().callback(sign="resign", task=_task)
        """

    async def on_message(self, message: AbstractIncomingMessage):
        try:
            await self.deal_message(message=message)
        except Exception as e:
            logger.error(f"Function Receiver Error {e}")
            await message.reject(requeue=False)
        finally:
            await message.ack(multiple=False)

    async def function(self):
        logger.success("Receiver Runtime:Function Fork Cpu start")
        await self.task.consuming_task(self.on_message)
