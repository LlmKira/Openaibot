# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午4:26
# @Author  : sudoskys
# @File    : llm.py
# @Software: PyCharm
from pydantic import BaseModel


class ChatGPTSetting(BaseModel):
    model: str = "text-davinci-003"
    token_limit: int = 4000


class OpenAISetting(BaseModel):
    model: str = "text-davinci-003"
    token_limit: int = 4000
