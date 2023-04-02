# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午9:23
# @Author  : sudoskys
# @File    : bucket.py
# @Software: PyCharm
import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Any

import elara
import redis
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool
from dotenv import load_dotenv
from loguru import logger

PREFIX = 'openai_bot_'


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


class ElaraClientWrapper(AbstractDataClass):
    """
    Elara 数据基类
    """

    def __init__(self, backend, prefix=PREFIX):
        self.prefix = prefix
        self.elara = elara.exe(path=backend)
        self.lock = asyncio.Lock()

    async def ping(self):
        return True

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
        self.connection_pool = redis.asyncio.ConnectionPool.from_url(backend)
        self._redis = redis.asyncio.Redis(connection_pool=self.connection_pool)

    async def ping(self):
        return await self._redis.ping()

    def update_backend(self, backend):
        self.connection_pool = ConnectionPool.from_url(backend)
        self._redis = Redis(connection_pool=self.connection_pool)
        return True

    async def set_data(self, key, value, timeout=None):
        return await self._redis.set(f"{self.prefix}{key}", json.dumps(value), ex=timeout)

    async def read_data(self, key):
        data = await self._redis.get(self.prefix + str(key))
        if data is not None:
            data = json.loads(data)
        return data


def check_redis_dsn(dsn):
    try:
        r = redis.Redis.from_url(dsn)
        assert r.ping() == True
    except Exception as e:
        print("Error connecting to Redis: ", e)
        return False
    else:
        return True


# 加载 .env 文件
load_dotenv()
redis_url = os.getenv('REDIS_DSN', 'redis://localhost:6379/0')
try:
    # 初始化实例
    cache: RedisClientWrapper = RedisClientWrapper(redis_url)
    # 检查连接
    if not check_redis_dsn(redis_url):
        raise ValueError('REDIS DISCONNECT')
except Exception as e:
    logger.error(e)
    if redis_url == 'redis://localhost:6379/0':
        logger.error('REDIS DISCONNECT:Ensure Configure the REDIS_DSN variable in .env')
    raise ValueError('REDIS DISCONNECT')
else:
    logger.success(f'RedisClientWrapper loaded successfully in {redis_url}')


class CacheNameSpace(object):
    """
    缓存命名空间, 用于区分不同的缓存
    """

    def __init__(self, prefix):
        self.prefix = prefix

    async def set_data(self, key, value, timeout: int = None):
        key = f"{self.prefix}_{key}"
        return await cache.set_data(key, value, timeout=timeout)

    async def read_data(self, key):
        key = f"{self.prefix}_{key}"
        return await cache.read_data(key)
