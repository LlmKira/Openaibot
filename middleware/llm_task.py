# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : llm_task.py
# @Software: PyCharm
from typing import List, Literal

from loguru import logger

from middleware.user import SubManager, UserInfo
from schema import TaskHeader, RawMessage
from sdk.endpoint import openai
from sdk.endpoint.openai import Message
from sdk.endpoint.openai.action import Scraper
from sdk.func_call import TOOL_MANAGER
from sdk.memory.redis import RedisChatMessageHistory
from sdk.utils import sync


class OpenaiMiddleware(object):
    """
    Openai中间件，用于处理消息转换和调用工具
    任务数据>转换器+函数填充>提取历史>放进刮削器>任务数据+刮削结果请求>获取Openai返回>进行声明通知/返回消息
    """

    def __init__(self, task: TaskHeader):
        self.scraper = Scraper()  # 刮削器
        self.functions = []
        self.task = task
        self.sub_manager = SubManager(user_id=self.task.sender.user_id)  # 由发送人承担接受者的成本
        self.message_history = RedisChatMessageHistory(session_id=str(task.receiver.user_id), ttl=60 * 60 * 1)

    def build(self, write_back):
        # 先拉取记录再转换
        self.create_message(write_back=write_back)
        self.append_function()
        return self

    def write_back(self,
                   name: str,
                   message_list: List[RawMessage],
                   role: Literal["user", "system", "function", "assistant"] = "user"):
        """
        写回消息
        """
        for message in message_list:
            self.message_history.add_message(message=Message(role=role, name=name, content=message.text))

    def append_function(self):
        """
        添加函数
        """
        self.functions = []
        raw_message = self.task.message
        raw_message: List[RawMessage]
        for i, message in enumerate(raw_message):
            # 创建函数系统
            if self.task.task_meta.function_enable:
                # 用户可以拉黑插件
                self.functions.extend(
                    TOOL_MANAGER.run_all_check(
                        message_text=message.text,
                        ignore=sync(self.sub_manager.get_lock_plugin())
                    )
                )

    def create_message(self, write_back=True):
        """
        转换消息
        """
        _history = []
        history_messages = self.message_history.messages
        for i, message in enumerate(history_messages):
            _history.append(message)
        # 刮削器合并消息，这里评价简写了。
        for i, _msg in enumerate(_history):
            self.scraper.add_message(_msg, score=len(str(_msg)))

        # 处理附带的任何原始消息
        if write_back:
            _buffer = []
            # 实时消息
            raw_message = self.task.message
            raw_message: List[RawMessage]
            for i, message in enumerate(raw_message):
                _buffer.append(Message(role="user", content=message.text))
            # 新消息的分数比较高
            for i, _msg in enumerate(_buffer):
                self.scraper.add_message(_msg, score=len(str(_msg)) + 50)
            # save to history
            for _msg in _buffer:
                self.message_history.add_message(message=_msg)

    async def func_message(self) -> Message:
        """
        处理消息转换和调用工具
        """
        model_name = "gpt-3.5-turbo-0613"
        self.scraper.reduce_messages(limit=openai.Openai.get_token_limit(model=model_name))
        message = self.scraper.get_messages()
        _functions = self.functions if self.functions else None
        driver = self.sub_manager.llm_driver
        assert isinstance(driver, openai.Openai.Driver), "llm_task.py:driver type error"

        # 消息缓存读取和转换
        # 断点
        logger.debug(f" [x] Openai request:{message}")
        endpoint = openai.Openai(
            config=driver,
            model=model_name,
            messages=message,
            functions=_functions,
            echo=True
        )

        # 调用Openai
        result = await endpoint.create()
        _message = openai.Openai.parse_single_reply(response=result)
        _usage = openai.Openai.parse_usage(response=result)
        self.message_history.add_message(message=_message)
        await self.sub_manager.add_cost(
            cost=UserInfo.Cost(token_usage=_usage, token_uuid=driver.uuid, model_name=model_name)
        )
        logger.info(f"openai result:{result}")
        return _message
