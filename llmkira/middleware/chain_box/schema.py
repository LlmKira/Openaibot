# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:35
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time
from typing import Any, Type, Optional

import shortuuid
from pydantic import field_validator, BaseModel, Field


class Chain(BaseModel):
    uid: str = Field(None, description="platform:user_id")
    address: str = Field(None, description="address")
    arg: Any = Field(None, description="arg")
    uuid: str = Field(default=str(shortuuid.uuid()[0:5]).upper(), description="uuid")

    created_times: int = Field(default_factory=lambda: int(time.time()), description="created_times")
    expire: int = Field(default=60 * 60 * 24 * 1, description="expire")

    deprecated: bool = Field(default=False, description="deprecated")

    def set_expire(self, expire: int):
        self.expire = expire
        return self

    @classmethod
    def from_redis(cls, data: dict):
        """
        从redis中获取,自动检查是否带有 created_times 和 expire
        """
        if not data.get("created_times"):
            data["deprecated"] = True
        if not data.get("expire"):
            data["deprecated"] = True
        return cls.model_validate(data)

    @property
    def is_expire(self):
        return (int(time.time()) - self.created_times > self.expire) or self.deprecated

    @field_validator("uid")
    def check_user_id(cls, v):
        if v.count(":") != 1:
            raise ValueError("Chain:uid format error")
        if not v:
            raise ValueError("Chain:uid is empty")
        return v

    @field_validator("address")
    def check_address(cls, v):
        if not v:
            raise ValueError("Chain:address is empty")
        return v

    def format_arg(self, arg: Type[BaseModel]):
        """
        神祗的格式化
        """
        if isinstance(self.arg, dict):
            self.arg = arg.model_validate(self.arg)
        return self
