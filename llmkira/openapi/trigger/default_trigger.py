# -*- coding: utf-8 -*-
# @Time    : 2023/10/27 下午4:05
# @Author  : sudoskys
# @File    : default_trigger.py
# @Software: PyCharm
from . import resign_trigger, Trigger


@resign_trigger(Trigger(on_platform="telegram", action="deny", priority=0))
async def on_chat_message(message: str, uid: str, **kwargs):
    """
    :param message: RawMessage
    :return:
    """
    if "<deny>" in message:
        return True
