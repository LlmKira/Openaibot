# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:34
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import Optional

from loguru import logger

from .schema import Chain
from ...sdk.cache import global_cache_runtime


class AuthReloader(object):
    """
    重放任务
    """

    def __init__(self, uid: str = None):
        self.uid = uid

    @classmethod
    def _prefix(cls, uuid: str) -> str:
        """auth:{auth_schema_version}:uuid"""
        return f"auth:v1:{uuid}"

    @classmethod
    def from_form(cls, platform: str, user_id: str):
        _c = cls()
        _c.uid = f"{platform}:{user_id}"
        return _c

    async def save_auth(self,
                        chain: Chain,
                        timeout: int = 60 * 60 * 24
                        ):
        cache = global_cache_runtime.get_redis()
        logger.debug("Resign Auth Point")
        assert chain.creator_uid == self.uid, "Cant Resign Uid Diff From `self`"
        _cache = await cache.set_data(
            key=self._prefix(uuid=chain.uuid),
            value=chain.model_dump_json(),
            timeout=timeout
        )
        return chain.uuid

    async def read_auth(self, uuid: str) -> Optional[Chain]:
        cache = global_cache_runtime.get_redis()
        _cache = await cache.read_data(key=self._prefix(uuid=uuid))
        if not _cache:
            return None
        logger.debug(f"Get Auth Data {_cache} {_cache}")
        chain = Chain.from_redis(_cache)
        if chain.is_expire:
            return None
        if chain.creator_uid != self.uid:
            logger.debug(f"Not User {self.uid} Created Auth")
            return None
        return chain


class ChainReloader(object):

    def __init__(self, uid: str):
        self.uid = uid

    @classmethod
    def _prefix(cls, uuid: str) -> str:
        """chain:{auth_schema_version}:uuid"""
        return f"chain:v1:{uuid}"

    async def add_task(self, chain: Chain) -> str:
        """
        Add A Chain To Redis List
        :param chain Task
        :return uuid
        """
        cache = global_cache_runtime.get_redis()
        await cache.lpush_data(
            key=self._prefix(uuid=chain.uuid),
            value=chain.model_dump_json()
        )
        return chain.uuid

    async def get_task(self) -> Optional[Chain]:
        """
        Get Task From Redis List
        :return Optional[Chain]
        """
        cache = global_cache_runtime.get_redis()
        redis_raw = await cache.lpop_data(
            key=self._prefix(uuid=self.uid)
        )
        if not redis_raw:
            return None
        chain = Chain.from_redis(redis_raw)
        if chain.is_expire:
            return None
        return chain
