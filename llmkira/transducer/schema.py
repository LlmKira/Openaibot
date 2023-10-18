# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel

from ..sdk.schema import File


class Parser(ABC, BaseModel):
    """
    Sender Parser
    媒体文件对象转消息对象
    """

    @abstractmethod
    def parse(self, message, file: List[File]) -> (list, List[File]):
        """
        change file list to RawMessage,pls return few message
        :return 递交消息列表,文件列表
        """
        ...


class Builder(ABC, BaseModel):
    """
    Receiver Parser
    消息对象转媒体文件
    """

    @abstractmethod
    def build(self, message) -> (bool, List[File]):
        """
        change just_file to `True` for send file only
        :return 是否要回复文本,文件列表
        """
        ...
