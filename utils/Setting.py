# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Setting.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from typing import Union

from loguru import logger
from pydantic import BaseModel

_bot_profile = {}


def _init_():
    global _bot_profile
    try:
        _bot_profile.get("1")
    except:
        _bot_profile = {}


_init_()


class ProfileReturn(BaseModel):
    bot_id: Union[str, int] = 0
    bot_name: str = ""


class ProfileManager(object):
    global _bot_profile

    @staticmethod
    def name_generate(first_name, last_name):
        # 反转内容
        _bot_full_name = f"{first_name}{last_name}"
        _bot_split_name = _bot_full_name.split()
        _bot_split_name: list
        _bot_name = _bot_full_name if not len(_bot_split_name) > 1 else _bot_split_name[1]
        _bot_name = _bot_name if _bot_name else "Assistant"
        _bot_name = _bot_name[:12]
        return _bot_name

    def access_api(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="api", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init API Bot Profile: {_bot_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="api"))

    def access_telegram(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="telegram", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init Telegram Bot Profile: {_bot_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="telegram"))

    def access_qq(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="qq", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init QQ Bot Profile: {_bot_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="qq"))

    def set_bot_profile(self, domain=None, bot_id=None, bot_name=None):
        global _bot_profile
        if not domain:
            raise Exception("ProfileManager:Missing Name")
        if not bot_id or not bot_name:
            raise Exception("BOT:NONE")
        _data = {"bot_id": bot_id, "bot_name": bot_name}
        _bot_profile[domain] = _data
        return _data

    def get_bot_profile(self, domain=None):
        global _bot_profile
        if not _bot_profile.get(domain):
            raise Exception("ProfileManager:Missing Name")
        return _bot_profile.get(domain)
