# -*- coding: utf-8 -*-
# @Time    : 12/27/22 7:19 PM
# @FileName: module.py
# @Software: PyCharm
# @Github    ：sudoskys

from pydantic import BaseModel
from loguru import logger


class PluginParam(BaseModel):
    text: str = ""
    server: dict = []


class PluginConfig(BaseModel):
    text: str = ""
    server: list = {}


class ChatPlugin(object):
    PLUGINS = {}

    def process(self, param: PluginParam, plugins=()) -> list:
        _return = []
        if plugins == ():
            plugins = self.PLUGINS.keys()
        for plugin_name in plugins:
            obj = self.PLUGINS[plugin_name]()
            try:
                if obj.check(param):
                    config = param.dict()
                    config.update({"server": param.server.get(plugin_name) if param.server.get(plugin_name) else []})
                    plugin_config: PluginConfig
                    plugin_config = PluginConfig(**config)
                    # print(plugin_config.dict())
                    text = obj.process(plugin_config)
                    _return.extend(text)
            except Exception as e:
                logger.error(f"Plugin:{plugin_name} --Error:{e}")
        return _return

    @classmethod
    def plugin_register(cls, plugin_name):
        def wrapper(plugin):
            cls.PLUGINS.update({plugin_name: plugin})
            return plugin

        return wrapper
