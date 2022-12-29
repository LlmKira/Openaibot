# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Setting.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from loguru import logger

global _bot_profile


async def bot_profile_init(bot):
    global _bot_profile
    _me = await bot.get_me()
    first_name = _me.first_name if _me.first_name else ""
    last_name = _me.last_name if _me.last_name else ""
    _name = f"{first_name}{last_name}"
    _bot_profile = {"id": _me.id, "name": _name[:6]}
    logger.success(f"Init Bot:{_bot_profile}")
    return bot_profile


def bot_profile():
    global _bot_profile
    return _bot_profile
