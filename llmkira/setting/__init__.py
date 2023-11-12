# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午12:49
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from pydantic import ConfigDict, Field, BaseModel

from .discord import BotSetting as DiscordSetting
from .kook import BotSetting as KookSetting
from .slack import BotSetting as SlackSetting
from .telegram import BotSetting as TelegramSetting


class StartSetting(BaseModel):
    """
    平台列表
    """
    discord: bool = Field(default=False)
    kook: bool = Field(default=False)
    slack: bool = Field(default=False)
    telegram: bool = Field(default=False)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_subdir(cls):
        _kwargs = {}
        if SlackSetting.available:
            _kwargs["slack"] = True
        if TelegramSetting.available:
            _kwargs["telegram"] = True
        if DiscordSetting.available:
            _kwargs["discord"] = True
        if KookSetting.available:
            _kwargs["kook"] = True
        return cls(**_kwargs)
