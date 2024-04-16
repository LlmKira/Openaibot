# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午12:49
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from pydantic import ConfigDict, BaseModel

from .discord import BotSetting as DiscordSetting
from .kook import BotSetting as KookSetting
from .slack import BotSetting as SlackSetting
from .telegram import BotSetting as TelegramSetting


class PlatformSetting(BaseModel):
    """
    平台列表
    """

    discord: bool = False
    kook: bool = False
    slack: bool = False
    telegram: bool = False
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_subdir(cls):
        return cls(
            discord=DiscordSetting.available,
            kook=KookSetting.available,
            slack=SlackSetting.available,
            telegram=TelegramSetting.available,
        )
