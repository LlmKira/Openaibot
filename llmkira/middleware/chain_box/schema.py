# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:35
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time

import shortuuid
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

from ...task.schema import TaskHeader


class Chain(BaseModel):
    thead_uuid: str = Field(..., description="Thead UUID")
    creator_uid: str = Field(default=str, description="platform:user_id")
    channel: str = Field(..., description="platform channel")
    arg: TaskHeader = Field(..., description="arg")

    uuid: str = Field(
        default=str(shortuuid.uuid()[0:5]).upper(), description="Always Auto Gen"
    )
    expire: int = Field(default=60 * 60 * 24 * 1, description="expire")
    deprecated: bool = Field(default=False, description="deprecated")
    created_times: int = Field(
        default_factory=lambda: int(time.time()), description="created_times"
    )

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    def set_expire(self, expire: int) -> "Chain":
        self.expire = expire
        return self

    @classmethod
    def create(
        cls, *, creator_uid: str, channel: str, arg: "TaskHeader", expire: int, **kwargs
    ) -> "Chain":
        return cls(
            creator_uid=creator_uid, channel=channel, arg=arg, expire=expire, **kwargs
        )

    @classmethod
    def from_redis(cls, data: dict) -> "Chain":
        """
        从redis中获取,自动检查是否带有 created_times 和 expire
        """
        assert isinstance(data, dict), "From Redis Receive Empty Data"
        if not data.get("created_times"):
            data["deprecated"] = True
        if not data.get("expire"):
            data["deprecated"] = True
        return cls.model_validate(data)

    @property
    def is_expire(self) -> bool:
        return (int(time.time()) - self.created_times > self.expire) or self.deprecated

    @model_validator(mode="before")
    def check_root(cls, values):
        arg = values.get("arg")
        if arg:
            if isinstance(arg, dict):
                values["arg"] = TaskHeader.model_validate(arg)
            if isinstance(arg, TaskHeader):
                values["arg"] = arg.model_copy(deep=True)
        return values

    @field_validator("creator_uid")
    def check_user_id(cls, v):
        if v.count(":") != 1:
            raise ValueError("Chain `creator_uid` Must Be `platform:user_id` Format")
        if not v:
            raise ValueError("Chain `creator_uid` Is Empty")
        return v

    @field_validator("channel")
    def check_address(cls, v):
        if not v:
            raise ValueError("Chain:channel is empty")
        return v
