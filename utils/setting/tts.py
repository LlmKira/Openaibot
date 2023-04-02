# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午4:19
# @Author  : sudoskys
# @File    : tts.py
# @Software: PyCharm
from typing import List, Dict
from pydantic import BaseModel


class VITS(BaseModel):
    api: str = "https://api.vits.ai"
    limit: int = 100
    model_name: str = "vits"
    speaker_id: int = 0


class Azure(BaseModel):
    key: List[str] = []
    limit: int = 100
    speaker: Dict[str, str] = {"ZH": "zh-CN-XiaoxiaoNeural", "EN": "en-US-JessaNeural"}
    location: str = "eastus"
