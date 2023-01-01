# -*- coding: utf-8 -*-
# @Time    : 1/1/23 12:50 PM
# @FileName: details.py
# @Software: PyCharm
# @Github    ：sudoskys

from ..platform import ChatPlugin, PluginConfig
from ._plugin_tool import PromptTool
import os
from loguru import logger

modulename = os.path.basename(__file__).strip(".py")


@ChatPlugin.plugin_register(modulename)
class Details(object):
    def __init__(self):
        self._server = None
        self._text = None
        # 绝望列表
        self._keywords = ["怎么做",
                          "How to",
                          "how to",
                          "如何做",
                          "帮我",
                          "帮助我",
                          "请给我",
                          "给出建议",
                          "给建议",
                          "给我建议",
                          "给我一些",
                          "请教",
                          "如何",
                          "帮朋友",
                          "怎么",
                          "需要什么",
                          "注意什么",
                          "怎么办"]

    async def check(self, params: PluginConfig) -> bool:
        if PromptTool.isStrIn(prompt=params.text, keywords=self._keywords):
            return True
        return False

    def requirements(self):
        return []

    async def process(self, params: PluginConfig) -> list:
        _return = []
        self._text = params.text
        # 校验
        if not all([self._text]):
            return []
        # GET
        _return.append(f"仔细思考 and show your step.")
        logger.trace(_return)
        return _return
