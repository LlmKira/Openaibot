# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Setting.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from typing import Union, Optional

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
    mentions: Optional[str] = None


class ProfileManager(object):
    global _bot_profile

    @staticmethod
    def name_generate(first_name, last_name):
        # 反转内容
        _bot_full_name = f"{first_name}{last_name}"
        _bot_split_name = _bot_full_name.split()
        _bot_split_name: list
        _bot_name = _bot_full_name if not len(
            _bot_split_name) > 1 else _bot_split_name[1]
        _bot_name = _bot_name if _bot_name else "Assistant"
        _bot_name = _bot_name[:12]
        return _bot_name

    def access_base(self, bot_name=None, bot_id=None, init=False, mentions: str = None, domain: str = ''):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(
                domain=domain, bot_id=bot_id, bot_name=bot_name, mentions=mentions)
            logger.success(
                f"Init {domain.capitalize()} Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain=domain))

    def access_api(self, bot_name=None, bot_id=None, init=False):
        return self.access_base(bot_name=bot_name, bot_id=bot_id,
                         init=init, domain='api')

    def access_telegram(self, bot_name: str = None, bot_id: int = None, mentions: str = None, init=False):
        return self.access_base(bot_name=bot_name, bot_id=bot_id,
                         init=init, domain='telegram', mentions=mentions)

    def access_qq(self, bot_name=None, bot_id=None, init=False):
        return self.access_base(bot_name=bot_name, bot_id=bot_id,
                         init=init, domain='qq')

    def access_wechat(self, bot_name=None, bot_id=None, init=False):
        return self.access_base(bot_name=bot_name, bot_id=bot_id,
                         init=init, domain='wechat')

    def set_bot_profile(self, domain=None, bot_id=None, bot_name=None, **kwargs):
        global _bot_profile
        if not domain:
            raise Exception("ProfileManager:Missing Name")
        if not bot_id or not bot_name:
            raise Exception("BOT:NONE")
        _data = {"bot_id": bot_id, "bot_name": bot_name}
        _data.update(**kwargs)
        _bot_profile[domain] = _data
        return _data

    def get_bot_profile(self, domain=None):
        global _bot_profile
        if not _bot_profile.get(domain):
            raise Exception("ProfileManager:Missing Name")
        return _bot_profile.get(domain)
