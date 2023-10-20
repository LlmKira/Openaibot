# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 下午6:30
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm
from llmkira.setting.discord import BotSetting

_upload_error_message_template = [
    "I cant upload file {filename} to server {error}",
    "we cant upload {filename}:( , because {error}...",
    "Seems like you're having a bit of a problem uploading {filename}\n`{error}`",
    "just cant upload {filename} to server {error} 💍",
    "I dont know why, but I cant upload {filename} to server {error}",
    ":( I dont want to upload {filename} to server\n `{error}`",
    "{error}, {filename} 404",
    "OMG, {filename} ,ERROR UPLOAD, `{error}`",
    "WTF, I CANT UPLOAD {filename} BECAUSE `{error}`",
    "MY PHONE IS BROKEN, I CANT UPLOAD {filename} BECAUSE `{error}`",
    "As a human, I can't upload {filename} for you :( \n `{error}`"
]


class MappingDefault(dict):
    def __missing__(self, key):
        return key


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

**Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance.**
""".format(prefix=BotSetting.prefix)
