# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午11:55
# @Author  : sudoskys
# @File    : test_config.py
# @Software: PyCharm
import os

import pytest
import asyncio

import shortuuid
from dotenv import load_dotenv
from loguru import logger


class TestConfig:
    def test_init(self):
        assert True is True


class TestDataClient(object):

    @pytest.mark.asyncio
    async def test_redis(self):
        import random
        from Component import cache
        obj = cache.CacheNameSpace(prefix="test_")
        random_key = shortuuid.uuid()
        logger.info(random_key)
        data = str(random.randint(0, 100))
        await obj.set_data(random_key, data)
        read_data = await obj.read_data(random_key)
        assert read_data == data

    @pytest.mark.asyncio
    async def test_redis(self):
        # Check if the redis server is running
        load_dotenv()
        redis_url = os.getenv('REDIS_DSN')
        assert redis_url is not None
        # Check Ping
        from redis import ConnectionPool, Redis
        connection_pool = ConnectionPool.from_url(redis_url)
        _redis = Redis(connection_pool=connection_pool)
        # Run DataWarp
        import random
        from Component import cache
        obj = cache.CacheNameSpace(prefix="test_")
        data = str(random.randint(0, 100))
        await obj.set_data("number", data)
        read_data = await obj.read_data("number")
        assert read_data == data

    @pytest.mark.asyncio
    async def test_elara(self):
        import random
        from Component import cache
        obj = cache.ElaraClientWrapper(backend="test.db")
        data = str(random.randint(0, 100))
        await obj.set_data("number", data)
        read_data = await obj.read_data("number")
        assert read_data == data
