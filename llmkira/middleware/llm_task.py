# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
# @Software: PyCharm
import time
from typing import List, Literal

from loguru import logger
from pydantic import Field, BaseModel

from .llm_provider import GetAuthDriver
from ..extra.user import UserCost, CostControl
from ..schema import RawMessage
from ..sdk.endpoint import openai
from ..sdk.endpoint.openai import Message
from ..sdk.endpoint.openai.action import Scraper
from ..sdk.memory.redis import RedisChatMessageHistory
from ..task import TaskHeader


class SystemPrompt(BaseModel):
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
    def on_system():
        top = SystemPrompt(
            start_tag="[ASSISTANT RULE]",
            end_tag="[RULE END]",
        )
        top.clear()
        top.append("DONT RE-USE THE FUNCTION WITH SAME PARAM")
        top.append("PARAMS NOT NULL")
        top.append("DONT REPEAT YOURSELF")
        top.append("REPLY IN SHORT-CONCISE")
        top.append("SPEAK IN MORE かわいい STYLE")
        top.append(f"<Time|{time.asctime(time.localtime(time.time()))}>")
        return top.prompt_message

    def prompt(self):
        if not self.content:
            return None
        return self.start_tag + "\n".join(self.content) + self.end_tag

    @property
    def prompt_message(self):
        content = self.prompt()
        if content:
            return Message(
                role="system", name="system", content=content
            )
        return None


class OpenaiMiddleware(object):
    """
    Openai中间件，用于处理消息转换和调用工具
    任务数据>转换器+函数填充>提取历史>放进刮削器>任务数据+刮削结果请求>获取Openai返回>进行声明通知/返回消息
    """

    def __init__(self, task: TaskHeader, function: List[openai.Function] = None):
        self.scraper = Scraper()  # 刮削器
        assert isinstance(task, TaskHeader), "llm_task.py:task type error"
        self.functions: List[openai.Function] = function
        if self.functions is None:
            self.functions = []
        self.task = task
        self.session_user_uid = task.receiver.uid
        self.system_prompt: SystemPrompt = SystemPrompt()
        self.message_history = RedisChatMessageHistory(
            session_id=f"{task.receiver.platform}:{task.receiver.user_id}",
            ttl=60 * 60 * 1
        )

    def write_back(self,
                   message_list: List[RawMessage],
                   name: str = None,
                   role: Literal["user", "system", "function", "assistant"] = "user"):
        """
        写回消息到 Redis 数据库中
        function 写回必须指定 name
        """
        for message in message_list:
            self.message_history.add_message(message=Message(role=role, name=name, content=message.text))

    def unique_function(self):
        """
        函数 hash 去重
        """
        _dict = {}
        for function in self.functions:
            assert isinstance(function, openai.Function), "llm_task.py:function type error,cant unique"
            _dict[function.name] = function
        self.functions = list(_dict.values())

    def scraper_create_message(self, write_back=True, system_prompt=True):
        """
        从人类消息和历史消息中构建请求所用消息
        :param write_back: 是否写回,如果是 False,那么就不会写回到 Redis 数据库中，也就是重新请求
        :param system_prompt: 是否添加系统提示
        """
        if system_prompt:
            # 此前和连带的消息都添加
            self.scraper.add_message(self.system_prompt.on_system(), score=1000)
            _plugin_system_prompt = self.system_prompt.prompt_message
            if _plugin_system_prompt is not None:
                assert isinstance(_plugin_system_prompt, Message), "llm_task.py:system prompt type error"
                self.scraper.add_message(_plugin_system_prompt, score=500)
        # 处理历史消息
        _history = []
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
                _buffer.append(Message(role="user", name=None, content=message.text))
            # 装样子添加评分
            # TODO 评分
            for i, _msg in enumerate(_buffer):
                self.scraper.add_message(_msg, score=len(str(_msg)) + 50)
            # 处理缓存后默认写回 Redis 数据库
            for _msg in _buffer:
                self.message_history.add_message(message=_msg)

    async def request_openai(
            self,
            auto_write_back: bool,
            disable_function: bool = False
    ) -> openai.OpenaiResult:
        """
        处理消息转换和调用工具
        :param auto_write_back: 是否自动写回
        :param disable_function: 禁用函数
        :return:
        """

        # 去重
        self.unique_function()  # 去重
        # 添加函数定义的系统提示
        if not disable_function:
            for function_item in self.functions[:5]:
                function_item: openai.Function
                self.system_prompt.append(function_item.config.system_prompt)
        # 构建标准函数列表
        functions = [
            function_item.format2parameters()
            for function_item in self.functions
        ] if self.functions else None

        # 构建请求的驱动信息
        auth_client = GetAuthDriver(uid=self.session_user_uid)
        driver = await auth_client.get()
        assert isinstance(driver, openai.Openai.Driver), "llm_task.py:GetAuthDriver s return not a driver!"

        # 构建请求的消息列表
        self.scraper_create_message(write_back=auto_write_back)
        # 校验消息列表
        self.scraper.reduce_messages(limit=openai.Openai.get_token_limit(model=driver.model))
        message = self.scraper.get_messages()
        assert message, "llm_task.py:message is None"

        # 日志
        logger.info(f"[x] Openai request "
                    f"\n--message {message} "
                    f"\n--url {driver.endpoint} "
                    f"\n--org {driver.org_id} "
                    f"\n--model {driver.model} "
                    f"\n--function {functions}"
                    )
        if disable_function or not functions:
            logger.debug(f"[x] Openai function empty warn \n--disable function:{disable_function}")

        # 必须校验
        if disable_function:
            _functions = None
        # Create endpoint
        endpoint = openai.Openai(
            config=driver,
            model=driver.model,
            messages=message,
            functions=functions,
            echo=False
        )

        # 调用Openai
        result: openai.OpenaiResult = await endpoint.create()
        _message = result.default_message  # 默认取第一条
        _usage = result.usage.total_tokens
        self.message_history.add_message(message=_message)

        # 记录消耗
        await CostControl.add_cost(
            cost=UserCost.create_from_task(
                uid=self.session_user_uid,
                request_id=result.id,
                cost=UserCost.Cost(
                    cost_by="chat",
                    token_usage=_usage,
                    token_uuid=driver.uuid,
                    model_name=driver.model,
                    provide_type=auth_client.provide_type().value
                )
            )
        )
        logger.debug(
            f"[x] Openai result "
            f"\n--message {result.choices} "
            f"\n--token {result.usage} "
            f"\n--model {driver.model}"
        )
        return result
