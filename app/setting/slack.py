# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午2:14
# @Author  : sudoskys
# @File    : slack.py
# @Software: PyCharm
from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SlackBot(BaseSettings):
    """
    代理设置
    """

    app_token: Optional[str] = Field(None, validation_alias="SLACK_APP_TOKEN")
    # https://api.slack.com/apps

    bot_token: Optional[str] = Field(None, validation_alias="SLACK_BOT_TOKEN")
    # https://api.slack.com/apps/XXXX/oauth?

    secret: Optional[str] = Field(None, validation_alias="SLACK_SIGNING_SECRET")
    # https://api.slack.com/authentication/verifying-requests-from-slack#signing_secrets_admin_page

    proxy_address: Optional[str] = Field(
        None, validation_alias="SLACK_BOT_PROXY_ADDRESS"
    )  # "all://127.0.0.1:7890"
    bot_id: Optional[str] = Field(None)
    bot_username: Optional[str] = Field(None)
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def bot_setting_validator(self):
        try:
            if self.app_token is None:
                raise ValueError("🍀SlackBot `app_token` Not Set")
            if self.bot_token is None:
                raise LookupError("\n🍀SlackBot `bot_token` is empty")
            if self.secret is None:
                raise LookupError("\n🍀SlackBot `secret` is empty")
        except ValueError as e:
            logger.info(str(e))
        except LookupError as e:
            logger.warning(str(e))
        return self

    @property
    def available(self):
        return all([self.app_token, self.bot_token, self.secret])


load_dotenv()
BotSetting = SlackBot()
