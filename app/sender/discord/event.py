# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 下午6:30
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm
from app.setting.discord import BotSetting


def help_message():
    return """
    `{prefix}chat` - Chat with me :)
    `{prefix}task` - Ask me do things with `func_enable`

    **Slash Command**
    `/help` - **You just did it :)**
    `/tool` - Check all useful tools
    `/clear` - wipe memory of your chat
    `/auth` - activate a task (my power)
    `/login` - set credential
    `/logout` - clear credential
    `/login_via_url` - login via url
    `/env` - set environment variable, split by ; ,  use `/env ENV=NONE` to disable a env.
    `/learn` - set your system prompt, reset by `/learn reset`

**Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance.**
""".format(prefix=BotSetting.prefix)
