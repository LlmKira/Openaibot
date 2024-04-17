# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 下午10:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import atexit
from typing import List

import hikari
from hikari.impl import ProxySettings
from loguru import logger

from app.middleware.llm_task import OpenaiMiddleware
from app.receiver import function
from app.receiver.receiver_client import BaseReceiver, BaseSender
from app.setting.discord import BotSetting
from llmkira.kv_manager.file import File
from llmkira.openai import OpenAIResult
from llmkira.openai.cell import Message
from llmkira.sdk.utils import sync
from llmkira.task import Task, TaskHeader

__receiver__ = "discord_hikari"

from llmkira.task.schema import Location, EventMessage

discord_rest: hikari.RESTApp = hikari.RESTApp(
    proxy_settings=ProxySettings(url=BotSetting.proxy_address)
)


class DiscordSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        self.bot = None

    def acquire(self):
        self.bot: hikari.impl.RESTClientImpl = discord_rest.acquire(
            token=BotSetting.token, token_type=hikari.TokenType.BOT
        )

    async def file_forward(self, receiver: Location, file_list: List[File]):
        for file_obj in file_list:
            # DATA
            file_data: bytes = await file_obj.download_file()
            if not file_data:
                logger.error(f"file not found {receiver.user_id}")
                continue
            file_warp = hikari.files.Bytes(file_data, file_obj.file_name, mimetype=None)
            if file_obj.file_name.endswith((".jpg", ".png")):
                async with self.bot as client:
                    client: hikari.impl.RESTClientImpl
                    _reply = None
                    if receiver.thread_id != receiver.chat_id:
                        _reply = await client.fetch_message(
                            channel=int(receiver.thread_id),
                            message=int(receiver.message_id),
                        )
                    await client.create_message(
                        channel=int(receiver.thread_id),
                        embed=hikari.EmbedImage(
                            resource=file_warp,
                        ),
                        reply=_reply,
                    )
            else:
                async with self.bot as client:
                    client: hikari.impl.RESTClientImpl
                    _reply = None
                    if receiver.thread_id != receiver.chat_id:
                        _reply = await client.fetch_message(
                            channel=int(receiver.thread_id),
                            message=int(receiver.message_id),
                        )
                    await client.create_message(
                        channel=int(receiver.thread_id),
                        attachment=file_warp,
                        reply=_reply,
                    )

    async def forward(self, receiver: Location, message: List[EventMessage]):
        """
        插件专用转发，是Task通用类型
        """
        for item in message:
            await self.file_forward(receiver=receiver, file_list=item.files)
            async with self.bot as client:
                client: hikari.impl.RESTClientImpl
                _reply = None
                if receiver.thread_id != receiver.chat_id:
                    _reply = await client.fetch_message(
                        channel=int(receiver.thread_id),
                        message=int(receiver.message_id)
                        if receiver.message_id
                        else None,
                    )
                await client.create_message(
                    channel=int(receiver.thread_id) if receiver.thread_id else None,
                    content=item.text,
                    reply=_reply,
                )

    async def reply(
        self, receiver: Location, messages: List[Message], reply_to_message: bool = True
    ):
        """
        模型直转发，Message是Openai的类型
        """
        event_message = [
            EventMessage.from_openai_message(message=item, locate=receiver)
            for item in messages
        ]
        # 转析器
        _, event_message, receiver = await self.hook(
            platform_name=__receiver__, messages=event_message, locate=receiver
        )
        event_message: list
        for event in event_message:
            await self.file_forward(receiver=receiver, file_list=event.files)
            if not event.text:
                continue
            async with self.bot as client:
                client: hikari.impl.RESTClientImpl
                _reply = None
                if receiver.thread_id != receiver.chat_id:
                    _reply = await client.fetch_message(
                        channel=int(receiver.thread_id),
                        message=int(receiver.message_id)
                        if receiver.message_id
                        else None,
                    )
                await client.create_message(
                    channel=int(receiver.thread_id),
                    content=event.text,
                    reply=_reply,
                )
        return logger.trace("reply message")

    async def error(self, receiver: Location, text):
        async with self.bot as client:
            client: hikari.impl.RESTClientImpl
            _reply = None
            if receiver.thread_id != receiver.chat_id:
                _reply = await client.fetch_message(
                    channel=int(receiver.thread_id),
                    message=int(receiver.message_id) if receiver.message_id else None,
                )
            await client.create_message(
                channel=int(receiver.thread_id), content=text, reply=_reply
            )

    async def function(
        self,
        receiver: Location,
        task: TaskHeader,
        llm: OpenaiMiddleware,
        llm_result: OpenAIResult,
    ):
        tool_calls = llm_result.default_message.tool_calls
        certify_needed_map = await self.push_task_create_message(
            llm_result=llm_result, receiver=receiver, tool_calls=tool_calls
        )
        new_receiver = task.receiver.model_copy()
        new_receiver.platform = __receiver__
        """更新接收者为当前平台，便于创建的函数消息能返回到正确的客户端"""

        new_sign = task.task_sign.update_tool_calls(
            tool_calls=tool_calls,
            certify_needed_map=certify_needed_map,
        )
        """克隆元数据为当前平台"""

        logger.debug(
            f"Sender.function:Create a new task {function.__receiver__} to {new_receiver} // {new_sign}"
        )
        await Task.create_and_send(
            queue_name=function.__receiver__,
            task=TaskHeader.from_function(
                llm_response=llm_result,
                task_sign=new_sign,
                receiver=new_receiver,
                message=task.message,
            ),
        )
        """发送到函数处理接收器"""


__sender__ = DiscordSender()


class DiscordReceiver(BaseReceiver):
    """
    receive message from telegram
    """

    async def discord(self):
        self.set_core(sender=__sender__, task=Task(queue=__receiver__))
        if not BotSetting.available:
            logger.warning("Receiver Runtime:Discord Setting empty")
            return None
        await discord_rest.start()
        __sender__.acquire()
        try:
            logger.success("Receiver Runtime:Discord start")
            await self.task.consuming_task(self.on_message)
        except KeyboardInterrupt:
            logger.warning("Discord Receiver shutdown")
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            await discord_rest.close()


if BotSetting.available:

    @atexit.register
    def __clean():
        try:
            sync(discord_rest.close())
        except Exception as e:
            logger.warning(f"Discord Receiver cleaning failed when exiting \n{e}")
