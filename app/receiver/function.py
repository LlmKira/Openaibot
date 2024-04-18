# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午7:08
# @Author  : sudoskys
# @File    : function.py
# @Software: PyCharm

__receiver__ = "llm_task"

import os
import time
from typing import Optional

import shortuuid
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger

from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.tool_call import GLOBAL_TOOLCALL_CACHE_HANDLER
from llmkira.openai.cell import ToolCall
from llmkira.sdk.tools.register import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import EventMessage, Location, Sign, Snapshot
from llmkira.task.snapshot import global_snapshot_storage, SnapData


async def append_snapshot(
    snapshot_credential: Optional[str],
    snapshot_data: TaskHeader,
    creator: str,
    channel: str,
    expire_at: int,
):
    """
    添加快照
    """
    snap = await global_snapshot_storage.read(user_id=creator)
    if not snap:
        snap = SnapData(data=[])
    snap_shot = Snapshot(
        snapshot_credential=snapshot_credential,
        snapshot_data=snapshot_data,
        creator=creator,
        channel=channel,
        expire_at=expire_at,
    )
    snap.data.append(snap_shot)
    await global_snapshot_storage.write(user_id=creator, snapshot=snap)
    return snap_shot.snapshot_credential


async def create_snapshot(
    *,
    task: TaskHeader,
    tool_calls_pending_now: ToolCall,
    memory_able: bool,
    channel: str,
    snapshot_credential: Optional[str] = None,
):
    """
    认证链重发注册
    """
    logger.debug(f"Create a snapshot for {task.receiver.platform}")
    task_snapshot = task.model_copy()
    meta: Sign = task_snapshot.task_sign.snapshot(
        name=__receiver__,
        memory_able=memory_able,
        # 不需要记忆
        response_snapshot=True,
        # 要求释放快照
    )
    """添加认证链并重置路由数据"""

    meta.snapshot_credential = meta.get_snapshot_credential(
        tool_calls=tool_calls_pending_now
    )
    """生成验证UUID"""

    snap_shot_task = TaskHeader(
        sender=task_snapshot.sender,
        receiver=task_snapshot.receiver,
        task_sign=meta,
        message=[],
    )
    task_id = await append_snapshot(
        snapshot_credential=snapshot_credential,
        snapshot_data=snap_shot_task,
        channel=channel,
        creator=task_snapshot.receiver.uid,
        expire_at=int(time.time()) + 60 * 2,
    )
    if snapshot_credential:
        logger.debug(f"Create a snapshot {task_id}")
    return snapshot_credential


async def reply_user(platform: str, task: TaskHeader, text: str, receiver: Location):
    """
    仅仅只是通知到用户，不需要LLM处理或组装
    :param platform: Default should be `task.receiver.platform`
    :param task: 任务 header
    :param text: 文本 str
    :param receiver: 接收者 TaskHeader.Location
    """
    return await Task.create_and_send(
        queue_name=platform,
        task=TaskHeader(
            sender=task.sender,
            receiver=receiver,
            task_sign=task.task_sign.notify(
                plugin_name=__receiver__, response_snapshot=False, memory_able=False
            ),
            message=[
                EventMessage(
                    user_id=task.receiver.user_id,
                    chat_id=task.receiver.chat_id,
                    text=text,
                )
            ],
        ),
    )


class FunctionReceiver(object):
    """
    receive message from any platform
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    @staticmethod
    async def run_pending_task(task: TaskHeader, pending_task: ToolCall):
        """
        如果执行异常，必须抛出异常，否则会导致任务无法结束
        如果重发认证，不需要结束任务
        :param task: 任务
        :param pending_task: 待执行的函数
        :return: None
        :raise ModuleNotFoundError: 没有找到 Tool
        """
        # Get Function Object
        tool_cls = ToolRegister().get_tool(name=pending_task.name)
        if not tool_cls:
            logger.warning(f"Not found function {pending_task.name}")
            await reply_user(
                platform=task.receiver.platform,
                receiver=task.receiver,
                task=task,
                text=f"🔭 Sorry function `{pending_task.name}` executor not found...",
            )
            raise ModuleNotFoundError(f"Function {pending_task.name} not found")
        await GLOBAL_TOOLCALL_CACHE_HANDLER.save_toolcall(
            tool_call=pending_task, tool_call_id=pending_task.id
        )
        logger.debug(f"Save ToolCall {pending_task.id} to Cache Map")
        # Run Function
        _tool_obj = tool_cls()

        # Get Env
        secrets = await EnvManager(user_id=task.receiver.uid).read_env()
        if not secrets:
            secrets = {}
        env_map = {name: secrets.get(name, None) for name in _tool_obj.env_list}
        # Auth
        if _tool_obj.require_auth(env_map):
            if task.task_sign.snapshot_credential:
                # 是携带密钥的函数，是预先构建的可信任务头
                task.task_sign.snapshot_credential = None
            else:
                snapshot_credential = str(shortuuid.uuid()).upper()[:5]
                # 创建 snapshot_credential 并创建函数快照
                task_id = await create_snapshot(
                    task=task,
                    tool_calls_pending_now=pending_task,
                    memory_able=False,
                    channel=__receiver__,
                    snapshot_credential=snapshot_credential,
                )
                # 通知
                await reply_user(
                    platform=task.receiver.platform,
                    receiver=task.receiver,
                    task=task,
                    text=f"🔑 Type `/auth {task_id}` to run `{pending_task.name}`"
                    f"\ntry `!auth {task_id}` when no slash command",
                )
                return logger.info(
                    f"[Snapshot Auth] \n--auth-require {pending_task.name} require."
                )

        # Resign Chain
        if len(task.task_sign.tool_calls_pending) == 1:
            logger.debug("ToolCall run out, resign a new request to request stop sign.")
            await create_snapshot(
                task=task,
                tool_calls_pending_now=pending_task,
                memory_able=True,
                channel=task.receiver.platform,
            )
            # 运行函数, 传递模型的信息，以及上一条的结果的openai raw信息
        run_result = await _tool_obj.load(
            task=task,
            receiver=task.receiver,
            arg=pending_task.arguments,
            env=env_map,
            pending_task=pending_task,
            refer_llm_result=task.task_sign.llm_response,
        )
        # 更新任务状态
        await task.task_sign.complete_task(
            tool_calls=pending_task, success_or_not=True, run_result=run_result
        )
        return run_result

    async def process_function_call(self, message: AbstractIncomingMessage):
        """
        定位，解析，运行函数。要求认证，或申请结束/继续指标。
        :param message: message from queue
        :return: None
        """
        if os.getenv("STOP_REPLY"):
            logger.warning("🚫 STOP_REPLY is set in env, stop reply message")
            return None
        logger.debug(
            f"[552351] Received A Function Call from {message.body.decode('utf-8')}"
        )
        task: TaskHeader = TaskHeader.model_validate_json(message.body.decode("utf-8"))
        # Get Function Call
        pending_task: ToolCall = await task.task_sign.get_pending_tool_call(
            tool_calls_pending_now=task.task_sign.snapshot_credential,
            return_default_if_empty=True,
        )
        if not pending_task:
            return logger.debug("But No ToolCall")
        logger.debug("Received A ToolCall")
        try:
            await self.run_pending_task(task=task, pending_task=pending_task)
        except Exception as e:
            await task.task_sign.complete_task(
                tool_calls=pending_task, success_or_not=False, run_result=str(e)
            )
            logger.error(f"Function Call Error {e}")
            raise e
        finally:
            logger.trace("Function Call Finished")

    async def on_message(self, message: AbstractIncomingMessage):
        """
        处理message
        :param message: message from queue
        :return: None
        """
        try:
            await self.process_function_call(message=message)
        except Exception as e:
            logger.exception(f"Function Receiver Error:{e}")
            await message.reject(requeue=False)
            raise e
        else:
            await message.ack(multiple=False)

    async def function(self):
        logger.success("Receiver Runtime:Function Fork Cpu start")
        await self.task.consuming_task(self.on_message)
