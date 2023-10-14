# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:43
# @Author  : sudoskys
# @File    : redis.py
# @Software: PyCharm
import json
import os
from typing import Optional, Tuple, List

import redis
from dotenv import load_dotenv
from llmkira.cache.base import AbstractDataClass, PREFIX
from loguru import logger
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool


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

    async def set_data(self, key, value, timeout=None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self._redis.set(name=f"{self.prefix}{key}", value=value, ex=timeout)

    async def read_data(self, key):
        data = await self._redis.get(self.prefix + str(key))
        if data is not None:
            try:
                data = json.loads(data)
            except Exception as e:
                pass
        return data

    async def lpush_data(self, key, value):
        """
        从左侧插入数据
        :param key: str
        :param value: json
        """
        # 验证是否可以被json序列化
        return await self._redis.lpush(self.prefix + str(key), value)

    async def lpop_data(self, key) -> Optional[str]:
        _data = await self._redis.lpop(self.prefix + str(key))
        if _data:
            return _data.decode("utf-8")
        return None

    async def lrange_data(self, key, start_end: Tuple[int, int] = (0, -1)) -> List[str]:
        _items = await self._redis.lrange(self.prefix + str(key), start=start_end[0], end=start_end[1])
        items = [m.decode("utf-8") for m in _items[::-1]]
        return items


def check_redis_dsn(dsn):
    try:
        import redis
        r = redis.from_url(dsn)
        assert r.ping() is True
    except Exception as exp:
        logger.warning(f"Error connecting to Redis: {exp}")
        return False
    else:
        return True


# 加载 .env 文件
load_dotenv()
redis_url = os.getenv('REDIS_DSN', None)
if not redis_url:
    logger.warning('REDIS_DSN not found in .env, use default redis://localhost:6379/0')
    redis_url = 'redis://localhost:6379/0'
cache: Optional[RedisClientWrapper]
if not check_redis_dsn(redis_url):
    logger.warning('REDIS DISCONNECT,pls set REDIS_DSN in env')
    cache = None
else:
    logger.success(f'RedisClientWrapper loaded successfully in {redis_url}')
    cache = RedisClientWrapper(redis_url)
