# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午9:54
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio

import aio_pika
from aio_pika import Message, DeliveryMode
from aiormq import DeliveryError
from loguru import logger
from pamqp.commands import Basic

from app.setting.database import RabbitMQSetting
from .schema import TaskHeader

EXPIRATION_SECOND = 60 * 5  # 5min
QUEUE_MAX_LENGTH = 120
X_OVERFLOW = "reject-publish"  # 拒绝
CONSUMER_PREFETCH_COUNT = 20  # 消息流控
QUEUE_ARGUMENTS = {
    "x-max-length": QUEUE_MAX_LENGTH,  # 上限
    # "message-ttl": EXPIRATION_SECOND * 1000,
    "x-overflow": X_OVERFLOW,  # 拒绝
}


class Task(object):
    def __init__(self, *, queue: str, amqp_dsn: str = None):
        """
        :param queue: The name of the queue started by the task
        :param amqp_dsn: Address of the RabbitMQ server
        """
        self.queue_name = queue
        if amqp_dsn is None:
            amqp_dsn = RabbitMQSetting.amqp_dsn
        self._amqp_url = amqp_dsn

    async def send_task(self, task: TaskHeader):
        connection = await aio_pika.connect_robust(self._amqp_url)
        async with connection:
            channel = await connection.channel(
                publisher_confirms=True  # 消息确认
            )
            # 通道超时 2s
            # await channel.initialize(timeout=2000)
            # Creating a message
            message = Message(
                body=task.model_dump_json().encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                expiration=EXPIRATION_SECOND,
            )
            # Declaring queue
            try:
                await channel.declare_queue(
                    self.queue_name,
                    arguments=QUEUE_ARGUMENTS,
                    durable=True,  # 持续化
                )
            except Exception as e:
                logger.error(
                    f"[5941163]Rabbitmq Queue param validation error, try deleting the abnormal "
                    f"queue manually and retrying. "
                    f"\n--error {e}"
                    f"\n--help |web: <database_ip>:15672/#/ |shell: `rabbitmqctl delete_queue {self.queue_name}`"
                )
                raise e
            # Sending the message
            try:
                confirmation = await channel.default_exchange.publish(
                    message, routing_key=self.queue_name, timeout=20
                )
            except DeliveryError as e:
                logger.error(
                    f"[502231] Task Delivery failed with exception: {e.reason}"
                )
                return (
                    False,
                    "🔭 Sorry,failure to reach the control centre, possibly i reach design limit 🧯",
                )
            except TimeoutError:
                logger.error("[528532] Task Delivery timeout")
                return False, "🔭 Sorry, failure to reach the control centre, ⏱ timeout"
            else:
                if not isinstance(confirmation, Basic.Ack):
                    logger.error("[552123]Task Delivery failed with confirmation")
                    return (
                        False,
                        "🔭 Sorry, failure to reach the control centre, sender error",
                    )
                else:
                    logger.info("[621132] Task sent success")
                    return True, "Task sent success"

    async def consuming_task(self, func: callable):
        connection = await aio_pika.connect_robust(self._amqp_url)
        async with connection:
            # Creating a channel
            channel = await connection.channel()
            # 通道超时 1s
            # await channel.initialize(timeout=1000)
            await channel.set_qos(prefetch_count=CONSUMER_PREFETCH_COUNT)  # 消息流控

            # Declaring queue
            try:
                queue = await channel.declare_queue(
                    self.queue_name,
                    arguments=QUEUE_ARGUMENTS,
                    durable=True,  # 持续化
                )
            except Exception as e:
                logger.error(
                    f"[502231]Rabbitmq Queue parameter validation failed, try deleting the abnormal queue manually "
                    f"and retrying."
                    f"\n--error {e}"
                    f"\n--help |web: <database_ip>:15672/#/ |shell: `rabbitmqctl delete_queue {self.queue_name}`"
                )
                raise e
            await queue.consume(func)
            await asyncio.Future()  # run forever

    @classmethod
    async def create_and_send(cls, *, queue_name: str, task: TaskHeader):
        sender = cls(queue=queue_name)
        await sender.send_task(task=task)
        return sender
