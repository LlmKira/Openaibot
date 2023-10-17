# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
# @Software: PyCharm
import os
import time
from typing import List, Literal

from loguru import logger

from ..middleware.user import SubManager, UserInfo
from ..schema import RawMessage
from ..sdk.endpoint import openai
from ..sdk.endpoint.openai import Message
from ..sdk.endpoint.openai.action import Scraper
from ..sdk.memory.redis import RedisChatMessageHistory
from ..task import TaskHeader
from ..utils import sync

RULE = """[ASSISTANT RULE]
* DO NOT RE-USE THE FUNCTION WITH SAME PARAMETERS
* KEEP YOUR ANSWERS CONCISE AND NON-REPETITIVE
* SPEAK IN MORE かわいい STYLE
[ASSISTANT RULE]"""


class OpenaiMiddleware(object):
    """
    Openai中间件，用于处理消息转换和调用工具
    任务数据>转换器+函数填充>提取历史>放进刮削器>任务数据+刮削结果请求>获取Openai返回>进行声明通知/返回消息
    """

    def __init__(self, task: TaskHeader, function: List[openai.Function] = None):
        self.scraper = Scraper()  # 刮削器
        self.functions: List[openai.Function] = function
        if self.functions is None:
            self.functions = []
        self.task = task
        self.sub_manager = SubManager(user_id=f"{task.sender.platform}:{task.sender.user_id}")  # 由发送人承担接受者的成本
        self.message_history = RedisChatMessageHistory(
            session_id=f"{task.receiver.platform}:{task.receiver.user_id}",
            ttl=60 * 60 * 1
        )

    def build(self, auto_write_back, default_system: bool = True):
        """
           构建消息和函数列表
           :param auto_write_back: 自动回写缓存消息到数据库
              :param default_system: 是否添加默认系统时钟/环境消息
        """
        self.create_message(write_back=auto_write_back, default_system=default_system)
        self.append_function()
        return self

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

    def append_function(self):
        """
        添加函数
        """
        # 去重
        _dict = {}
        for function in self.functions:
            _dict[function.name] = function
        self.functions = list(_dict.values())
        # 取消
        _ignore = sync(self.sub_manager.get_lock_plugin())
        for function in self.functions:
            if function.name in _ignore:
                self.functions.remove(function)

    def create_message(self, write_back=True, default_system: bool = True):
        """
        从人类消息和历史消息中构建请求所用消息
        """
        if default_system:
            localtime = time.asctime(time.localtime(time.time()))
            rule = f"<Time|{localtime}>" + RULE
            self.scraper.add_message(Message(role="system", name="system",
                                             content=rule),
                                     score=0)
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

    async def request_openai(self, disable_function: bool = False) -> openai.OpenaiResult:
        """
        处理消息转换和调用工具
        :param disable_function: 禁用函数
        :return:
        """
        # 模型内容
        model_name = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-0613")
        self.scraper.reduce_messages(limit=openai.Openai.get_token_limit(model=model_name))
        message = self.scraper.get_messages()
        assert message, "llm_task.py:message is None"
        _functions = self.functions if self.functions else None
        driver = self.sub_manager.llm_driver
        assert isinstance(driver, openai.Openai.Driver), "llm_task.py:driver type error"

        # 消息缓存读取和转换
        # 断点
        logger.info(f"[x] Openai request \n--message {message} \n--url {driver.endpoint} \n--org {driver.org_id} ")
        if disable_function or not _functions:
            logger.debug(f"[x] Openai function empty warn \n--disable function:{disable_function}")
        if disable_function:
            _functions = None
        endpoint = openai.Openai(
            config=driver,
            model=model_name,
            # presence_penalty=0.5,
            # frequency_penalty=0.3,
            messages=message,
            functions=_functions,
            echo=False
        )

        # 调用Openai
        result: openai.OpenaiResult = await endpoint.create()
        _message = result.default_message
        _usage = result.usage.total_tokens
        self.message_history.add_message(message=_message)
        await self.sub_manager.add_cost(
            cost=UserInfo.Cost(token_usage=_usage, token_uuid=driver.uuid, model_name=model_name)
        )
        logger.success(f"[x] Openai result \n--message {result.choices} \n--token {result.usage}")
        return result
