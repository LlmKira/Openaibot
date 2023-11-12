# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午1:41
# @Author  : sudoskys
# @File    : penne.py
# @Software: PyCharm

"""
此文件供上下使用，不可引用外部其他文件
"""
import hashlib
import os
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import field_validator, Field

from ..error import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    pass


def sha1_encrypt(string):
    """
    sha1加密算法
    """

    sha = hashlib.sha1(string.encode('utf-8'))
    encrypts = sha.hexdigest()
    return encrypts[:8]


class Driver(BaseSettings):
    """
    通用配置
    """
    endpoint: str = Field(default="https://api.openai.com/v1/chat/completions")
    api_key: str = Field(default=None)
    org_id: Optional[str] = Field(default=None)
    model: str = Field(default="gpt-3.5-turbo-0613")
    retrieve_model: str = Field(default="gpt-3.5-turbo-16k")
    proxy_address: Optional[str] = Field(None)

    # TODO:AZURE API VERSION

    @property
    def detail(self):
        """
        脱敏
        """
        api_key = "****" + str(self.api_key)[-4:]
        return (
            f"Endpoint: {self.endpoint}\nApi_key: {api_key}\n"
            f"Org_id: {self.org_id}\nModel: {self.model}\nRetrieve_model: {self.retrieve_model}"
        )

    @property
    def available(self):
        """
        检查可用性
        :return:
        """
        return all([self.endpoint, self.api_key, self.model])

    @classmethod
    def from_public_env(cls):
        openai_api_key = os.getenv("OPENAI_API_KEY", None)
        openai_endpoint = os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1/chat/completions")
        openai_org_id = os.getenv("OPENAI_API_ORG_ID", None)
        openai_model = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-0613")
        openai_model_retrieve = os.getenv("OPENAI_API_RETRIEVE_MODEL", "gpt-3.5-turbo-16k")
        openai_proxy = os.getenv("OPENAI_API_PROXY", None)
        return cls(
            endpoint=openai_endpoint,
            api_key=openai_api_key,
            org_id=openai_org_id,
            model=openai_model,
            model_retrieve=openai_model_retrieve,
            proxy_address=openai_proxy
        )

    @field_validator("api_key")
    def check_key(cls, v):
        if v:
            if len(str(v)) < 4:
                raise ValidationError("api_key is too short???")
            """
            # 严格检查
            if not len(str(v)) == 51:
                raise ValidationError("api_key must be 51 characters long")
            """
        else:
            raise ValidationError("api_key is required,pls set OPENAI_API_KEY in .env")
        return v

    @property
    def uuid(self):
        """
        取 api key 最后 3 位 和 sha1 加密后的前 8 位
        :return: uuid for token
        """
        _flag = self.api_key[-3:]
        return f"{_flag}:{sha1_encrypt(self.api_key)}"
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True, arbitrary_types_allowed=True, extra="allow")
