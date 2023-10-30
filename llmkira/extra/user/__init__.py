# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 上午12:06
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List, Union, Optional
from urllib.parse import urlparse

from llmkira.sdk.endpoint.openai import Openai, MODEL
from llmkira.sdk.func_calling import ToolRegister
from .client import UserCostClient, UserConfigClient, UserCost, UserConfig
from .schema import UserDriverMode


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class CostControl(object):

    @staticmethod
    async def add_cost(cost: UserCost):
        """
        :param cost: cost
        :return: list
        """
        _user_data = await UserCostClient().insert(data=cost)
        return _user_data

    @staticmethod
    async def get_cost_by_uid(uid: str) -> List[UserCost]:
        return await UserCostClient().read_by_uid(uid=uid)


class UserControl(object):
    @staticmethod
    def get_model():
        return MODEL.__args__

    @staticmethod
    async def get_driver_config(
            uid: str
    ) -> UserConfig.LlmConfig:
        """
        :param uid: user id
        :return: UserConfig.LlmConfig(Token/Driver)
        """
        _user_data = await UserConfigClient().read_by_uid(uid=uid)
        _user_data = _user_data or UserConfig(uid=uid)
        assert _user_data.llm_driver, "user driver is empty"
        return _user_data.llm_driver

    @staticmethod
    def uid_make(
            platform: str,
            user_id: Union[str, int]
    ):
        """
        :param platform: platform.
        :param user_id: user id.
        :raise AssertionError: user id is not str | platform is empty.
        :return: str
        """
        if isinstance(user_id, int):
            user_id = str(user_id)
        assert isinstance(user_id, str), "user id is not str"
        assert platform, "platform is empty"
        return f"{platform}:{user_id}"

    @staticmethod
    async def clear_endpoint(
            uid: str
    ):
        """
        :param uid: user id
        :return: bool
        """
        _user_data = await UserConfigClient().read_by_uid(uid=uid)
        if not _user_data:
            return True
        _user_data.llm_driver.driver = None
        await UserConfigClient().update(uid=uid, data=_user_data)
        return True

    @staticmethod
    async def set_endpoint(
            uid: str,
            api_key: str,
            endpoint: str = None,
            model: str = None,
            org_id: str = None
    ) -> Openai.Driver:
        """
        :param uid: user id
        :param api_key: openai api key
        :param endpoint: openai endpoint
        :param model: openai model
        :param org_id: openai org_id id:
        :raise ValidationError: openai model is not valid
        :return: new_driver
        """
        # assert model in MODEL.__args__, f"openai model is not valid,must be one of {MODEL.__args__}"
        if model not in MODEL.__args__:
            model = MODEL.__args__[0]
        _user_data = await UserConfigClient().read_by_uid(uid=uid)
        _user_data = _user_data or UserConfig(uid=uid)
        new_driver = Openai.Driver(endpoint=endpoint, api_key=api_key, model=model, org_id=org_id)
        _user_data.llm_driver.driver = new_driver
        await UserConfigClient().update(uid=uid, data=_user_data)
        return new_driver

    @staticmethod
    async def block_plugin(
            uid: str,
            plugin_name: str
    ) -> list:
        """
        :param uid: user id
        :param plugin_name: plugin name
        :return: list
        """
        if not (plugin_name in ToolRegister().functions):
            raise ValueError(f"plugin {plugin_name} is not exist :(")
        _user_data = await UserConfigClient().read_by_uid(uid=uid)
        _user_data = _user_data or UserConfig(uid=uid)
        _user_data.plugin_subs.block(plugin_name=plugin_name)
        await UserConfigClient().update(uid=uid, data=_user_data)
        return _user_data.plugin_subs.block_list

    @staticmethod
    async def unblock_plugin(
            uid: str,
            plugin_name: str
    ) -> list:
        """
        :param uid: user id
        :param plugin_name: plugin name
        :return: list
        """
        _user_data = UserConfigClient().read_by_uid(uid=uid)
        _user_data = _user_data or UserConfig(uid=uid)
        _user_data.plugin_subs.unblock(plugin_name=plugin_name)
        await UserConfigClient().update(uid=uid, data=_user_data)
        return _user_data.plugin_subs.block_list

    @staticmethod
    async def set_token(
            uid: str,
            token: Optional[str] = None
    ) -> Optional[str]:
        """
        :param uid: user id
        :param token: bind token
        :raise ValidationError: openai model is not valid
        :return: new_driver
        """
        # assert model in MODEL.__args__, f"openai model is not valid,must be one of {MODEL.__args__}"
        _user_data = await UserConfigClient().read_by_uid(uid=uid)
        _user_data = _user_data or UserConfig(uid=uid)
        _user_data.llm_driver.token = token
        await UserConfigClient().update(uid=uid, data=_user_data)
        return token
