# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
from typing import List, Optional

from loguru import logger
from pydantic import SecretStr

from app.components.credential import Credential
from app.components.user_manager import record_cost
from llmkira.kv_manager.instruction import InstructionManager
from llmkira.memory import global_message_runtime
from llmkira.openai.cell import Tool, Message, active_cell_string, SystemMessage
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

    async def build_message(self, remember=True):
        """
        从任务会话和历史消息中构建消息
        :param remember: 是否写入历史消息
        :return: None
        """
        system_prompt = await InstructionManager(
            user_id=self.session_uid
        ).read_instruction()
        message_run = []
        if isinstance(system_prompt, str):
            message_run.append(SystemMessage(content=system_prompt))
        history = await self.message_history.read(lines=10)
        for de_active_message in history:
            try:
                msg = active_cell_string(de_active_message)
            except Exception as ex:
                logger.error(f"llm_task:build_message error {ex}")
                continue
            else:
                message_run.append(msg)
        # 处理 人类 发送的消息
        task_message = self.task.message
        task_message: List[EventMessage]
        for i, message in enumerate(task_message):
            message: EventMessage
            # message format
            user_message = message.format_user_message()
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
        :raise RuntimeError: 无法处理消息
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
        messages.extend(await self.build_message(remember=remember))
        # TODO:实现消息时序切片
        # 日志
        logger.info(
            f"[x] Openai request" f"\n--message {messages} " f"\n--tools {tools}"
        )
        # 必须校验
        if disable_tool or not tools:
            logger.debug("llm_task:Tool not enable")
            tools = None
        # 根据模型选择不同的驱动a
        assert messages, RuntimeError("llm_task:message cant be none...")
        endpoint: OpenAI = OpenAI(
            messages=messages, tools=tools, model=credential.api_model
        )
        # 调用Openai
        result: OpenAIResult = await endpoint.request(
            session=OpenAICredential(
                api_key=SecretStr(credential.api_key), base_url=credential.api_endpoint
            )
        )
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
