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

from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.receiver import function
from llmkira.receiver.receiver_client import BaseReceiver, BaseSender
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.schema import File, Message
from llmkira.sdk.utils import sync
from llmkira.setting.discord import BotSetting
from llmkira.task import Task, TaskHeader

__receiver__ = "discord_hikari"

from llmkira.middleware.router.schema import router_set

router_set(role="receiver", name=__receiver__)

discord_rest: hikari.RESTApp = hikari.RESTApp(
    proxy_settings=ProxySettings(
        url=BotSetting.proxy_address
    )
)


class DiscordSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        self.bot = None

    def acquire(self):
        self.bot: hikari.impl.RESTClientImpl = discord_rest.acquire(
            token=BotSetting.token,
            token_type=hikari.TokenType.BOT
        )

    async def file_forward(self, receiver: TaskHeader.Location, file_list: List[File]):
        for file_obj in file_list:
            # URL FIRST
            if file_obj.file_url:
                async with self.bot as client:
                    client: hikari.impl.RESTClientImpl
                    _reply = None
                    if receiver.thread_id != receiver.chat_id:
                        _reply = await client.fetch_message(
                            channel=receiver.thread_id,
                            message=receiver.message_id
                        )
                    await client.create_message(
                        channel=receiver.thread_id,
                        attachment=hikari.files.URL(file_obj.file_url, filename=file_obj.file_name),
                        reply=_reply,
                    )
                break
            # DATA
            _data: File.Data = sync(file_obj.raw_file())
            if not _data:
                logger.error(f"file download failed {file_obj.file_id}")
                continue
            file_warp = hikari.files.Bytes(_data.file_data, file_obj.file_name, mimetype="image/png")
            if file_obj.file_name.endswith((".jpg", ".png")):
                async with self.bot as client:
                    client: hikari.impl.RESTClientImpl
                    _reply = None
                    if receiver.thread_id != receiver.chat_id:
                        _reply = await client.fetch_message(
                            channel=receiver.thread_id,
                            message=receiver.message_id
                        )
                    await client.create_message(
                        channel=receiver.thread_id,
                        embed=hikari.EmbedImage(
                            resource=file_warp,
                        ),
                        reply=_reply
                    )
            else:
                async with self.bot as client:
                    client: hikari.impl.RESTClientImpl
                    _reply = None
                    if receiver.thread_id != receiver.chat_id:
                        _reply = await client.fetch_message(
                            channel=receiver.thread_id,
                            message=receiver.message_id
                        )
                    await client.create_message(
                        channel=receiver.thread_id,
                        attachment=file_warp,
                        reply=_reply
                    )

    async def forward(self, receiver: TaskHeader.Location, message: List[RawMessage]):
        """
        插件专用转发，是Task通用类型
        """
        for item in message:
            await self.file_forward(
                receiver=receiver,
                file_list=item.file
            )
            if item.only_send_file:
                continue
            async with self.bot as client:
                client: hikari.impl.RESTClientImpl
                _reply = None
                if receiver.thread_id != receiver.chat_id:
                    _reply = await client.fetch_message(
                        channel=receiver.thread_id,
                        message=receiver.message_id
                    )
                await client.create_message(
                    channel=receiver.thread_id,
                    content=item.text,
                    reply=_reply
                )

    async def reply(self, receiver: TaskHeader.Location, message: List[Message], reply_to_message: bool = True):
        """
        模型直转发，Message是Openai的类型
        """
        for item in message:
            raw_message = await self.loop_turn_from_openai(platform_name=__receiver__, message=item, locate=receiver)

            await self.file_forward(
                receiver=receiver,
                file_list=raw_message.file
            )
            if raw_message.only_send_file:
                continue
            if not raw_message.text:
                continue
            assert raw_message.text, f"message content is empty"
            async with self.bot as client:
                client: hikari.impl.RESTClientImpl
                _reply = None
                if receiver.thread_id != receiver.chat_id:
                    _reply = await client.fetch_message(
                        channel=receiver.thread_id,
                        message=receiver.message_id
                    )
                await client.create_message(
                    channel=receiver.thread_id,
                    content=raw_message.text,
                    reply=_reply
                )
        return logger.trace(f"reply message")

    async def error(self, receiver: TaskHeader.Location, text):
        async with self.bot as client:
            client: hikari.impl.RESTClientImpl
            _reply = None
            if receiver.thread_id != receiver.chat_id:
                _reply = await client.fetch_message(
                    channel=receiver.thread_id,
                    message=receiver.message_id
                )
            await client.create_message(
                channel=receiver.thread_id,
                content=text,
                reply=_reply
            )

    async def function(self,
                       receiver: TaskHeader.Location,
                       task: TaskHeader,
                       llm: OpenaiMiddleware,
                       llm_result: LlmResult
                       ):
        task_batch = llm_result.default_message.get_executor_batch()
        verify_map = await self.push_task_create_message(
            task=task,
            task_batch=task_batch,
            llm_result=llm_result,
            receiver=receiver
        )
        new_receiver = task.receiver.model_copy()
        new_receiver.platform = __receiver__
        """更新接收者为当前平台，便于创建的函数消息能返回到正确的客户端"""
        new_meta = task.task_meta.pack_loop(
            plan_chain_pending=task_batch,
            verify_map=verify_map
        )
        """克隆元数据为当前平台"""

        await Task(queue=function.__receiver__).send_task(
            task=TaskHeader.from_function(
                llm_result=llm_result,
                task_meta=new_meta,
                receiver=new_receiver,
                message=task.message
            )
        )
        """发送打包后的任务数据"""
        del new_meta
        del task
        """清理内存"""


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
