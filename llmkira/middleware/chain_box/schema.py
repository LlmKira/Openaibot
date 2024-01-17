# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:35
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time
from typing import List

import shortuuid
from pydantic import field_validator, BaseModel, Field, ConfigDict

from ...task.schema import TaskHeader


class ChainBat(BaseModel):
    class ChainCell(BaseModel):
        meta: TaskHeader = Field(..., description="meta data")
        creator_uid: str = Field(..., description="platform:user_id")
        communication_channel: str = Field(..., description="platform channel")

        expiration: int = Field(default=60 * 60 * 24 * 1, description="expire seconds")
        uuid: str = Field(
            str(shortuuid.uuid()[0:5]).upper(), description="Always Auto Gen"
        )
        created_date: int = Field(default=int(time.time()), description="created_times")

        @field_validator("creator_uid")
        def check_user_id(cls, v):
            if v.count(":") != 1:
                raise ValueError(
                    "ChainCell `creator_uid` Must Be `platform:user_id` Format"
                )
            if not v:
                raise ValueError("ChainCell `creator_uid` Is Empty")
            return v

        def set_expire(self, expiration_second: int) -> "ChainBat.ChainCell":
            self.expiration = expiration_second
            return self

        @classmethod
        def create(
            cls,
            *,
            meta: TaskHeader,
            creator_uid: str,
            communication_channel: str,
            expiration: int,
            **kwargs,
        ) -> "ChainBat.ChainCell":
            return cls(
                meta=meta.model_copy(
                    deep=True
                ),  # NOTE: deep copy to avoid circular reference
                creator_uid=creator_uid,
                communication_channel=communication_channel,
                expiration=expiration,
                **kwargs,
            )

    thead_uuid: str = Field(..., description="Thead UUID")
    chains: List[ChainCell] = Field(..., description="chains")

    @property
    def length(self):
        return len(self.chains)


class Chain(BaseModel):
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
