# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:43
from abc import abstractmethod, ABC
from typing import Any, Union

PREFIX = "oai_bot:"


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

    @staticmethod
    def check_client_dsn(dsn):
        raise NotImplementedError

    def check_client(self) -> bool:
        raise NotImplementedError

    def init_client(self, verbose=False):
        raise NotImplementedError

    def get_client(self) -> "AbstractDataClass":
        raise NotImplementedError


class AbstractDataClass(ABC):
    @abstractmethod
    async def ping(self):
        return True

    @abstractmethod
    def update_backend(self, backend):
        pass

    @abstractmethod
    async def set_data(
        self, key: str, value: Union[dict, str, bytes], timeout: int = None
    ) -> Any:
        pass

    @abstractmethod
    async def read_data(self, key: str) -> Any:
        pass
