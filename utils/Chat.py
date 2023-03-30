# -*- coding: utf-8 -*-
# @Time    : 12/9/22 8:15 AM
# @FileName: Chat.py
# @Software: PyCharm
# @Github    ：sudoskys

import time
from typing import Optional
from pydantic import BaseModel


class FromChat(BaseModel):
    id: int
    name: str = "猫娘群"


class FromUser(BaseModel):
    id: int
    name = "猫娘"
    admin: bool = False


class UserMessage(BaseModel):
    id: int = 0
    from_user: FromUser
    from_chat: FromChat
    text: str
    prompt: list
    date: int = int(time.time() * 1000)
    reply_user_id: Optional[int]
    reply_chat_id: Optional[int]
