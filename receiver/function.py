# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import json

from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from schema import TaskHeader
from sdk.func_call import TOOL_MANAGER
from sdk.schema import Message
from task import Task


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
        if not _task.task_meta.parent_call:
            return None
        _function = Message.parse_obj(_task.task_meta.parent_call)
        _function: Message
        if not _function.function_call:
            return None
        logger.info(" [x] Received Function %r" % _function.function_call.name)
        # 运行函数
        _arg = json.loads(_function.function_call.arguments)
        _tool = TOOL_MANAGER.get_tool(_function.function_call.name)
        if not _tool:
            logger.warning(f"not found function {_function.function_call.name}")
            return None
        await _tool().run(task=_task, receiver=_task.receiver, arg=_arg)

    async def function(self):
        logger.success("Receiver Runtime:Function Fork Cpu start")
        await self.task.consuming_task(self.on_message)
