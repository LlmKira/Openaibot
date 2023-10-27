# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import json
import os

import shortuuid
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from llmkira.middleware.chain_box import Chain, AuthReloader, ChainReloader
from llmkira.middleware.env_virtual import EnvManager
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.task import Task, TaskHeader


class ChainFunc(object):
    @staticmethod
    async def auth_chain(task: TaskHeader, func_name: str = "Unknown"):
        """
        认证链重发注册
        """
        _task_forward: TaskHeader = task.copy()
        # 重置路由元数据，添加递归指标
        meta = _task_forward.task_meta.chain(
            name=__receiver__,
            write_back=False,  # 无所谓，因为本地人
            release_chain=True
        )
        meta.verify_uuid = str(shortuuid.uuid()[0:8]).upper()
        # 追加中断
        if meta.limit_child <= 1:
            return None
        # 注册本地部署点
        task_id = await AuthReloader(uid=_task_forward.receiver.uid).add_auth(
            chain=Chain(
                uuid=meta.verify_uuid,
                uid=_task_forward.receiver.uid,
                address=__receiver__,  # 重要：转发回来这里
                arg=TaskHeader(
                    sender=_task_forward.sender,
                    receiver=_task_forward.receiver,
                    task_meta=meta,
                    message=[]
                )
            )
        )
        # 通知用户重发，不写回，不释放链条
        task_meta = meta.copy(deep=True)
        task_meta.write_back = False
        task_meta.release_chain = False
        task_meta.direct_reply = True
        # 上面路由的意思是：什么也不做
        await Task(queue=_task_forward.receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,  # 继承发送者
                receiver=task.receiver,  # 因为可能有转发，所以可以单配
                task_meta=task_meta,
                message=[
                    RawMessage(
                        user_id=_task_forward.receiver.user_id,
                        chat_id=_task_forward.receiver.chat_id,
                        text=f"🔑 Type `/auth {task_id}` to run `{func_name}`"
                             f"\ntry `!auth {task_id}` when no slash command"
                    )
                ]
            )
        )
        del task_meta
        del meta
        return

    @staticmethod
    async def resign_chain(
            task: TaskHeader,
            parent_func: str,
            repeatable: bool,
            deploy_child: int
    ):
        """
        子链孩子函数，请注意，此处为高风险区域，预定一下函数部署点位
        :param task: 任务
        :param parent_func: 父函数
        :param repeatable: 是否可重复
        :param deploy_child: 是否部署子链
        """
        _task_forward: TaskHeader = task.copy()

        # 重置路由元数据，添加递归指标
        meta = _task_forward.task_meta.chain(
            name=__receiver__,
            write_back=True,
            release_chain=True
        )
        # 追加中断
        if meta.limit_child <= 1:
            return None

        # 放弃子链
        if deploy_child == 0:
            logger.debug(f"[112532] Function {parent_func} End its chain...")
            return None
        _task_forward.task_meta = meta
        # 禁用子链使用出现过的函数
        try:
            if not repeatable:
                _task_forward.task_meta.function_list = [
                    item
                    for item in _task_forward.task_meta.function_list
                    if item.name != parent_func
                ]
        except Exception as e:
            logger.error(e)
            logger.warning(f"[362211]Remove function {parent_func} failed")
        # 注册部署点
        await ChainReloader(uid=_task_forward.receiver.uid).add_task(
            chain=Chain(
                uid=_task_forward.receiver.uid,
                address=_task_forward.receiver.platform,
                expire=60 * 60 * 2,
                arg=TaskHeader(
                    sender=_task_forward.sender,
                    receiver=_task_forward.receiver,
                    task_meta=meta,
                    message=[]
                )
            )
        )


class FunctionReceiver(object):
    """
    receive message from telegram
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    async def deal_message(self, message: AbstractIncomingMessage):
        """
        处理message
        :param message:
        :return:
        """
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
        _tool_obj = _tool_cls()
        if _tool_obj.require_auth:
            if not _task.task_meta.verify_uuid:
                await ChainFunc.auth_chain(task=_task, func_name=func_message.function_call.name)
                logger.warning(
                    f"[x] Function \n--auth-require {func_message.function_call.name} require."
                )
                return None
            else:
                _task.task_meta.verify_uuid = None
        # 订购回复
        await ChainFunc.resign_chain(
            task=_task,
            parent_func=func_message.function_call.name,
            repeatable=_tool_obj.repeatable,
            deploy_child=_tool_obj.deploy_child,
        )
        _env_dict = await EnvManager.from_uid(uid=_task.receiver.uid).get_env_list(name_list=_tool_obj.env_required)
        assert isinstance(_env_dict, dict), "env_dict must be dict"
        # 运行函数
        await _tool_obj.load(
            task=_task,
            receiver=_task.receiver,
            arg=_arg,
            env=_env_dict
        )

    async def on_message(self, message: AbstractIncomingMessage):
        """
        处理message
        :param message:
        :return:
        """
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
