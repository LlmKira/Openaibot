# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午9:57
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from enum import Enum
from typing import Type, Union, Dict

from .default_factory import DefaultBuilder, DefaultParser
from .schema import Builder, Parser

__builder__: Dict[str, Type[Builder]] = {
}
__parser__: Dict[str, Type[Parser]] = {
}


class Locate(Enum):
    sender = 1
    receiver = 0


def resign_transfer(agent_name: str):
    """
    装饰器
    :param agent_name: 平台名称
    """

    def decorator(func: Union[Builder, Parser, Type[Builder], Type[Parser]]):
        if issubclass(func, Builder):
            __builder__[agent_name] = func
        elif issubclass(func, Parser):
            __parser__[agent_name] = func
        else:
            raise ValueError(f"UNKNOWN TRANSFER{type(func)}")

        async def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(**kwargs)

        return wrapper

    return decorator


# 装饰器
class TransferManager(object):

    def receiver_builder(self, agent_name: str) -> Type[Builder]:
        """
        receiver
        """
        _func = __builder__.get(agent_name)
        if _func:
            return _func
        return DefaultBuilder

    def sender_parser(self, agent_name: str) -> Type[Parser]:
        _func = __parser__.get(agent_name)
        if _func:
            return _func
        return DefaultParser
