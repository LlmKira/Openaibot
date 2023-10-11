# -*- coding: utf-8 -*-
# @Time    : 2023/10/11 下午3:35
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Any, Type

import shortuuid
from pydantic import BaseModel, Field, validator


class Chain(BaseModel):
    user_id: str = Field(None, description="user_id")
    address: str = Field(None, description="address")
    time: int = 0
    arg: Any = Field(None, description="arg")
    uuid: str = shortuuid.uuid()[0:8]

    @validator("user_id")
    def check_user_id(cls, v):
        if not v:
            raise ValueError("Chain:user_id is empty")
        return v

    @validator("address")
    def check_address(cls, v):
        if not v:
            raise ValueError("Chain:address is empty")
        return v

    def format_arg(self, arg: Type[BaseModel]):
        if isinstance(self.arg, dict):
            self.arg = arg.parse_obj(self.arg)
        return self
