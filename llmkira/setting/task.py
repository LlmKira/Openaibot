# -*- coding: utf-8 -*-
# @Time    : 2023/10/14 下午3:10
# @Author  : sudoskys
# @File    : task.py
# @Software: PyCharm
from dotenv import load_dotenv
from llmkira.utils import sync
from loguru import logger
from pydantic import Field, BaseSettings, root_validator


class RabbitMQ(BaseSettings):
    """
    代理设置
    """
    amqp_dsn: str = Field("amqp://admin:admin@localhost:5672", env='AMQP_DSN')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @root_validator()
    def is_connect(cls, values):
        import aio_pika
        try:
            sync(aio_pika.connect_robust(
                values['amqp_dsn']
            ))
        except Exception as e:
            logger.error('RabbitMQ connect failed, pls set AMQP_DSN in .env')
            raise ValueError('RabbitMQ connect failed')
        else:
            logger.success(f"RabbitMQ connect success")
        return values


load_dotenv()
RabbitMQSetting = RabbitMQ()
