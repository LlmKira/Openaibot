# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 上午12:06
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import List, Union, Optional

from llmkira.sdk.endpoint.openai import Openai
from pydantic import BaseModel, Field, BaseSettings, validator


# 负责任务前后的APIKey信息管理和验证机制(认证可信平台) 平台:ID


class UserInfo(BaseSettings):
    class Plugin(BaseModel):
        lock: List[str] = []

    class Cost(BaseModel):
        cost_by: str = Field("chat", description="环节")
        token_usage: int = Field(0)
        token_uuid: str = Field(None, description="API KEY 的 hash")
        model_name: str = Field(None, description="模型")

        @classmethod
        def by_function(cls, function_name: str,
                        token_usage: int,
                        token_uuid: str,
                        model_name: str,
                        ):
            return cls(cost_by=function_name, token_usage=token_usage, token_uuid=token_uuid, model_name=model_name)

    user_id: Union[str, int] = Field(None, description="用户ID")
    plugin_subs: Plugin = Field(Plugin(), description="插件的设置")
    costs: List[Cost] = Field([], description="消费记录")
    llm_driver: Optional[Openai.Driver] = None
    update_driver: bool = False

    def total_cost(self):
        return sum([cost.token_usage for cost in self.costs])

    @validator("user_id")
    def check_user_id(cls, v):
        return str(v)
