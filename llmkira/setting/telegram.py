# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:22
# @Author  : sudoskys
# @File    : telegram.py
# @Software: PyCharm
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseSettings, Field, root_validator


class TelegramBot(BaseSettings):
    """
    代理设置
    """
    token: str = Field(None, env='TELEGRAM_BOT_TOKEN')
    proxy_address: str = Field(None, env="TELEGRAM_BOT_PROXY_ADDRESS")  # "all://127.0.0.1:7890"
    bot_link: str = Field(None, env='TELEGRAM_BOT_LINK')
    bot_id: str = Field(None, env="TELEGRAM_BOT_ID")
    bot_username: str = Field(None, env="TELEGRAM_BOT_USERNAME")

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @root_validator
    def bot_validator(cls, values):
        if values['proxy_address']:
            logger.success(f"TelegramBot proxy was set to {values['proxy_address']}")
        if values.get('bot_id') is None:
            try:
                from telebot import TeleBot
                # 创建 Bot
                if values['proxy_address'] is not None:
                    from telebot import apihelper
                    if "socks5://" in values['proxy_address']:
                        values['proxy_address'] = values['proxy_address'].replace("socks5://", "socks5h://")
                    apihelper.proxy = {'https': values['proxy_address']}
                _bot = TeleBot(token=values.get('token')).get_me()
                values['bot_id'] = _bot.id
                values['bot_username'] = _bot.username
                values['bot_link'] = f"https://t.me/{values['bot_username']}"
            except Exception as e:
                logger.warning(f"Telegrambot token is empty:{e}")
            else:
                logger.success(f"TelegramBot connect success: {values.get('bot_username')}")
        return values

    @property
    def available(self):
        return self.token is not None


load_dotenv()
BotSetting = TelegramBot()
