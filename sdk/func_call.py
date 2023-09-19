# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午8:54
# @Author  : sudoskys
# @File    : func_call.py
# @Software: PyCharm
import re
from abc import ABC, abstractmethod
from typing import Optional, Type, List, Union

from loguru import logger
from pydantic import BaseModel

from .endpoint.openai import Function


class BaseTool(ABC, BaseModel):
    """
    基础工具类，所有工具类都应该继承此类
    """
    silent: bool = False
    function: Function
    keywords: List[str]
    pattern: Optional[re.Pattern] = None

    @abstractmethod
    def pre_check(self) -> Union[bool, str]:
        """
        预检查，如果不合格则返回False，合格则返回True
        返回字符串表示不合格，且有原因
        """
        return ...

    @abstractmethod
    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        # 正则匹配
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        return None

    @abstractmethod
    async def failed(self, platform, task, receiver, reason):
        """
        处理失败
        """
        return ...

    @abstractmethod
    async def run(self, task, receiver, arg, **kwargs):
        """
        处理message，返回message
        """
        return ...


class ToolManager:
    """
    工具管理器，用于管理所有工具
    """

    def __init__(self):
        self.__tool = {}
        self.__function = {}

    def add_tool(self, name: str, function: Function, tool: Type[BaseTool]):
        self.__tool[name] = tool
        self.__function[name] = function

    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        return self.__tool.get(name)

    def find_tool(self, tool: Type[BaseTool]) -> Optional[str]:
        for name, item in self.__tool.items():
            if item == tool:
                return name
        return None

    def get_function(self, name: str) -> Optional[Function]:
        return self.__function.get(name)

    def find_function(self, func: Function) -> Optional[str]:
        for name, function in self.__function.items():
            if function == func:
                return name
        return None

    def get_all_tool(self) -> dict:
        return self.__tool

    def get_all_function(self) -> dict:
        return self.__function

    def run_all_check(self, message_text, ignore: List[str] = None) -> List[Function]:
        """
        运行所有工具的检查，返回所有检查通过的 函数
        """
        if ignore is None:
            ignore = []
        _pass = []
        for name, tool in self.get_all_tool().items():
            if tool().func_message(message_text=message_text):
                if name in ignore:
                    continue
                    # 跳过
                _pass.append(self.get_function(name))
        return _pass


TOOL_MANAGER = ToolManager()


def listener(function: Function):
    def decorator(func: Type[BaseTool]):
        if not isinstance(function, Function):
            raise TypeError(f"listener function must be Function, not {type(function)}")
        if not issubclass(func, BaseTool):
            raise TypeError(f"listener function must be subclass of BaseTool, not {func.__name__}")

        # 注册进工具管理器
        _check = func().pre_check()
        if _check is True:
            TOOL_MANAGER.add_tool(name=function.name, function=function, tool=func)
            logger.info(f"Function loaded success:{function.name}")
        else:
            logger.info(f"Function loaded failed:{function.name}, reason:{_check}")

        async def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(**kwargs)

        return wrapper

    return decorator
