# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

import telebot
from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from telegramify_markdown import convert

from app.receiver import function
from app.receiver.receiver_client import BaseReceiver, BaseSender
from app.setting.telegram import BotSetting
from llmkira.kv_manager.file import File
from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.openai.cell import Message
from llmkira.openai.request import OpenAIResult
from llmkira.task import Task, TaskHeader

__receiver__ = "telegram"

from llmkira.task.schema import Location, EventMessage


class TelegramSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        if not BotSetting.available:
            return
        self.bot = AsyncTeleBot(token=BotSetting.token)
        from telebot import apihelper

        if BotSetting.proxy_address:
            apihelper.proxy = {"https": BotSetting.proxy_address}
        else:
            apihelper.proxy = None

    async def file_forward(self, receiver: Location, file_list: List[File]):
        for file_obj in file_list:
            file_data: bytes = await file_obj.download_file()
            if not file_data:
                logger.error(f"File {receiver.user_id} not found")
                continue
            file_downloaded = (file_obj.file_name, file_data)
            if file_obj.file_name.endswith((".jpg", ".png", ".jpeg", ".gif")):
                await self.bot.send_photo(
                    chat_id=receiver.chat_id,
                    photo=file_downloaded,
                    reply_to_message_id=receiver.message_id,
                    caption=file_obj.caption,
                )
            elif file_obj.file_name.endswith(".webp"):
                await self.bot.send_sticker(
                    chat_id=receiver.chat_id,
                    reply_to_message_id=receiver.message_id,
                    sticker=file_downloaded,
                )
            elif file_obj.file_name.endswith(".ogg"):
                try:
                    await self.bot.send_voice(
                        chat_id=receiver.chat_id,
                        voice=file_downloaded,
                        reply_to_message_id=receiver.message_id,
                        caption=file_obj.caption,
                    )
                except telebot.apihelper.ApiTelegramException as e:
                    if "VOICE_MESSAGES_FORBIDDEN" in str(e):
                        await self.bot.send_message(
                            chat_id=receiver.chat_id,
                            reply_to_message_id=receiver.message_id,
                            text="I can't send voice message because of your privacy settings.",
                        )
                    else:
                        raise e
            else:
                await self.bot.send_document(
                    chat_id=receiver.chat_id,
                    document=file_downloaded,
                    reply_to_message_id=receiver.message_id,
                    caption=file_obj.caption,
                )

    async def forward(
        self,
        receiver: Location,
        message: List[EventMessage],
    ):
        """
        转发消息
        :param receiver: 接收者
        :param message: 消息
        """
        for item in message:
            await self.file_forward(receiver=receiver, file_list=item.files)
            if isinstance(item.text, str) and len(item.text) == 0:
                continue
            await self.bot.send_message(
                chat_id=receiver.chat_id,
                text=convert(item.text),
                reply_to_message_id=receiver.message_id,
                parse_mode="MarkdownV2",
            )
        return logger.trace("forward message")

    async def reply(
        self,
        receiver: Location,
        messages: List[Message],
        reply_to_message: bool = True,
    ):
        """
        :param receiver: 接收者
        :param messages: OPENAI Format Message
        :param reply_to_message: 是否回复消息
        """
        for message in messages:
            event_message = EventMessage.from_openai_message(
                message=message, locate=receiver
            )
            await self.file_forward(receiver=receiver, file_list=event_message.files)
            if not event_message.text:
                continue
            try:
                await self.bot.send_message(
                    chat_id=receiver.chat_id,
                    text=convert(event_message.text),
                    reply_to_message_id=receiver.message_id
                    if reply_to_message
                    else None,
                    parse_mode="MarkdownV2",
                )
            except telebot.apihelper.ApiTelegramException as e:
                if "message to reply not found" in str(e):
                    await self.bot.send_message(
                        chat_id=receiver.chat_id, text=convert(event_message.text)
                    )
                else:
                    logger.error(f"User {receiver.user_id} send message error")
                    raise e
        return logger.trace("reply message")

    async def error(self, receiver: Location, text):
        await self.bot.send_message(
            chat_id=receiver.chat_id,
            text=convert(text),
            reply_to_message_id=receiver.message_id,
            parse_mode="MarkdownV2",
        )
        return logger.error("send error message")

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
        new_meta = task.task_sign.update_tool_calls(
            tool_calls=tool_calls,
            certify_needed_map=certify_needed_map,
        )
        """克隆元数据为当前平台"""

        await Task(queue=function.__receiver__).send_task(
            task=TaskHeader.from_function(
                llm_result=llm_result,
                task_meta=new_meta,
                receiver=new_receiver,
                message=task.message,
            )
        )
        """发送到函数处理接收器"""

        del new_meta
        del task
        """清理内存"""


__sender__ = TelegramSender()


class TelegramReceiver(BaseReceiver):
    """
    receive message from telegram
    """

    async def telegram(self):
        self.set_core(sender=__sender__, task=Task(queue=__receiver__))
        if not BotSetting.available:
            logger.warning("Receiver Runtime:TelegramBot Setting empty")
            return None
        logger.success("Receiver Runtime:TelegramBot start")
        await self.task.consuming_task(self.on_message)