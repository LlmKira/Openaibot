# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午11:38
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import ABC, abstractmethod

from pydantic import field_validator, Field

from llmkira.sdk.endpoint import Driver
from pydantic_settings import BaseSettings


class ProviderSetting(BaseSettings):
    provider: str = Field("PUBLIC", validation_alias="SERVICE_PROVIDER")

    @property
    def is_open_everyone(self):
        return self.provider.upper() == "PUBLIC"

    @field_validator("provider")
    def provider_upper(cls, v):
        return v.upper()


ProviderSettingObj = ProviderSetting()


class ProviderException(Exception):

    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider

    def __str__(self):
        if self.provider:
            return f"\n🥐 Provider {self.provider} Say:\n{self.message}"
        return f"\n🧊 {self.message}"


class BaseProvider(ABC):
    name: str

    def __init__(self, *args, **kwargs):
        if not self.name:
            raise ProviderException("Provider must have name", provider="BaseProvider")

    @abstractmethod
    def config_docs(self):
        """
        配置文档
        """
        return "Base Provider"

    @abstractmethod
    async def authenticate(self, uid, token, status) -> bool:
        """
        必须提供认证文档
        """
        raise ProviderException("Base Provider auth your token,refer docs", provider=self.name)

    @abstractmethod
    async def request_driver(self, uid, token) -> Driver:
        """
        根据 Token 申请使用 Public Driver
        """
        raise ProviderException("Base Provider cant request driver", provider=self.name)
