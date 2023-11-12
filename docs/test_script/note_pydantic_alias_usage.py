# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 上午10:18
# @Author  : sudoskys
# @File    : pydantic.py
# @Software: PyCharm

from pydantic import BaseModel, Field


class Test(BaseModel):
    __slots__ = ()
    test: int = Field(0, alias="test")
    env_required: list = Field([], alias="env_required")
    env_help_docs: str = Field("")


class Child(Test):
    rs = 1
    env_required = ["test"]


_r = Child().model_dump()
_s = Child().env_help_docs
print(_r)
