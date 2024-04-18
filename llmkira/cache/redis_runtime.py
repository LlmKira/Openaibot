# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:43
import json
from typing import Optional, Union

import redis
from loguru import logger
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool

from .runtime_schema import AbstractDataClass, PREFIX


class RedisClientWrapper(AbstractDataClass):
    """
    Redis 数据类
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

    async def set_data(self, key, value: Union[dict, str, bytes], timeout=None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self._redis.set(
            name=f"{self.prefix}{key}", value=value, ex=timeout
        )

    async def read_data(self, key) -> Optional[Union[str, dict, int]]:
        data = await self._redis.get(self.prefix + str(key))
        if data is not None:
            try:
                data = json.loads(data)
            except Exception as ex:
                logger.trace(ex)
        return data
