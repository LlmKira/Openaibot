# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午9:23
# @Author  : sudoskys
# @File    : Bucket.py
# @Software: PyCharm
import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Any

import elara
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool
from dotenv import load_dotenv
from loguru import logger

PREFIX = 'openai_bot_'


class AbstractDataClass(ABC):

    @abstractmethod
    def update_backend(self, backend):
        pass

    @abstractmethod
    async def set_data(self, key: str, value: Any, **kwargs) -> Any:
        pass

    @abstractmethod
    async def read_data(self, key: str) -> Any:
        pass


class ElaraClientWrapper(AbstractDataClass):
    """
    Elara 数据基类
    """

    def __init__(self, backend, prefix=PREFIX):
        self.prefix = prefix
        self.elara = elara.exe(path=backend)
        self.lock = asyncio.Lock()

    def update_backend(self, backend):
        self.elara = elara.exe(path=backend)
        return True

    async def read_data(self, key):
        async with self.lock:
            _res = self.elara.get(self.prefix + str(key))
            return _res

    async def set_data(self, key, value, timeout=None):
        async with self.lock:
            self.elara.set(self.prefix + str(key), value)
            self.elara.commit()


class RedisClientWrapper(AbstractDataClass):
    """
    Redis 数据基类
    """

    def __init__(self, backend, prefix=PREFIX):
        self.prefix = prefix
        self.connection_pool = ConnectionPool.from_url(backend)
        self._redis = Redis(connection_pool=self.connection_pool)

    def update_backend(self, backend):
        self.connection_pool = ConnectionPool.from_url(backend)
        self._redis = Redis(connection_pool=self.connection_pool)
        return True

    async def set_data(self, key, value, timeout=None):
        return await self._redis.set(self.prefix + str(key), json.dumps(value), ex=timeout)

    async def read_data(self, key):
        data = await self._redis.get(self.prefix + str(key))
        if data is not None:
            data = json.loads(data)
        return data


# 加载 .env 文件
load_dotenv()
redis_url = os.getenv('REDIS_DSN')
if not redis_url:
    logger.error('Please configure the REDIS_DSN variable in .env')
    raise ValueError('Redis configuration not found')
logger.success(f'RedisClientWrapper loaded successfully')
cache: AbstractDataClass = RedisClientWrapper(redis_url)
