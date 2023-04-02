# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午11:18
# @Author  : sudoskys
# @File    : config.py
# @Software: PyCharm

from dotenv import load_dotenv
from typing import Set, List, Dict, Optional, Any, Union, Literal

from loguru import logger
from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    RedisDsn,
    Field, validator,
)

# 二级数据类
from .tts import VITS, Azure
from .proxy import ProxySetting
from .llm import OpenAISetting, ChatGPTSetting

# 提前导入加载变量
load_dotenv()


class LLMSettings(BaseSettings):
    type: Literal['openai', 'chatgpt'] = 'openai'
    openai: OpenAISetting = OpenAISetting()
    chatgpt: ChatGPTSetting = ChatGPTSetting()


class ModerationSettings(BaseSettings):
    DFA: bool = False
    DFA_path: str = "./Data/Danger.form"
    Openai_moderation: bool = False
    Openai_moderation_type: Optional[List] = [
        "sexual",
        "hate/threatening",
        "sexual/minors",
        "violence",
        "violence/graphic"
    ]

    @validator('Openai_moderation_type')
    def check_moderation_type(cls, v):
        # 遍历
        for i in v:
            # 如果不在列表中，就抛出异常
            if i not in [
                "sexual",
                "hate/threatening",
                "sexual/minors",
                "violence",
                "violence/graphic"
            ]:
                raise ValueError("审核类型不正确")
        return v


class TTSSettings(BaseSettings):
    status: bool = False
    select: Literal['vits', 'azure'] = "vits"
    vits: VITS = VITS()
    azure: Azure = Azure()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_prefix = "TTS_"

    @validator('select')
    def check_select(cls, v):
        if v not in ['vits', 'azure']:
            raise ValueError("TTS引擎选择错误")
        return v


class MediaSettings(BaseSettings):
    blip_status: bool = False
    blip_api: str = "http://127.0.0.1:10885/upload/"
    sticker_status: bool = True
    sticker_penalty: float = 0.95

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_prefix = "MEDIA_"

    @validator('sticker_penalty')
    def check_sticker_penalty(cls, v):
        if v > 1 or v < 0:
            # auto adjust
            logger.warning("sticker_penalty 超出范围，自动调整为 0.95")
            return 0.95
        return v


class DataSettings(BaseSettings):
    redis_dsn: RedisDsn = Field(None, env='REDIS_DSN')
    proxy_setting: ProxySetting = ProxySetting()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


class AppConfig(BaseSettings):
    moderation: ModerationSettings = ModerationSettings()
    tts: TTSSettings = TTSSettings()
    media: MediaSettings = MediaSettings()
    bucket: DataSettings = DataSettings()
    llm: LLMSettings = LLMSettings()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def create_appconfig(json: dict) -> AppConfig:
    return AppConfig(**json)
