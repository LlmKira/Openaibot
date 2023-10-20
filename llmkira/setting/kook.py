# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:59
# @Author  : sudoskys
# @File    : kook.py
# @Software: PyCharm
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseSettings, Field, validator, root_validator


class KookBot(BaseSettings):
    """
    代理设置
    """
    token: str = Field(None, env='KOOK_BOT_TOKEN')

    # proxy_address: str = Field(None, env="DISCORD_BOT_PROXY_ADDRESS")  # "all://127.0.0.1:7890"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @validator('token')
    def proxy_address_validator(cls, v):
        if v is None:
            logger.warning(f"KookBot token is empty")
        else:
            logger.success(f"KookBot token ready")
        return v

    @root_validator
    def bot_setting_validator(cls, values):
        return values

    @property
    def available(self):
        return self.token is not None


load_dotenv()
BotSetting = KookBot()
