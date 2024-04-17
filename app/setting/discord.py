# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 下午10:23
# @Author  : sudoskys
# @File    : discord.py
# @Software: PyCharm
from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DiscordBot(BaseSettings):
    """
    代理设置
    """

    token: Optional[str] = Field(
        None, validation_alias="DISCORD_BOT_TOKEN", strict=True
    )
    prefix: Optional[str] = Field("/", validation_alias="DISCORD_BOT_PREFIX")
    proxy_address: Optional[str] = Field(
        None, validation_alias="DISCORD_BOT_PROXY_ADDRESS"
    )  # "all://127.0.0.1:7890"
    bot_id: Optional[str] = Field(None)
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def bot_setting_validator(self):
        if self.token is None:
            logger.info("🍀Discord Bot Token Not Set")
        if self.proxy_address:
            logger.success(f"DiscordBot proxy was set to {self.proxy_address}")
        return self

    @property
    def available(self):
        return self.token is not None


load_dotenv()
BotSetting = DiscordBot()
