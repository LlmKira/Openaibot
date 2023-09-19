# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午9:54
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio

import aio_pika
from aio_pika import Message, DeliveryMode
from loguru import logger

from schema import TaskHeader
from setting.task import RabbitMQSetting


# 用于通知消息变换（GPT 中间件）


class Task(object):
    def __init__(self, queue: str):
        """
        :param queue: 队列名字
        """
        self.queue_name = queue
        self.amqp_url = RabbitMQSetting.amqp_dsn

    async def send_task(self, task: TaskHeader):
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            channel = await connection.channel()
            message = Message(
                task.json().encode("utf-8"), delivery_mode=DeliveryMode.PERSISTENT,
            )
            await channel.declare_queue(
                self.queue_name, durable=True,
            )
            # Sending the message
            await channel.default_exchange.publish(
                message, routing_key=self.queue_name,
            )
            logger.debug("生产者发送了任务：%r" % task.json())

    async def consuming_task(self, func: callable):
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            # Creating a channel
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)

            # Declaring queue
            queue = await channel.declare_queue(
                self.queue_name,
                durable=True,
            )
            await queue.consume(func)
            await asyncio.Future()  # run forever
