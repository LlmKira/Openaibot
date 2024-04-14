# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
# @Software: PyCharm
import time
from typing import List, Optional

from loguru import logger
from pydantic import Field, BaseModel

from .llm_provider import GetAuthDriver
from ..extra.user import UserCost, CostControl
from ..extra.user.schema import Cost
from ..schema import RawMessage, Scraper
from ..sdk.adapter import SCHEMA_GROUP, SingleModel
from ..sdk.endpoint.openai import Message, Openai, OpenaiResult
from ..sdk.endpoint.schema import LlmRequest, LlmResult
from ..sdk.endpoint.tee import Driver
from ..sdk.memory.redis import RedisChatMessageHistory
from ..sdk.schema import ToolCallCompletion, SystemMessage, Function, Tool
from ..sdk.utils import sync
from ..task import TaskHeader


class SystemPrompt(BaseModel):
    # FIXME Deprecated
    """
    系统提示
    """

    start_tag: str = Field(default="[ACT CLAUSE]", description="开始标签")
    end_tag: str = Field(default="[CLAUSE END]", description="结束标签")
    content: List[str] = Field([], description="内容")

    def append(self, content: str):
        if isinstance(content, str):
            if len(content) > 3:
                self.content.append(f"* {content.upper()}")
        return self

    def clear(self):
        self.content = []

    @staticmethod
    def on_system() -> SystemMessage:
        top = SystemPrompt(
            start_tag="[ASSISTANT RULE]",
            end_tag="[RULE END]",
        )
        top.clear()
        top.append("DONT RE-USE THE FUNCTION WITH SAME PARAM")
        top.append("DONT REPEAT")
        top.append("REPLY IN SHORT-CONCISE")
        top.append("SPEAK IN MORE かわいい STYLE")
        top.append("ACT STEP BY STEP")
        top.append(f"<Time|{time.asctime(time.localtime(time.time()))}>")
        return top.prompt_message

    def prompt(self):
        if not self.content:
            return None
        return self.start_tag + "\n".join(self.content) + self.end_tag

    @property
    def prompt_message(self) -> Optional[SystemMessage]:
        """
        系统提示消息
        :raise: Exception if prompt message is empty
        :return: SystemMessage
        """
        content = self.prompt()
        if content:
            return SystemMessage(content=content)
        return None


class OpenaiMiddleware(object):
    """
    Openai中间件，用于处理消息转换和调用工具
    任务数据>转换器+函数填充>提取历史>放进刮削器>任务数据+刮削结果请求>获取Openai返回>进行声明通知/返回消息
    """

    def __init__(
        self,
        task: TaskHeader,
        functions: List[Function] = None,
        tools: List[ToolCallCompletion] = None,
    ):
        self.auth_client = None
        self.driver = None
        if functions is None:
            functions = []
        if tools is None:
            tools = []

        assert isinstance(task, TaskHeader), "llm_task.py:task type error"

        self.functions: List[Function] = functions
        self._unique_function()
        # 必须先初始化函数
        self.tools: List[Tool] = tools
        self.scraper = Scraper()  # 刮削器
        self.task = task
        self.session_uid = task.receiver.uid
        self.system_prompt: SystemPrompt = SystemPrompt()
        self.message_history = RedisChatMessageHistory(
            session_id=self.session_uid, ttl=60 * 60 * 1
        )

    def init(self):
        """
        :raise: ProviderException
        """
        # 构建请求的驱动信息
        self.auth_client = GetAuthDriver(uid=self.session_uid)
        self.driver = sync(self.auth_client.get())
        assert isinstance(
            self.driver, Driver
        ), "llm_task.py:GetAuthDriver s return not a driver!"
        return self

    def get_schema(self, model_name: str = None):
        if not model_name:
            model_name = self.driver.model
        return SCHEMA_GROUP.get_by_model_name(model_name=model_name)

    def _unique_function(self):
        """
        函数去重，禁止同名函数
        """
        _dict = {}
        for function in self.functions:
            assert isinstance(
                function, Function
            ), "llm_task.py:function type error,cant unique"
            _dict[function.name] = function
        self.functions = list(_dict.values())

    def write_back(self, *, message: Optional[Message] = None):
        """
        写回消息到 Redis 数据库中
        function 写回必须指定 name
        """
        if message:
            self.message_history.add_message(message=message)

    def _append_function_tools(self, functions: List[Function]):
        """ """
        for function_item in functions:
            assert isinstance(
                function_item, Function
            ), "llm_task.py:function type error"
            self.tools.append(Tool(type="function", function=function_item))
        return self.tools

    def scraper_create_message(self, write_back=True, system_prompt=True):
        # FIXME Deprecated
        """
        从人类消息和历史消息中构建请求所用消息
        :param write_back: 是否写回,如果是 False,那么就不会写回到 Redis 数据库中，也就是重新请求
        :param system_prompt: 是否添加系统提示
        :return: None
        """
        if system_prompt:
            # 此前和连带的消息都添加
            self.scraper.add_message(self.system_prompt.on_system(), score=1000)
            _plugin_system_prompt = self.system_prompt.prompt_message
            if _plugin_system_prompt is not None:
                assert isinstance(
                    _plugin_system_prompt, Message
                ), "llm_task.py:system prompt type error"
                self.scraper.add_message(_plugin_system_prompt, score=500)
        _history = []
        # database:read redis
        history_messages = self.message_history.messages
        for i, message in enumerate(history_messages):
            _history.append(message)
        # 刮削器合并消息，这里评价简写了。
        for i, _msg in enumerate(_history):
            self.scraper.add_message(_msg, score=len(str(_msg)))
        # 处理 人类 发送的消息
        if write_back:
            _buffer = []
            raw_message = self.task.message
            raw_message: List[RawMessage]
            for i, message in enumerate(raw_message):
                message: RawMessage
                # message covert
                user_message = message.format_user_message(
                    role="user",
                )
                _buffer.append(user_message)
            for i, _msg in enumerate(_buffer):
                self.scraper.add_message(_msg, score=len(str(_msg)) + 50)
            # database:save redis
            for _msg in _buffer:
                self.message_history.add_message(message=_msg)

    async def request_openai(
        self,
        auto_write_back: bool,
        disable_function: bool = False,
    ) -> LlmResult:
        """
        处理消息转换和调用工具
        :param auto_write_back: 是否自动写回
        :param disable_function: 禁用函数
        :return: OpenaiResult
        """
        run_driver_model = self.driver.model
        endpoint_schema = self.get_schema(model_name=run_driver_model)
        if not endpoint_schema:
            logger.warning(
                f"Openai model {run_driver_model} not found, use {run_driver_model} instead"
            )
            endpoint_schema = SingleModel(
                llm_model=run_driver_model,
                token_limit=8192,
                request=Openai,
                response=OpenaiResult,
                schema_type="openai",
                func_executor="tool_call",
                exception=None,
            )
        # 添加函数定义的系统提示
        if not disable_function:
            for function_item in self.functions:
                assert isinstance(
                    function_item, Function
                ), "llm_task.py:function type error"
                self.system_prompt.append(function_item.config.system_prompt)
        # 构建标准函数列表并转换添加到工具列表
        functions = [
            function_item.request_final(schema_model=run_driver_model)
            for function_item in self.functions
        ]
        self._append_function_tools(functions=functions)
        tools = [
            tool_item.request_final(schema_model=run_driver_model)
            for tool_item in self.tools
        ]
        # 构建消息列表
        self.scraper_create_message(write_back=auto_write_back)
        # 削减消息列表
        self.scraper.reduce_messages(
            limit=endpoint_schema.token_limit, model_name=run_driver_model
        )
        # 获取消息列表
        messages = self.scraper.get_messages()
        # 标准化消息列表
        messages = [
            message.request_final(schema_model=run_driver_model) for message in messages
        ]
        # 日志
        logger.info(
            f"[x] Openai request"
            f"\n--message {messages} "
            f"\n--url {self.driver.endpoint} "
            f"\n--org {self.driver.org_id} "
            f"\n--model {run_driver_model} "
            f"\n--function {functions}"
        )
        # 禁用函数？
        if disable_function or not functions:
            logger.debug(f"Llm Driver --disable function:{disable_function}")
        if endpoint_schema.func_executor == "unsupported":
            logger.debug(f"Llm Driver --unsupported function:{functions}")
            disable_function = True
        # 必须校验
        if disable_function:
            functions = None
            tools = None
        # 根据模型选择不同的驱动a
        assert messages, "message cant be none"
        endpoint: LlmRequest = endpoint_schema.request.init(
            driver=self.driver,
            messages=messages,
            functions=functions,
            tools=tools,
            echo=False,
        )
        # 调用Openai
        result: LlmResult = await endpoint.create()
        _message = result.default_message
        _usage = result.usage.total_tokens
        self.write_back(message=_message)
        # print(result.model_dump_json(indent=2))
        # 记录消耗
        await CostControl.add_cost(
            cost=UserCost.create_from_task(
                uid=self.session_uid,
                cost=Cost(
                    cost_by=self.task.receiver.platform,
                    token_usage=_usage,
                    token_uuid=self.driver.uuid,
                    llm_model=self.driver.model,
                    provide_type=self.auth_client.provide_type().value,
                ),
            )
        )
        return result
