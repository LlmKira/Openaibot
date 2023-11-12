# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import time
from typing import List

import telebot
from loguru import logger
from telebot import TeleBot

from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.receiver import function
from llmkira.receiver.receiver_client import BaseReceiver, BaseSender
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.schema import Message, File
from llmkira.setting.telegram import BotSetting
from llmkira.task import Task, TaskHeader

__receiver__ = "telegram"

from llmkira.middleware.router.schema import router_set

router_set(role="receiver", name=__receiver__)


class TelegramSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        if not BotSetting.available:
            return
        self.bot = TeleBot(token=BotSetting.token)
        from telebot import apihelper
        if BotSetting.proxy_address:
            apihelper.proxy = {'https': BotSetting.proxy_address}
        else:
            apihelper.proxy = None

    async def file_forward(self, receiver: TaskHeader.Location, file_list: List[File]):
        for file_obj in file_list:
            if file_obj.file_url:
                self.bot.send_document(chat_id=receiver.chat_id, document=file_obj.file_url,
                                       reply_to_message_id=receiver.message_id, caption=file_obj.file_name)
                continue
            _data: File.Data = await file_obj.raw_file()
            if not _data:
                logger.error(f"file download failed {file_obj.file_id}")
                continue
            if file_obj.file_name.endswith((".jpg", ".png", ".jpeg", ".gif")):
                self.bot.send_photo(
                    chat_id=receiver.chat_id,
                    photo=_data.pair,
                    reply_to_message_id=receiver.message_id,
                    caption=file_obj.caption
                )
            elif file_obj.file_name.endswith(".webp"):
                self.bot.send_sticker(
                    chat_id=receiver.chat_id,
                    reply_to_message_id=receiver.message_id,
                    sticker=_data.pair,
                )
            elif file_obj.file_name.endswith(".ogg"):
                self.bot.send_voice(
                    chat_id=receiver.chat_id,
                    voice=_data.pair,
                    reply_to_message_id=receiver.message_id,
                    caption=file_obj.caption
                )
            else:
                self.bot.send_document(
                    chat_id=receiver.chat_id,
                    document=_data.pair,
                    reply_to_message_id=receiver.message_id,
                    caption=file_obj.caption
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
            try:
                self.bot.send_message(
                    chat_id=receiver.chat_id,
                    text=item.text,
                    reply_to_message_id=receiver.message_id,
                    parse_mode="MarkdownV2"
                )
                # TODO Telegram format
            except telebot.apihelper.ApiTelegramException as e:
                time.sleep(1)
                logger.error(f"telegram send message error, retry\n{e}")
                self.bot.send_message(
                    chat_id=receiver.chat_id,
                    text=item.text,
                    reply_to_message_id=receiver.message_id
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
            self.bot.send_message(
                chat_id=receiver.chat_id,
                text=raw_message.text,
                reply_to_message_id=receiver.message_id if reply_to_message else None,
            )
        return logger.trace(f"reply message")

    async def error(self, receiver: TaskHeader.Location, text):
        self.bot.send_message(
            chat_id=receiver.chat_id,
            text=text,
            reply_to_message_id=receiver.message_id
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
