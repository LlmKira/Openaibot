# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 下午10:19
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Literal, List

from pydantic import BaseModel, Field, validator

SENDER = {}
RECEIVER = {}


def router_set(role: Literal["sender", "receiver"], name: str):
    if role == "sender":
        SENDER[name] = name
    elif role == "receiver":
        RECEIVER[name] = name
    else:
        raise ValueError(f"role must in sender or receiver, not {role}")


ROUTER_METHOD = Literal["push", "chat", "task"]
ALLOW_METHOD = ["push", "chat", "task"]


class Router(BaseModel):
    from_: str = Field(..., description="Sender")
    to_: str = Field(..., description="Receiver")
    user_id: int = Field(..., description="用户ID")
    rules: str = Field(..., description="URL")
    method: ROUTER_METHOD = Field('push', description="")  # "summary"

    @classmethod
    def build_from_receiver(cls, receiver, user_id, dsn: str):
        try:
            from_, rules, _method = dsn.split("@", maxsplit=3)
        except Exception as e:
            raise ValueError(f"dsn error {dsn},{e}. exp: rss@http://rss.toml@push  available: {SENDER}")
        if from_ not in SENDER:
            raise ValueError(f"sender must in {SENDER}, not {from_}")
        if _method not in ALLOW_METHOD:
            raise ValueError(f"method must in {ALLOW_METHOD}, not {_method}")
        return cls(from_=from_, to_=receiver, user_id=user_id, rules=rules)

    def dsn(self, user_dsn=False):
        if user_dsn:
            return f"{self.from_}@{self.rules}@{self.method}"
        return f"{self.from_}@{self.to_}@{self.user_id}@{self.rules}@{self.method}"


class RouterCache(BaseModel):
    router: List[Router] = []

    @validator("router", always=True)
    def router_validate(cls, v):
        _dict = {}
        for item in v:
            _dict[item.dsn()] = item
        v = list(_dict.values())
        return v
