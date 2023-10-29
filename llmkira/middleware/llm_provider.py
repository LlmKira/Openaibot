# -*- coding: utf-8 -*-
# @Time    : 2023/10/27 下午2:13
# @Author  : sudoskys
# @File    : provider.py
# @Software: PyCharm
from loguru import logger

from llmkira.extra.user import UserControl, UserConfig, UserDriverMode
from llmkira.middleware.service_provider.schema import ProviderSettingObj
from .service_provider import loaded_provider, PublicProvider

if not loaded_provider:
    raise Exception("⚠️ No Any Driver Provider Loaded, Even Public Provider")


class GetAuthDriver(object):
    def __init__(self, uid: str):
        assert uid, "uid is empty"
        self.uid = uid
        self.user = None

    @classmethod
    def from_platform(cls, platform: str, userid: str):
        return cls(uid=UserControl.uid_make(platform=platform, user_id=userid))

    def provide_type(self):
        if not isinstance(self.user, UserConfig.LlmConfig):
            return None
        return self.user.mode

    async def get(self):
        """
        :raise ProviderException: No Any LLM Config Available
        :return: Openai.Driver
        """
        self.user = await UserControl.get_driver_config(uid=self.uid)
        assert isinstance(self.user, UserConfig.LlmConfig), "UserConfig.LlmConfig is empty"
        # 配置了自己的私有例
        if self.user.mode == UserDriverMode.private:
            return self.user.driver
        # Public Provider
        if ProviderSettingObj.is_open_everyone:
            provider = PublicProvider()
            logger.debug(f"🍦 Public Provider({provider.name})&Mode({self.user.mode})&UID({self.uid})")
            if await provider.authenticate(
                    uid=self.uid,
                    token=self.user.token, status=self.user.mode):
                return await provider.request_driver(uid=self.uid, token=self.user.token)
        else:
            # 用户需要特别配置 Token
            provider = loaded_provider()
            if await provider.authenticate(
                    uid=self.uid,
                    token=self.user.token,
                    status=self.user.mode
            ):
                return await provider.request_driver(uid=self.uid, token=self.user.token)
        """
        raise ProviderException(
            f"AuthChanged {self.user.provider} >>change>> {loaded_provider.name.upper()}"
            f"\n🥕 Provider({loaded_provider.name})&Mode({self.user.mode})&UID({self.uid})"
            f"\n🍦 Auth Docs: {loaded_provider().config_docs()}"
        )
        """
