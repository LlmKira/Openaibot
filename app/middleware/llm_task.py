# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
import os
from pprint import pprint
from typing import List, Optional

from loguru import logger
from pydantic import SecretStr

from app.components.credential import Credential
from app.components.user_manager import record_cost
from llmkira.kv_manager.instruction import InstructionManager
from llmkira.kv_manager.time import TimeFeelManager
from llmkira.kv_manager.tool_call import GLOBAL_TOOLCALL_CACHE_HANDLER
from llmkira.memory import global_message_runtime
from llmkira.openai.cell import (
    Tool,
    Message,
    active_cell_string,
    SystemMessage,
    ToolMessage,
    AssistantMessage,
    UserMessage,
)
from llmkira.openai.request import OpenAIResult, OpenAI, OpenAICredential
from llmkira.task import TaskHeader
from llmkira.task.schema import EventMessage


def unique_function(tools: List[Tool]):
    """
    函数去重，禁止同名函数
    """
    _dict = {}
    for function in tools:
        assert isinstance(function, Tool), "llm_task:function type error,cant unique"
        _dict[function.function.name] = function
    functions = list(_dict.values())
    if len(functions) != len(tools):
        logger.warning("llm_task:Tool name is not unique")
    return functions


def mock_tool_message(assistant_message: AssistantMessage, mock_content: str):
    _tool_message = []
    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            _tool_message.append(
                ToolMessage(content=mock_content, tool_call_id=tool_call.id)
            )
    return _tool_message


async def validate_mock(messages: List[Message]):
    """
    所有的具有 tool_calls 的 AssistantMessage 后面必须有对应的 ToolMessage 响应，其他消息类型按照原顺序
    """
    map_cache = {}
    paired_messages = []
    # 缓存已经存在的 ToolMessage
    for message in messages:
        if isinstance(message, AssistantMessage):
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    map_cache[tool_call.id] = AssistantMessage(
                        content=message.content, tool_calls=[tool_call]
                    )
    # 激活 ToolMessage
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_call_id = message.tool_call_id
            if tool_call_id in map_cache:
                paired_assistant_message = map_cache[tool_call_id]
            else:
                tool_call_origin = await GLOBAL_TOOLCALL_CACHE_HANDLER.get_toolcall(
                    tool_call_id
                )
                if tool_call_origin:
                    paired_assistant_message = AssistantMessage(
                        content=None, tool_calls=[tool_call_origin]
                    )
                else:
                    paired_assistant_message = None
            if paired_assistant_message:
                paired_messages.append(paired_assistant_message)
                paired_messages.append(message)
            else:
                logger.error(f"llm_task:ToolCall not found {tool_call_id}, skip")
        else:
            paired_messages.append(message)

    # 删除没有被响应的 AssistantMessage
    def pair_check(_messages):
        new_list = []
        for i in range(len(_messages) - 1):
            if isinstance(_messages[i], AssistantMessage) and _messages[i].tool_calls:
                if isinstance(_messages[i + 1], ToolMessage):
                    new_list.append(_messages[i])
            else:
                new_list.append(_messages[i])
        new_list.append(_messages[-1])
        if isinstance(_messages[-1], AssistantMessage) and _messages[-1].tool_calls:
            logger.warning("llm_task:the last AssistantMessage not paired, be careful")
            new_list.extend(mock_tool_message(_messages[-1], "[On Queue]"))
        return new_list

    final_messages = pair_check(paired_messages)
    if len(final_messages) != len(messages):
        # 获取被删除的 AssistantMessage
        diff = [msg for msg in messages if msg not in final_messages]
        logger.debug(f"llm_task:validate_mock cache, delete:{diff}")
    return final_messages


class OpenaiMiddleware(object):
    """
    Openai Middleware get response from Openai
    """

    def __init__(
        self,
        task: TaskHeader,
        tools: List[Tool] = None,
    ):
        assert isinstance(task, TaskHeader), "Task should be TaskHeader"
        self.tools: List[Tool] = unique_function(tools)
        self.task = task
        session_uid = task.receiver.uid
        self.session_uid = session_uid
        self.message_history = global_message_runtime.update_session(
            session_id=session_uid
        )

    async def remember(self, *, message: Optional[Message] = None):
        """
        写回消息到历史消息
        """
        if message:
            await self.message_history.append(messages=[message])

    async def build_history_messages(self):
        """
        从任务会话和历史消息中构建消息
        :return: None
        """
        system_prompt = await InstructionManager(
            user_id=self.session_uid
        ).read_instruction()
        message_run = []
        if isinstance(system_prompt, str):
            message_run.append(SystemMessage(content=system_prompt))
        history = await self.message_history.read(lines=8)
        logger.trace(f"History message {history}")
        for de_active_message in history:
            try:
                msg = active_cell_string(de_active_message)
            except Exception as ex:
                logger.error(f"llm_task:build_message error {ex}")
                continue
            else:
                message_run.append(msg)
        return message_run

    async def build_task_messages(self, remember=True):
        """
        从任务会话和历史消息中构建消息
        :param remember: 是否写入历史消息
        :return: None
        """
        message_run = []
        # 处理 人类 发送的消息
        task_message = self.task.message
        task_message: List[EventMessage]
        for i, message in enumerate(task_message):
            message: EventMessage
            # message format
            user_message = await message.format_user_message()
            message_run.append(user_message)
            if remember:
                await self.message_history.append(messages=[user_message])
        return message_run

    async def request_openai(
        self,
        remember: bool,
        credential: Credential,
        disable_tool: bool = False,
    ) -> OpenAIResult:
        """
        处理消息转换和调用工具
        :param remember: 是否自动写回
        :param disable_tool: 禁用函数
        :param credential: 凭证
        :return: OpenaiResult 返回结果
        :raise RuntimeError: 消息为空
        :raise AssertionError: 无法处理消息
        :raise OpenaiError: Openai错误
        """
        # 添加系统提示
        messages = []
        tools = [tool for tool in self.tools if isinstance(tool, Tool)]
        if len(tools) != len(self.tools):
            logger.warning(f"llm_task:Tool is not unique {self.tools}")
        if isinstance(self.task.task_sign.instruction, str):
            messages.append(SystemMessage(content=self.task.task_sign.instruction))
        # 先读取历史消息才能操作
        message_head = await self.build_history_messages()
        messages.extend(message_head)  # 历史消息
        # 操作先写入一个状态
        time_feel = await TimeFeelManager(self.session_uid).get_leave()
        if time_feel:
            messages.append(
                SystemMessage(content=f"statu:[After {time_feel} leave, user is back]")
            )  # 插入消息
            await self.remember(
                message=SystemMessage(
                    content=f"statu:[After {time_feel} leave, user is back]"
                )
            )
        # 同步状态到历史消息
        message_body = await self.build_task_messages(remember=remember)
        messages.extend(message_body)

        # TODO:实现消息时序切片
        # 日志
        logger.info(
            f"Request Details:"
            f"\n--message {len(messages)} "
            f"\n--tools {tools} "
            f"\n--model {credential.api_model}"
        )
        for msg in messages:
            if isinstance(msg, UserMessage):
                if len(str(msg)) < 100:
                    logger.debug(f"Message: {msg}")
                else:
                    logger.debug("Message: UserMessage")
            else:
                logger.debug(f"Message:{msg}")
        # 必须校验
        if disable_tool or not tools:
            logger.debug("llm_task:no tool loaded")
            tools = None
        # 根据模型选择不同的驱动
        assert messages, RuntimeError("llm_task:message cant be none...")
        messages = await validate_mock(messages)
        endpoint: OpenAI = OpenAI(
            messages=messages, tools=tools, model=credential.api_model
        )
        # 调用Openai
        try:
            result: OpenAIResult = await endpoint.request(
                session=OpenAICredential(
                    api_key=SecretStr(credential.api_key),
                    base_url=credential.api_endpoint,
                )
            )
        except Exception as e:
            if os.getenv("DEBUG"):
                pprint(messages)
            logger.error(f"llm_task:Openai request error {e}")
            raise e
        _message = result.default_message
        _usage = result.usage.total_tokens
        await record_cost(
            cost_model=credential.api_model,
            cost_token=_usage,
            endpoint=credential.api_endpoint,
            user_id=self.session_uid,
        )
        # 写回数据库
        await self.remember(message=_message)
        return result
