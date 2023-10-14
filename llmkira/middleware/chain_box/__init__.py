# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:34
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
from typing import Optional

from loguru import logger

from llmkira.cache.redis import cache
from llmkira.task import TaskHeader
from .schema import Chain


class AuthReloader(object):

    async def add_auth(self, task: Chain):
        _cache = await cache.set_data(key=f"auth:{task.uuid}", value=task.json(), timeout=60 * 60 * 24 * 7)
        return task.uuid

    async def get_auth(self, uuid: str, user_id: str) -> Optional[Chain]:
        _cache = await cache.read_data(key=f"auth:{uuid}")
        if not _cache:
            logger.debug(f"[x] Auth \n--empty {uuid}")
            return None
        logger.debug(f"[x] Auth \n--data {_cache}")
        task = Chain().parse_obj(_cache)
        task = task.format_arg(arg=TaskHeader)
        if task.user_id != user_id:
            logger.debug(f"[x] Auth \n--not found user {uuid}")
            return None
        return task


class ChainReloader(object):

    async def add_task(self, task: Chain):
        _cache = await cache.lpush_data(key=f"chain:{task.user_id}", value=task.json())
        return task.uuid

    async def get_task(self, user_id: str) -> Optional[Chain]:
        _data = await cache.lpop_data(key=f"chain:{user_id}")
        if not _data:
            return None
        _task = Chain.parse_obj(json.loads(_data))
        _task = _task.format_arg(arg=TaskHeader)
        return _task


AUTH_MANAGER = AuthReloader()
CHAIN_MANAGER = ChainReloader()
