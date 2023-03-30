# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午10:06
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm

from .Bucket import ElaraClientWrapper, RedisClientWrapper, cache, AbstractDataClass

__all__ = ["ElaraClientWrapper", "cache", "RedisClientWrapper"]


# 包装一下
class CacheNameSpace(AbstractDataClass):
    def __init__(self, prefix):
        self.prefix = prefix

    async def set_data(self, key, value, timeout: int = None):
        key = f"{self.prefix}_{key}"
        return cache.set_data(key, value, timeout=timeout)

    async def read_data(self, key):
        key = f"{self.prefix}_{key}"
        return cache.read_data(key)
