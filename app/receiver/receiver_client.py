# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 下午10:48
# @Author  : sudoskys
# @File    : receiver_client.py
# @Software: PyCharm
#####
# This file is not a top-level schematic file!
#####
import asyncio
import os
import time
from abc import ABCMeta, abstractmethod
from typing import Optional, Tuple, List, Dict

import shortuuid
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger
from telebot import formatting

from app.components import read_user_credential
from app.components.credential import global_credential
from app.middleware.llm_task import OpenaiMiddleware
from llmkira.kv_manager.env import EnvManager
from llmkira.openai import OpenaiError, NetworkError
from llmkira.openai.cell import ToolCall, Message, Tool
from llmkira.openai.request import OpenAIResult
from llmkira.openapi.fuse import get_error_plugin
from llmkira.openapi.hook import run_hook, Trigger
from llmkira.sdk.tools import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Location, EventMessage, Router
from llmkira.task.snapshot import global_snapshot_storage


class UserLocks:
    def __init__(self):
        self.locks = {}
        self.locks_lock = asyncio.Lock()

    async def get(self, user_id):
        async with self.locks_lock:
            if user_id not in self.locks:
                self.locks[user_id] = asyncio.Lock()
            return self.locks[user_id]


# UserLocks 的实例
user_locks = UserLocks()


async def generate_authorization(
    secrets: Dict, tool_invocation: ToolCall
) -> Tuple[dict, list, bool]:
    """
    生成授权
    :param secrets: 用户ID
    :param tool_invocation: 工具调用
    :return: 授权字典，消息列表，是否静默
    """
    authorization_map = {}
    tool_object = ToolRegister().get_tool(tool_invocation.name)

    if not tool_object:
        logger.warning(f"Function not found {tool_invocation.name()}")
        return (
            authorization_map,
            ["🍩 [Unknown]" + f" `{tool_invocation.name}` "],
            False,
        )

    tool = tool_object()  # 实例化
    icon = "🌟"
    env_map = {name: secrets.get(name, None) for name in tool.env_list}
    if tool.require_auth(env_map):
        icon = "🔐"
        auth_key = str(shortuuid.uuid()[0:5].upper())
        authorization_map[auth_key] = tool_invocation
        logger.trace(f"🔐 Auth Map {authorization_map}")

    function_tips = [
        f"{icon} [ActionBlock] `{tool_invocation.name}` ",
        f"""```json\n{tool_invocation.arguments}\n```""" if not tool.silent else "",
    ]

    if tool.env_required:
        missing_env_vars = [
            name for name in tool.env_list if not secrets.get(name, None)
        ]
        escaped_env_vars = [
            f"`{formatting.escape_markdown(name)}`" for name in missing_env_vars
        ]
        if escaped_env_vars:
            function_tips.append(f"🦴 Env required:  {','.join(escaped_env_vars)} ")
        help_docs = tool.env_help_docs(missing_env_vars)
        if help_docs:
            function_tips.append(help_docs)
    return authorization_map, function_tips, tool.silent


async def reorganize_tools(task: TaskHeader, error_times_limit: int = 10) -> List[Tool]:
    """
    重整工具
    :param task: 任务
    :param error_times_limit: 错误次数限制
    :return: 工具列表
    """
    tools = []
    sign = task.task_sign
    if sign.disable_tool_action:
        return tools
    for message in task.message:
        message: EventMessage
        tools.extend(
            ToolRegister().filter_pair(
                key_phrases=message.text,
                message_raw=message,
                file_list=message.files,
                address=(task.sender, task.receiver),
            )
        )
    broken_tools = get_error_plugin(error_times=error_times_limit)
    for _tool in broken_tools:
        if _tool in tools:
            tools.remove(_tool)
    return tools


class BaseSender(object, metaclass=ABCMeta):
    @staticmethod
    async def hook(platform_name, messages: List[EventMessage], locate: Location):
        """
        :param platform_name: 平台名称
        :param messages: 消息
        :param locate: 位置
        :return: 平台名称，消息，位置
        """
        arg, kwarg = await run_hook(
            Trigger.RECEIVER,
            platform=platform_name,
            messages=messages,
            locate=locate,
        )
        platform_name = kwarg.get("platform", platform_name)
        messages = kwarg.get("messages", messages)
        locate = kwarg.get("locate", locate)
        return platform_name, messages, locate

    @abstractmethod
    async def file_forward(self, receiver: Location, file_list: list):
        raise NotImplementedError

    @abstractmethod
    async def forward(self, receiver: Location, message: list):
        """
        插件专用转发，是Task通用类型
        """
        raise NotImplementedError

    @abstractmethod
    async def reply(
        self, receiver: Location, messages: List[Message], reply_to_message: bool = True
    ):
        """
        模型直转发，Message是Openai的类型
        """
        raise NotImplementedError

    @abstractmethod
    async def error(self, receiver: Location, text: str):
        raise NotImplementedError

    async def push_task_create_message(
        self,
        *,
        receiver: Location,
        llm_result: OpenAIResult,
        tool_calls: List[ToolCall],
    ):
        """
        生成授权
        :param receiver: 接收者
        :param llm_result: Openai结果
        :param tool_calls: 工具调用
        :return: 授权字典
        """
        auth_map = {}
        task_message = [
            f"**💫 Plan** `{llm_result.id[-4:]}` ",
        ]
        total_silent = True
        assert isinstance(tool_calls, list), f"task batch type error {type(tool_calls)}"
        secrets = await EnvManager(user_id=receiver.uid).read_env()
        if not secrets:
            secrets = {}
        # EnvManager 读取用户环境变量
        for tool_call in tool_calls:
            tool_map, message, silent = await generate_authorization(
                tool_invocation=tool_call, secrets=secrets
            )
            auth_map.update(tool_map)
            if not silent:
                total_silent = False
            if isinstance(message, list):
                task_message.extend(message)
        # 拼接消息
        task_message_str = formatting.format_text(*task_message, separator="\n")
        if not total_silent:
            await self.forward(
                receiver=receiver,
                message=[EventMessage(text=task_message_str)],
            )
        return auth_map

    @abstractmethod
    async def function(self, *, receiver, task, llm, llm_result):
        raise NotImplementedError


class BaseReceiver(object):
    def __init__(self):
        self.sender: Optional[BaseSender] = None
        self.task: Optional[Task] = None

    def set_core(self, sender: BaseSender, task: Task):
        self.sender = sender
        self.task = task

    async def _flash(
        self,
        *,
        task: TaskHeader,
        llm: OpenaiMiddleware,
        remember: bool = True,
        intercept_function: bool = False,
        disable_tool: bool = False,
    ):
        """
        函数池刷新
        :param intercept_function: 是否拦截函数调用转发到函数处理器
        :param task: 任务
        :param llm: Openai中间件
        :param remember: 是否记忆
        :param disable_tool: 是否禁用函数
        :return:
        """
        try:
            try:
                credentials = await read_user_credential(user_id=task.receiver.uid)
                if global_credential and not credentials:
                    credentials = global_credential
                assert credentials, "You need to /login first"
                llm_result = await llm.request_openai(
                    remember=remember,
                    disable_tool=disable_tool,
                    credential=credentials,
                )
                assistant_message = llm_result.default_message
                logger.debug(f"Assistant:{assistant_message}")
            except NetworkError as exc:
                await self.sender.error(receiver=task.receiver, text=str(exc))
                if os.getenv("DEBUG"):
                    logger.exception(exc)
                return exc
            except OpenaiError as exc:
                await self.sender.error(receiver=task.receiver, text=exc.message)
                if os.getenv("DEBUG"):
                    logger.exception(exc)
                return exc
            except RuntimeError as exc:
                logger.exception(exc)
                await self.sender.error(
                    receiver=task.receiver,
                    text="Can't get message validate from your history",
                )
                return exc
            except AssertionError as exc:
                logger.exception(exc)
                await self.sender.error(
                    receiver=task.receiver, text=f"Assert {str(exc)}"
                )
                return exc
            except Exception as exc:
                logger.exception(exc)
                await self.sender.error(
                    receiver=task.receiver, text="Unexpected error occurred to me..."
                )
                return exc
            if intercept_function:
                if assistant_message.tool_calls:
                    if assistant_message.content:
                        await self.sender.reply(
                            receiver=task.receiver,
                            messages=[assistant_message],
                            reply_to_message=False,
                        )
                    await self.sender.function(
                        receiver=task.receiver,
                        task=task,
                        llm=llm,
                        llm_result=llm_result,
                    )
                    return logger.debug("Function loop ended")
            return await self.sender.reply(
                receiver=task.receiver, messages=[assistant_message]
            )
        except Exception as e:
            raise e

    async def deal_message(self, task_head: TaskHeader) -> Tuple:
        """
        :param task_head: 任务头
        :return: 任务，中间件，路由类型，是否释放函数快照
        """
        router = task_head.task_sign.router
        # Deliver 直接转发
        if router == Router.DELIVER:
            await self.sender.forward(
                receiver=task_head.receiver, message=task_head.message
            )
            return task_head, None, router, task_head.task_sign.response_snapshot

        tools = await reorganize_tools(task=task_head, error_times_limit=10)
        """函数组建，自动过滤拉黑后的插件和错误过多的插件"""
        if task_head.task_sign.layer == 0:
            task_head.task_sign.tools_ghost.extend(tools)
        else:
            tools.extend(task_head.task_sign.tools_ghost)
        """当首条链确定工具组成后，传递给子链使用"""
        llm_middleware = OpenaiMiddleware(
            task=task_head,
            tools=tools,
        )
        """构建通信代理"""
        logger.trace(f"Received Task:{task_head.model_dump_json(indent=2)}")
        # function_response write back
        if task_head.task_sign.memory_able:
            for response in task_head.task_sign.tool_response:
                tool_msg = response.format_tool_message()
                """消息类型是由请求结果决定的。也就是理论不存在预料外的冲突。"""
                await llm_middleware.remember(message=tool_msg)
                logger.debug(f"Tool Response Write Back:{tool_msg.tool_call_id}")
        if router == Router.REPROCESS:
            # 重处理直接转发
            await self._flash(
                llm=llm_middleware,
                task=task_head,
                intercept_function=True,
                disable_tool=False,
                remember=True,
            )
            return (
                task_head,
                llm_middleware,
                router,
                task_head.task_sign.response_snapshot,
            )
        elif router == Router.REPLIES:
            # 重复消息直接转发
            await self.sender.forward(
                receiver=task_head.receiver, message=task_head.message
            )
            return task_head, None, router, task_head.task_sign.response_snapshot
        elif router == Router.ANSWER:
            # 回答直接转发
            await self._flash(
                task=task_head,
                llm=llm_middleware,
                intercept_function=True,
                remember=True,
            )
            return (
                task_head,
                llm_middleware,
                router,
                task_head.task_sign.response_snapshot,
            )
        else:
            logger.exception(f"Router {router} not implemented")
            await self.sender.forward(
                receiver=task_head.receiver, message=task_head.message
            )
            return task_head, None, router, task_head.task_sign.response_snapshot

    async def on_message(self, message: AbstractIncomingMessage):
        if not self.task or not self.sender:
            raise ValueError("receiver not set core")
        if os.getenv("STOP_REPLY"):
            logger.warning("🚫 STOP_REPLY is set in env, stop reply message")
            return None
        logger.debug(f"Received MQ Message 📩{message.message_id}")
        try:
            task_head: TaskHeader = TaskHeader.model_validate_json(
                json_data=message.body.decode("utf-8")
            )
            logger.debug(f"Received Task:{task_head.model_dump_json(indent=2)}")
            # 处理消息
            async with await user_locks.get(task_head.receiver.uid):
                task_head, llm, router, response_snapshot = await self.deal_message(
                    task_head=task_head
                )
                logger.debug(f"Message Success:Router {router}")
                # 启动链式函数应答循环
                if task_head and response_snapshot:
                    snap_data = await global_snapshot_storage.read(
                        user_id=task_head.receiver.uid
                    )
                    if snap_data is not None:
                        data = snap_data.data
                        renew_snap_data = []
                        for task in data:
                            if task.expire_at < int(time.time()):
                                logger.info(
                                    f"🧀 Expire snapshot {task.snap_uuid} at {router}"
                                )
                                # 跳过过期的任何任务
                                continue
                            # 不是认证任务
                            if not task.snapshot_credential:
                                # 没有被处理
                                if not task.processed:
                                    try:
                                        # await asyncio.sleep(10)
                                        logger.debug(
                                            f"🧀 Send snapshot {task.snap_uuid} at {router}"
                                        )
                                        await Task.create_and_send(
                                            queue_name=task.channel,
                                            task=task.snapshot_data,
                                        )
                                    except Exception as e:
                                        logger.exception(
                                            f"Response to snapshot error {e}"
                                        )
                                    else:
                                        logger.info(
                                            f"🧀 Response to snapshot {task.snap_uuid} at {router}"
                                        )
                                    finally:
                                        task.processed_at = int(time.time())
                                        # renew_snap_data.append(task)
                                else:
                                    # 被处理过的任务。不再处理
                                    pass
                            else:
                                # 认证任务
                                renew_snap_data.append(task)
                        snap_data.data = renew_snap_data
                        await global_snapshot_storage.write(
                            user_id=task_head.receiver.uid, snapshot=snap_data
                        )
        except Exception as e:
            logger.exception(e)
            await message.reject(requeue=False)
        else:
            await message.ack(multiple=False)
