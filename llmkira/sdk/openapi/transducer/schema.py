# -*- coding: utf-8 -*-
import re
from abc import ABC, abstractmethod
from typing import Literal, Any

from pydantic import BaseModel, Field


class TransferMata(BaseModel):
    """
    注册标头
    """
    platform: re.Pattern
    plugin_name: str
    # 优先级
    priority: int = Field(default=0, ge=-100, le=100)
    # 适用端 (sender/receiver)
    agent: Literal["sender", "receiver", None] = Field(default=None)


class AbstractTransfer(ABC):
    sign: Any

    async def pipe(self, *args, **kwargs) -> Any:
        pass


class Builder(AbstractTransfer):
    """
    Receiver Parser
    消息对象转媒体文件
    """
    sign: TransferMata

    @abstractmethod
    async def pipe(self, arg: dict) -> Any:
        """
        change just_file to `True` for send file only
        :return 是否要回复文本,文件列表
        """
        return arg


class Parser(AbstractTransfer):
    """
    Sender Parser
    媒体文件对象转消息对象
    """
    sign: TransferMata

    @abstractmethod
    async def pipe(self, arg: dict) -> Any:
        """
        change file list to RawMessage,pls return few message
        :return 回环消息列表,文件列表
        """
        return arg
