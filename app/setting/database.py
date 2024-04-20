from dotenv import load_dotenv
from httpx import AsyncClient
from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from llmkira.sdk.utils import sync

global_httpx_client = AsyncClient(timeout=180)


class RabbitMQ(BaseSettings):
    """
    代理设置
    """

    amqp_dsn: str = Field(
        "amqp://admin:8a8a8a@localhost:5672", validation_alias="AMQP_DSN"
    )
    """RabbitMQ 配置"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def is_connect(self):
        from aio_pika import connect_robust

        try:
            sync(connect_robust(url=self.amqp_dsn))
        except Exception as e:
            logger.exception(
                f"\n⚠️ RabbitMQ DISCONNECT, pls set AMQP_DSN in .env\n--error {e} \n--dsn {self.amqp_dsn}"
            )
            raise e
        else:
            logger.success("🍩 RabbitMQ Connect Success")
            if self.amqp_dsn == "amqp://admin:8a8a8a@localhost:5672":
                logger.warning(
                    "\n⚠️ You Are Using The Default RabbitMQ Password"
                    "\nMake Sure You Handle The Port `5672` And Set Firewall Rules"
                )
        return self

    @property
    def task_server(self):
        return self.amqp_dsn


load_dotenv()
RabbitMQSetting = RabbitMQ()
