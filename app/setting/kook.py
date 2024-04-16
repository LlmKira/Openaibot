# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:59
# @Author  : sudoskys
# @File    : kook.py
# @Software: PyCharm
from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KookBot(BaseSettings):
    """
    代理设置
    """

    token: Optional[str] = Field(None, validation_alias="KOOK_BOT_TOKEN")
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def bot_setting_validator(self):
        if self.token is None:
            logger.info("🍀Kook Bot Token Not Set")
        return self

    @property
    def available(self):
        return self.token is not None


load_dotenv()
BotSetting = KookBot()
