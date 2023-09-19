# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import time
from typing import List

import telebot
from aio_pika.abc import AbstractIncomingMessage
from loguru import logger
from telebot import TeleBot

from middleware.llm_task import OpenaiMiddleware
from receiver import function
from schema import TaskHeader, RawMessage
from sdk.func_call import TOOL_MANAGER
from sdk.schema import Message
from sdk.utils import sync
from setting.telegram import BotSetting
from task import Task

__receiver__ = "telegram"

from middleware.router.schema import router_set

router_set(role="receiver", name=__receiver__)


class TelegramSender(object):
    """
    平台路由
    """

    def __init__(self):
        self.bot = TeleBot(token=BotSetting.token)
        from telebot import apihelper
        if BotSetting.proxy_address:
            apihelper.proxy = {'https': BotSetting.proxy_address}
        else:
            apihelper.proxy = None

    def forward(self, chat_id, reply_to_message_id, message: List[RawMessage]):
        for item in message:
            for file_obj in item.file:
                if file_obj.file_url:
                    self.bot.send_document(chat_id=chat_id, document=file_obj.file_url,
                                           reply_to_message_id=reply_to_message_id, caption=file_obj.file_name)
                    continue
                _data = sync(RawMessage.download_file(file_obj.file_id))
                if not _data:
                    logger.error(f"file download failed {file_obj.file_id}")
                    continue
                if file_obj.file_name.endswith(".jpg") or file_obj.file_name.endswith(".png"):
                    self.bot.send_photo(
                        chat_id=chat_id,
                        photo=(file_obj.file_name, _data),
                        reply_to_message_id=reply_to_message_id,
                        caption=file_obj.file_name
                    )
                elif file_obj.file_name.endswith(".ogg"):
                    self.bot.send_voice(
                        chat_id=chat_id,
                        voice=(file_obj.file_name, _data),
                        reply_to_message_id=reply_to_message_id,
                        caption=file_obj.file_name
                    )
                else:
                    self.bot.send_document(
                        chat_id=chat_id,
                        document=(file_obj.file_name, _data), reply_to_message_id=reply_to_message_id,
                        caption=file_obj.file_name
                    )
            try:
                self.bot.send_message(
                    chat_id=chat_id,
                    text=item.text,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode="MarkdownV2"
                )
            except telebot.apihelper.ApiTelegramException as e:
                time.sleep(3)
                logger.error("telegram send message error, retry")
                self.bot.send_message(
                    chat_id=chat_id,
                    text=item.text,
                    reply_to_message_id=reply_to_message_id
                )

    def reply(self, chat_id, reply_to_message_id, message: List[Message]):
        for item in message:
            self.bot.send_message(
                chat_id=chat_id,
                text=item.content,
                reply_to_message_id=reply_to_message_id
            )

    async def function(self, chat_id, reply_to_message_id, task: TaskHeader, message: Message):
        if not message.function_call:
            raise ValueError("message not have function_call,forward type error")

        # 获取设置查看是否静音
        _tool = TOOL_MANAGER.get_tool(message.function_call.name)
        if not _tool:
            logger.warning(f"not found function {message.function_call.name}")
            return None
        if not _tool().silent:
            self.bot.send_message(
                chat_id=chat_id,
                text=f"🦴 Task be created: {message.function_call.name}",
                reply_to_message_id=reply_to_message_id
            )

        # 构建对应的消息
        receiver = task.receiver.copy()
        receiver.platform = __receiver__

        # 运行函数
        await Task(queue=function.__receiver__).send_task(
            task=TaskHeader.from_function(
                parent_call=message,
                task_meta=task.task_meta,
                receiver=receiver,
                message=task.message
            )
        )


__sender__ = TelegramSender()


class TelegramReceiver(object):
    """
    receive message from telegram
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    @staticmethod
    async def llm_request(llm_agent: OpenaiMiddleware):
        try:
            _message = await llm_agent.func_message()
            print(f" [x] LLM Message {_message}")
            return _message
        except Exception as e:
            logger.exception(e)
            # return await message.ack()
            return None

    async def on_message(self, message: AbstractIncomingMessage):
        await message.ack()
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        _llm = OpenaiMiddleware(task=_task)
        print(" [x] Received Order %r" % _task)

        # 拦截注入内容
        if _task.task_meta.callback_forward:
            # 此函数回写了这里携带了的历史回调消息
            _llm.write_back(
                role=_task.task_meta.callback.role,
                name=_task.task_meta.callback.name,
                message_list=_task.message
            )
            if _task.task_meta.reprocess_needed:
                # 不回写任何原始消息
                _llm.build(write_back=False)
                _message = await self.llm_request(_llm)
                return __sender__.reply(
                    chat_id=_task.receiver.chat_id,
                    reply_to_message_id=_task.receiver.message_id,
                    message=[_message]
                )

            return __sender__.forward(
                chat_id=_task.receiver.chat_id,
                reply_to_message_id=_task.receiver.message_id,
                message=_task.message
            )

        _llm.build(write_back=True)  # 回写任何原始消息
        _message = await self.llm_request(_llm)

        # 拦截函数调用
        if hasattr(_message, "function_call"):
            await __sender__.function(
                chat_id=_task.receiver.chat_id,
                reply_to_message_id=_task.receiver.message_id,
                task=_task,
                message=_message
            )
            return

        # 正常调用
        __sender__.reply(
            chat_id=_task.receiver.chat_id,
            reply_to_message_id=_task.receiver.message_id,
            message=[_message]
        )
        return

    async def telegram(self):
        if not BotSetting.available:
            logger.warning("Receiver Runtime:TelegramBot Setting not available")
            return None
        await self.task.consuming_task(self.on_message)
