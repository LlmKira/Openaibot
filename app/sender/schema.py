# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import abstractmethod, ABC
from typing import List

from llmkira.openapi.hook import run_hook, Trigger
from llmkira.task.schema import EventMessage, Sign


class Runner(ABC):
    @staticmethod
    async def hook(platform: str, messages: List[EventMessage], sign: Sign) -> tuple:
        """
        :param platform: 平台
        :param messages: 消息
        :param sign: 签名
        :return: 平台,消息,文件列表
        """
        arg, kwarg = await run_hook(
            Trigger.SENDER,
            platform=platform,
            messages=messages,
            sign=sign,
        )
        platform = kwarg.get("platform", platform)
        messages = kwarg.get("messages", messages)
        sign = kwarg.get("sign", sign)
        return platform, messages, sign

    @abstractmethod
    async def upload(self, *args, **kwargs):
        ...

    async def transcribe(self, *args, **kwargs) -> List[EventMessage]:
        ...

    @abstractmethod
    def run(self, *args, **kwargs):
        ...
