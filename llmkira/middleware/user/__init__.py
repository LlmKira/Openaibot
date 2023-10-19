# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 上午12:06
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from urllib.parse import urlparse

from loguru import logger

from llmkira.cache.redis import cache
from llmkira.utils import sync
from .schema import UserInfo
from ...sdk.endpoint import openai


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class SubManager(object):
    def __init__(self, user_id: str):
        self.reload_exception = None
        self.sub_info: UserInfo = sync(self._sync(user_id=user_id))
        assert isinstance(self.sub_info, UserInfo), "sub info error"

    async def _upload(self, user_id: str, ignore_exception=False):
        if self.reload_exception and not ignore_exception:
            logger.warning(f"you are upload a default sub info for {user_id} to wipe out the original data")
            return None
        await cache.set_data(key=f"sub:{user_id}", value=self.sub_info.json())

    async def _sync(self, user_id: str):
        _cache = await cache.read_data(key=f"sub:{user_id}")
        if not _cache:
            return UserInfo(user_id=user_id)
        try:
            sub_info = UserInfo().parse_obj(_cache)
        except Exception as e:
            self.reload_exception = True
            logger.warning(f"not found sub info {user_id},{e}")
            return UserInfo(user_id=user_id)
        return sub_info

    @property
    def llm_driver(self):
        if not self.sub_info.update_driver:
            return openai.Openai.Driver()
        return self.sub_info.llm_driver

    async def block_plugin(self, plugin_name: str):
        self.sub_info.plugin_subs.lock.append(plugin_name)
        return self.sub_info.plugin_subs.lock

    async def unblock_plugin(self, plugin_name: str):
        if plugin_name in self.sub_info.plugin_subs.lock:
            self.sub_info.plugin_subs.lock.remove(plugin_name)
        return self.sub_info.plugin_subs.lock

    async def set_endpoint(self, api_key: str, endpoint: str = None):
        """
        这里容易产生鉴权错误和环境变量被泄漏的问题！！
        # TODO: 优化鉴权机制
        """
        if not endpoint:
            endpoint = "https://api.openai.com/v1/chat/completions"
        else:
            assert is_valid_url(endpoint), "endpoint is not valid url"
        assert api_key, "api key is empty"
        self.sub_info.llm_driver = openai.Openai.Driver(endpoint=endpoint, api_key=api_key)
        self.sub_info.update_driver = True
        await self._upload(user_id=self.sub_info.user_id)

    async def clear_endpoint(self):
        self.sub_info.update_driver = False
        self.sub_info.llm_driver = None
        await self._upload(user_id=self.sub_info.user_id)

    async def get_lock_plugin(self):
        return self.sub_info.plugin_subs.lock

    async def add_cost(self, cost: UserInfo.Cost) -> list:
        self.sub_info.costs.append(cost)
        await self._upload(user_id=self.sub_info.user_id)
        return self.sub_info.costs

    async def get_total_cost(self) -> int:
        return self.sub_info.total_cost()

    async def get_cost_by_function_name(self, function_name: str) -> list:
        return [cost for cost in self.sub_info.costs if cost.function_name == function_name]
