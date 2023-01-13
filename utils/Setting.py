# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Setting.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器

#from graia.ariadne import Ariadne
#from graia.ariadne.model import Profile
# ^^^ Unused import? ^^^
from loguru import logger

global _bot_profile


def qqbot_profile_init():
    global _bot_profile
    # _me: Profile = await bot.get_bot_profile()
    _name = "None"
    _bot_profile = {"id": 3552600542, "name": _name[:6]}
    logger.success(f"Init QQ Bot:{_bot_profile}")
    return bot_profile


async def bot_profile_init(bot):
    global _bot_profile
    _me = await bot.get_me()
    first_name = _me.first_name if _me.first_name else ""
    last_name = _me.last_name if _me.last_name else ""
    _name = f"{first_name}{last_name}"
    _bot_profile = {"id": _me.id, "name": _name[:6]}
    logger.success(f"Init Telegram Bot:{_bot_profile}")
    return bot_profile


def bot_profile():
    global _bot_profile
    return _bot_profile
