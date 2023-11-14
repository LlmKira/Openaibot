# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:48
# @Author  : sudoskys
# @File    : redis_lpush.py
# @Software: PyCharm
import time

from llmkira.sdk.cache import RedisRuntime


async def redis():
    cache = RedisRuntime().get_redis()
    await cache.lpush_data("test", int(time.time()))
    await cache.lpush_data("test", int(time.time()) + 1)
    _data = await cache.lrange_data("test")
    print(f"now data is {_data}")
    _data = await cache.lpop_data("test")
    print(f"pop data is {_data}")
    _data = await cache.lrange_data("test")
    print(f"now data is {_data}")
    _data = await cache.lrange_data("test", start_end=(0, 1))
    print(f"(0,1) data is {_data}")


import asyncio

asyncio.run(redis())
