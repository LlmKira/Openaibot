# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午4:19
# @Author  : sudoskys
# @File    : tts.py
# @Software: PyCharm
from typing import List, Dict
from pydantic import BaseModel


class VITS(BaseModel):
    api: str
    limit: int
    model_name: str
    speaker_id: int


class Azure(BaseModel):
    key: List[str]
    limit: int
    speaker: Dict[str, str]
    location: str
