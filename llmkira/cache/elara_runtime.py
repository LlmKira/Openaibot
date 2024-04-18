# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:44
import asyncio
import json
from typing import Union

import elara
from loguru import logger

from .runtime_schema import AbstractDataClass, PREFIX


class ElaraClientAsyncWrapper(AbstractDataClass):
    """
    Elara 数据基类
    """

    def __init__(self, backend, prefix=PREFIX):
        self.prefix = prefix
        self.elara = elara.exe_cache(path=backend)
        self.lock = asyncio.Lock()

    async def ping(self):
        return True

    def update_backend(self, backend):
        self.elara = elara.exe_cache(path=backend)
        return True

    async def read_data(self, key):
        """
        Read data from elara
        """
        data = self.elara.get(self.prefix + str(key))
        if data is not None:
            try:
                data = json.loads(data)
            except Exception as ex:
                logger.trace(ex)
        return data

    async def set_data(self, key, value: Union[dict, str, bytes], timeout: int = None):
        """
        Set data to elara
        :param key:
        :param value:
        :param timeout: seconds
        :return:
        """
        self.elara.set(self.prefix + str(key), value, max_age=timeout)
        self.elara.commit()
