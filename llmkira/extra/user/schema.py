# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 上午12:06
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
# 负责任务前后的APIKey信息管理和验证机制(认证可信平台) 平台:ID
import time
from enum import Enum
from typing import List, Union, Optional

from pydantic import BaseModel, Field, BaseSettings, validator

from ...sdk.endpoint.openai import Openai


class UserDriverMode(Enum):
    public = 100
    """公共环境变量，只有预先设定的规则管控了Driver的配置，此情况无论如何都不能配置其他endpoint"""

    private = 200
    """私有 环境变量/私有端点，要求用户无论如何自己配置，用户可以自己产生 Driver"""

    proxy_public = 300
    """代理公共环境变量，也就是额外的token计费系统控制了公共环境变量的使用"""


# 基本单元

class UserCost(BaseModel):
    """用户消费记录
    """

    class Cost(BaseModel):
        """消费记录细节
        """
        cost_by: str = Field("chat", description="环节")
        token_usage: int = Field(0)
        token_uuid: str = Field(None, description="Api Key 的 hash")
        model_name: str = Field(None, description="Model Name")
        provide_type: int = Field(None, description="认证模式")

        @classmethod
        def by_function(cls, function_name: str,
                        token_usage: int,
                        token_uuid: str,
                        model_name: str,
                        ):
            return cls(cost_by=function_name, token_usage=token_usage, token_uuid=token_uuid, model_name=model_name)

    request_id: str = Field(default=None, description="请求 UUID")
    uid: str = Field(default=None, description="用户 UID ,注意是平台+用户")
    cost: Cost = Field(default=None, description="消费记录")
    cost_time: int = Field(default=None, description="消费时间")
    meta: dict = Field(default={}, description="元数据")

    @classmethod
    def create_from_function(
            cls,
            uid: str,
            request_id: str,
            cost_by: str,
            token_usage: int,
            token_uuid: str,
            model_name: str,
    ):
        return cls(
            request_id=request_id,
            uid=uid,
            cost=cls.Cost.by_function(
                function_name=cost_by,
                token_usage=token_usage,
                token_uuid=token_uuid,
                model_name=model_name,
            ),
            cost_time=int(time.time()),
        )

    @classmethod
    def create_from_task(
            cls,
            uid: str,
            request_id: str,
            cost: Cost,
    ):
        return cls(
            request_id=request_id,
            uid=uid,
            cost=cost,
            cost_time=int(time.time()),
        )

    class Config:
        extra = "ignore"
        allow_mutation = True
        arbitrary_types_allowed = True
        validate_assignment = True
        validate_all = True
        validate_on_assignment = True
        json_encoders = {
            Openai.Driver: lambda v: v.dict(),
        }


class UserConfig(BaseSettings):
    """
    :tip 注意此类和公共环境变量的区别！禁止用户使用 公共变量 请求 私有端点！
    """

    class LlmConfig(BaseModel):
        """用户配置
        driver 作为一个单例模式
        其他 `公共授权` 组件！
        """
        driver: Optional[Openai.Driver] = Field(None, description="私有端点配置")
        token: Optional[str] = Field(None, description="代理认证系统的token")
        provider: Optional[str] = Field(None, description="认证平台")

        @property
        def mode(self):
            """
            :return: 返回模式
            """
            if self.driver:
                if self.driver.api_key:
                    return UserDriverMode.private
            if self.token and not self.driver:
                return UserDriverMode.proxy_public
            return UserDriverMode.public

        @classmethod
        def default(cls):
            return cls()

        def set_proxy_public(self, token: str, provider: str):
            self.provider = provider
            self.token = token
            return self

        @validator("provider")
        def upper_provider(cls, v):
            if v:
                return v.upper()
            return v

    class PluginConfig(BaseModel):
        block_list: List[str] = Field([], description="黑名单")

        @classmethod
        def default(cls):
            return cls()

        def block(self, plugin_name: str) -> "PluginConfig":
            if plugin_name not in self.block_list:
                self.block_list.append(plugin_name)
            return self

        def unblock(self, plugin_name: str) -> "PluginConfig":
            if plugin_name in self.block_list:
                self.block_list.remove(plugin_name)
            return self

    created_time: int = Field(default=int(time.time()), description="创建时间")
    last_use_time: int = Field(default=int(time.time()), description="最后使用时间")
    uid: Union[str, int] = Field(None, description="用户UID")
    plugin_subs: PluginConfig = Field(default_factory=PluginConfig.default, description="插件订阅")
    llm_driver: LlmConfig = Field(default_factory=LlmConfig.default, description="驱动")

    @validator("uid")
    def check_user_id(cls, v):
        if v:
            return str(v)
        return v

    class Config:
        extra = "ignore"
        allow_mutation = True
        arbitrary_types_allowed = True
        validate_assignment = True
        validate_all = True
        validate_on_assignment = True
        json_encoders = {
            Openai.Driver: lambda v: v.dict(),
        }
