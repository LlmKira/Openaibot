# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午7:27
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import ABC
from typing import Optional, Any, Union, List
from typing import TYPE_CHECKING

import shortuuid
from pydantic import BaseModel, Field, PrivateAttr

from .tee import Driver

if TYPE_CHECKING:
    from ..schema import AssistantMessage


class LlmResult(BaseModel, ABC):
    """
    LlmResult
    """

    id: str = Field(default_factory=lambda x: str(shortuuid.uuid()[0:8]), alias="request_id")
    object: str
    created: int
    model: str
    choices: list
    usage: Any

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @property
    def result_type(self):
        return self.object

    def ack(self):
        """
        向上转型
        """
        return self

    @property
    def default_message(self) -> "AssistantMessage":
        return self.choices[0].message


class LlmRequest(BaseModel, ABC):
    """
    LlmRequest
    """

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    _config: Driver = PrivateAttr()
    messages: list
    temperature: Optional[float] = 1
    top_p: Optional[float]
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]]
    max_tokens: Optional[int]
    presence_penalty: Optional[float]
    frequency_penalty: Optional[float]
    seed: Optional[int]

    # 用于调试
    _echo: bool = Field(default=None)

    @property
    def config(self):
        return self._config

    @property
    def model(self):
        if self.config:
            return self.config.model
        return None

    @classmethod
    def init(cls, driver: Driver, **kwargs):
        """
        Init private args
        :param driver: Driver
        :param kwargs: 配置
        :return: LlmRequest Object
        """
        return cls(
            **kwargs
        ).set_driver(driver=driver)

    def set_driver(self, driver: Driver):
        self._config = driver
        return self

    @property
    def schema_map(self) -> dict:
        return {
            "model": True,
            "messages": True,
            "temperature": True,
            "top_p": True,
            "n": True,
            "stop": True,
            "max_tokens": True,
            "seed": True,
            "presence_penalty": True,
            "frequency_penalty": True,
        }

    def create_params(self):
        _arg = self.dict(
            exclude_none=True,
            include=self.schema_map
        )
        assert "messages" in _arg, "messages is required"
        _arg["model"] = self.model
        _arg = {
            k: v
            for k, v in _arg.items()
            if v is not None
        }
        return _arg

    def proxy_address(self):
        return self._config.proxy_address

    async def create(
            self,
            **kwargs
    ):
        raise NotImplementedError


class BaseSchemaType(BaseModel, ABC):
    name: str = "base"
