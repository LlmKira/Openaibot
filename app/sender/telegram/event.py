# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:40
# @Author  : sudoskys
# @File    : event.py
# @Software: PyCharm


def help_message():
    return """
# Command List

`/help` - show help message
`/chat` - just want to chat with me
`/task` - chat with function_enable
`/ask` - chat with function_disable
`/tool` - check all useful tools
`/clear` - clear the chat history
`/auth` - auth the tool_call
`/learn` - set your system prompt, reset by `/learn reset`

**Private Chat Only**

`/login` - login via url or something
`/logout` - clear credential
`/env` - set v-env split by ; ,  use `/env ENV=NONE` to disable a env.

> Please confirm that that bot instance is secure, some plugins may be dangerous on unsafe instance, wink~
"""
