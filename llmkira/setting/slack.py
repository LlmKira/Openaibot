# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午2:14
# @Author  : sudoskys
# @File    : slack.py
# @Software: PyCharm
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseSettings, Field, root_validator


class SlackBot(BaseSettings):
    """
    代理设置
    """
    app_token: str = Field(None, env='SLACK_APP_TOKEN')
    # https://api.slack.com/apps

    bot_token: str = Field(None, env='SLACK_BOT_TOKEN')
    # https://api.slack.com/apps/XXXX/oauth?

    secret: str = Field(None, env='SLACK_SIGNING_SECRET')
    # https://api.slack.com/authentication/verifying-requests-from-slack#signing_secrets_admin_page

    proxy_address: str = Field(None, env="SLACK_BOT_PROXY_ADDRESS")  # "all://127.0.0.1:7890"
    bot_id: str = Field(None)
    bot_username: str = Field(None)

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @root_validator
    def bot_setting_validator(cls, values):
        try:
            if values['app_token'] is None:
                raise ValueError("\n🍀Check:SlackBot app_token is empty")
            if values['bot_token'] is None:
                raise ValueError("\n🍀Check:SlackBot bot_token is empty")
            if values['secret'] is None:
                raise ValueError("\n🍀Check:SlackBot secret is empty")
        except Exception as e:
            logger.warning(e)
        else:
            logger.success(f"🍀Check:SlackBot token ready")
        return values

    @property
    def available(self):
        return all([self.app_token, self.bot_token, self.secret])


load_dotenv()
BotSetting = SlackBot()
