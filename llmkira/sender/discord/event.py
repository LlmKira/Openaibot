# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 下午6:30
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm
from llmkira.setting.discord import BotSetting


def help_message():
    return """ 
    `{prefix}chat` - Chat with me :)
    `{prefix}task` - Ask me do things with `func_enable`
    
    **Slash Command**
    `/help` - **You just did it :)**
    `/tool` - Check all useful tools
    `/clear` - wipe memory of your chat
    `/auth` - activate a task (my power)
    `/bind` - bind third party platform
    `/unbind` - unbind platform
    `/set_endpoint` - set endpoint
    `/clear_endpoint` - clear endpoint and key
    `/env` - set environment variable
    `/token` - bind your service provider token
    `/token_clear` - clear your service provider token
    `/func_ban` - ban function
    `/func_unban` - unban function

**Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance.**
""".format(prefix=BotSetting.prefix)
