# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import json
import time

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from schema import TaskHeader
from sdk.endpoint import openai
from sdk.func_call import TOOL_MANAGER, CHAIN_MANAGER, Chain
from task import Task


class ChainFunc(object):
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
        CHAIN_MANAGER.add_task(task=Chain(user_id=str(_task_forward.receiver.user_id),
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

    async def on_message(self, message: AbstractIncomingMessage):
        await message.ack()
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        # 没有任何参数
        if not _task.task_meta.parent_call:
            return None

        _function: openai.OpenaiResult = openai.OpenaiResult.parse_obj(_task.task_meta.parent_call)
        message = _function.default_message
        if not message.function_call:
            return None
        logger.debug("[x] Received Function %r" % message.function_call.name)
        # 运行函数
        _arg = json.loads(message.function_call.arguments)
        _tool = TOOL_MANAGER.get_tool(message.function_call.name)
        if not _tool:
            logger.warning(f"Not found function {message.function_call.name}")
            return None

        if _tool().require_auth:
            # TODO
            if not _task.task_meta.verify_uuid:
                logger.warning(f"Function {message.function_call.name} require auth but not found verify_uuid")
                pass
                return None

        # 追加步骤
        await ChainFunc.resign_chain(task=_task, ignore_func=message.function_call.name)
        # 运行函数
        await _tool().run(task=_task, receiver=_task.receiver, arg=_arg)
        # 注册区域，必须在run之后
        """
        reload_tool = TOOL_MANAGER.get_tool(name=message.function_call.name)
        if reload_tool:
            logger.info(f"[875521]Chain child callback sent {message.function_call.name}")
            await reload_tool().callback(sign="resign", task=_task)
        """

    async def function(self):
        logger.success("Receiver Runtime:Function Fork Cpu start")
        await self.task.consuming_task(self.on_message)
