# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Setting.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from typing import Union

# from graia.ariadne import Ariadne
# from graia.ariadne.model import Profile
# TODO: ^^^ Will be imported soon, maybe along with a commit feating "at" to call ^^^
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
    bot_id: Union[str, int]
    bot_name: str


async def qqbot_profile_init(bot):
    global _bot_profile
    _me: Profile = await bot.get_bot_profile()
    _name = _me.nickname
    _bot_profile = {"id": bot.account, "name": _name}
    logger.success(f"Init QQ Bot:{_bot_profile}")
    return _bot_profile


"""
def api_profile_init(apicfg):
    global _bot_profile
    _bot_profile = {"id": apicfg.botid, "name": apicfg.botname}
    logger.success(f"Init APIServer: {_bot_profile}")
    return _bot_profile
"""


class ProfileManager(object):
    global _bot_profile

    def access_api(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="api", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init QQ Bot Profile: {_bot_profile}")
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


