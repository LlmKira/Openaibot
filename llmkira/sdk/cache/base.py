# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:43
# @Author  : sudoskys
# @File    : base.py
# @Software: PyCharm
from abc import abstractmethod, ABC
from typing import Any

PREFIX = 'base_bot:'


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


class BaseRuntime(ABC):
    init_already = False
    client = None
    dsn = None


class AbstractDataClass(ABC):

    @abstractmethod
    async def ping(self):
        return True

    @abstractmethod
    def update_backend(self, backend):
        pass

    @abstractmethod
    async def set_data(self, key: str, value: Any, **kwargs) -> Any:
        pass

    @abstractmethod
    async def read_data(self, key: str) -> Any:
        pass
