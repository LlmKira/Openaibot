# -*- coding: utf-8 -*-
# @Time    : 2023/3/31 下午11:55
# @Author  : sudoskys
# @File    : profile.py
# @Software: PyCharm
from typing import Union, Optional

from loguru import logger
from pydantic import BaseModel


class ProfileReturn(BaseModel):
    bot_id: Union[str, int] = 0
    bot_name: str = ""
    mentions: Optional[str] = None


class ProfileManager(object):
    def __init__(self):
        self._bot_profile = {}

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
        if init:
            _profile = self.set_bot_profile(domain="sign_api", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init API Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="sign_api"))

    def access_telegram(self, bot_name: str = None, bot_id: int = None, mentions: str = None, init=False):
        if init:
            _profile = self.set_bot_profile(domain="telegram", bot_id=bot_id, bot_name=bot_name, mentions=mentions)
            logger.success(f"Init Telegram Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="telegram"))

    def access_qq(self, bot_name=None, bot_id=None, init=False):
        if init:
            _profile = self.set_bot_profile(domain="qq", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init QQ Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="qq"))

    def set_bot_profile(self, domain=None, bot_id=None, bot_name=None, **kwargs):
        if not domain:
            raise Exception("ProfileManager:Missing Name")
        if not bot_id or not bot_name:
            raise Exception("BOT:NONE")
        _data = {"bot_id": bot_id, "bot_name": bot_name}
        _data.update(**kwargs)
        self._bot_profile[domain] = _data
        return _data

    def get_bot_profile(self, domain=None):
        if not self._bot_profile.get(domain):
            raise Exception("ProfileManager:Missing Name")
        return self._bot_profile.get(domain)


GlobalProfileManager = ProfileManager()
