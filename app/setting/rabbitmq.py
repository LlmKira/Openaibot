# -*- coding: utf-8 -*-
# @Time    : 2023/11/14 上午11:39
# @Author  : sudoskys
# @File    : rabbitmq.py
# @Software: PyCharm
from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from llmkira.sdk.utils import sync


class RabbitMQ(BaseSettings):
    """
    代理设置
    """

    amqp_dsn: str = Field(
        "amqp://admin:8a8a8a@localhost:5672", validation_alias="AMQP_DSN"
    )
    _verify_status: bool = PrivateAttr(default=False)
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def is_connect(self):
        import aio_pika

        try:
            sync(aio_pika.connect_robust(self.amqp_dsn))
        except Exception as e:
            self._verify_status = False
            logger.exception(
                f"\n⚠️ RabbitMQ DISCONNECT, pls set AMQP_DSN in .env\n--error {e} \n--dsn {self.amqp_dsn}"
            )
            raise e
        else:
            self._verify_status = True
            logger.success("🍩 RabbitMQ Connect Success")
            if self.amqp_dsn == "amqp://admin:8a8a8a@localhost:5672":
                logger.warning(
                    "\n⚠️ You Are Using The Default RabbitMQ Password"
                    "\nMake Sure You Handle The Port `5672` And Set Firewall Rules"
                )
        return self

    @property
    def available(self):
        return self._verify_status

    @property
    def task_server(self):
        return self.amqp_dsn


load_dotenv()
RabbitMQSetting = RabbitMQ()
