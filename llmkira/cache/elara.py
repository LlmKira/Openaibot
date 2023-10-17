# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:44
# @Author  : sudoskys
# @File    : elara.py
# @Software: PyCharm
import asyncio

import elara

from ..cache.base import AbstractDataClass, PREFIX


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


