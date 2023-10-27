# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 上午11:47
# @Author  : sudoskys
# @File    : default_factory.py
# @Software: PyCharm
import re
from typing import Any

from . import resign_transfer
from .schema import Builder, Parser, TransferMata


@resign_transfer()
class DefaultMessageBuilder(Builder):
    sign = TransferMata(
        platform=re.compile(r".*"),  # 匹配所有
        plugin_name="default",
        agent="receiver",
        priority=0
    )

    async def pipe(self, arg) -> Any:
        return arg


@resign_transfer()
class DefaultMessageParser(Parser):
    sign = TransferMata(
        platform=re.compile(r".*"),  # 匹配所有
        plugin_name="default",
        agent="sender",
        priority=0
    )

    async def pipe(self, arg) -> Any:
        return arg
