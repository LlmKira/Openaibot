# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import os
import ssl
import time
from typing import List

import telebot
from aio_pika.abc import AbstractIncomingMessage
from llmkira.middleware.chain_box import Chain, CHAIN_MANAGER
from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.receiver import function
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.error import RateLimitError
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.sdk.schema import Message, File
from llmkira.setting.telegram import BotSetting
from llmkira.task import Task, TaskHeader
from llmkira.utils import sync
from loguru import logger
from telebot import TeleBot, formatting

__receiver__ = "telegram"

from llmkira.middleware.router.schema import router_set

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
        """
        直接转发结果出来，不做任何处理
        """
        for item in message:
            for file_obj in item.file:
                if file_obj.file_url:
                    self.bot.send_document(chat_id=chat_id, document=file_obj.file_url,
                                           reply_to_message_id=reply_to_message_id, caption=file_obj.file_name)
                    continue
                _data: File.Data = sync(RawMessage.download_file(file_obj.file_id))

                if not _data:
                    logger.error(f"file download failed {file_obj.file_id}")
                    continue
                if file_obj.file_name.endswith(".jpg") or file_obj.file_name.endswith(".png"):
                    self.bot.send_photo(
                        chat_id=chat_id,
                        photo=_data.pair,
                        reply_to_message_id=reply_to_message_id,
                        caption=file_obj.file_name
                    )
                elif file_obj.file_name.endswith(".ogg"):
                    self.bot.send_voice(
                        chat_id=chat_id,
                        voice=_data.pair,
                        reply_to_message_id=reply_to_message_id,
                        caption=file_obj.file_name
                    )
                else:
                    self.bot.send_document(
                        chat_id=chat_id,
                        document=_data.pair, reply_to_message_id=reply_to_message_id,
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
            assert item.content, f"message content is empty"
            self.bot.send_message(
                chat_id=chat_id,
                text=item.content,
                reply_to_message_id=reply_to_message_id
            )

    def error(self, chat_id, reply_to_message_id, text):
        self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )

    async def function(self, chat_id, reply_to_message_id,
                       task: TaskHeader,
                       llm: OpenaiMiddleware,
                       result: openai.OpenaiResult,
                       message: Message):
        if not message.function_call:
            raise ValueError("message not have function_call,forward type error")

        # 获取设置查看是否静音
        _tool = ToolRegister().get_tool(message.function_call.name)
        if not _tool:
            logger.warning(f"not found function {message.function_call.name}")
            return None
        task_message = formatting.format_text(
            formatting.mbold("🦴 Task be created:") + f" `{message.function_call.name}` ",
            formatting.mcode(message.function_call.arguments),
            separator="\n"
        )
        if not _tool().silent:
            self.bot.send_message(
                chat_id=chat_id,
                text=task_message,
                reply_to_message_id=reply_to_message_id,
                parse_mode="MarkdownV2"
            )
        # 回写创建消息
        sign = f"<{task.task_meta.sign_as[0] + 1}>"
        # 二周目消息不回写，因为写过了
        llm.write_back(
            role="assistant",
            name=message.function_call.name,
            message_list=[
                RawMessage(
                    text=f"Okay,Task be created:{message.function_call.arguments}.")]
        )
        # 构建对应的消息
        receiver = task.receiver.copy()
        receiver.platform = __receiver__

        # 运行函数
        await Task(queue=function.__receiver__).send_task(
            task=TaskHeader.from_function(
                parent_call=result,
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
    async def llm_request(llm_agent: OpenaiMiddleware, disable_function: bool = False):
        """
        校验包装，没有其他作用
        """
        try:
            _result = await llm_agent.request_openai(disable_function=disable_function)
            _message = _result.default_message
            logger.debug(f"[x] LLM Message Sent \n--message {_message}")
            assert _message, "message is empty"
            return _result
        except ssl.SSLSyscallError as e:
            logger.error(f"Network ssl error: {e},that maybe caused by bad proxy")
            raise e
        except RateLimitError as e:
            logger.error(f"ApiEndPoint:{e}")
            raise ValueError(f"Authentication expiration, overload or other issues with the Api Endpoint")
        except Exception as e:
            logger.exception(e)
            raise e

    async def _flash(self,
                     task: TaskHeader,
                     llm: OpenaiMiddleware,
                     auto_write_back: bool = True,
                     intercept_function: bool = False,
                     disable_function: bool = False
                     ):
        """
        函数池刷新
        :param auto_write_back: 是否将task携带的消息回写进消息池中，如果为False则丢弃task携带消息
        :param intercept_function: 是否拦截函数调用转发到函数处理器
        """
        try:
            llm.build(auto_write_back=auto_write_back)
            try:
                result = await self.llm_request(llm, disable_function=disable_function)
            except Exception as e:
                __sender__.error(
                    chat_id=task.receiver.chat_id,
                    reply_to_message_id=task.receiver.message_id,
                    text=f"🦴 Sorry, your request failed because: {e}"
                )
                return
            if intercept_function:
                # 拦截函数调用
                if hasattr(result.default_message, "function_call"):
                    return await __sender__.function(
                        chat_id=task.receiver.chat_id,
                        reply_to_message_id=task.receiver.message_id,
                        task=task,
                        llm=llm,  # IMPORTANT
                        message=result.default_message,
                        result=result
                    )
            return __sender__.reply(
                chat_id=task.receiver.chat_id,
                reply_to_message_id=task.receiver.message_id,
                message=[result.default_message]
            )
        except Exception as e:
            raise e

    async def deal_message(self, message):
        """
        处理消息
        """
        # 解析数据
        _task: TaskHeader = TaskHeader.parse_raw(message.body)
        # 没有任何参数
        if _task.task_meta.direct_reply:
            __sender__.forward(
                chat_id=_task.receiver.chat_id,
                reply_to_message_id=_task.receiver.message_id,
                message=_task.message
            )
            return None, None, None
            # 函数重整策略
        functions = None
        if _task.task_meta.function_enable:
            # 继承函数
            functions = _task.task_meta.function_list
            if _task.task_meta.sign_as[0] == 0:
                # 复制救赎
                _task.task_meta.function_salvation_list = _task.task_meta.function_list
                functions = []

                # 重整
                for _index, _message in enumerate(_task.message):
                    functions.extend(
                        ToolRegister().filter_pair(
                            key_phrases=_message.text,
                        )
                    )
                _task.task_meta.function_list = functions
        if _task.task_meta.sign_as[0] == 0:
            # 容错一层旧节点
            functions.extend(_task.task_meta.function_salvation_list)
        # 构建通信代理
        _llm = OpenaiMiddleware(task=_task, function=functions)
        logger.debug(f"[x] Received Order \n--order {_task.json(indent=2)}")
        # 插件直接转发与重处理
        if _task.task_meta.callback_forward:
            # 手动追加插件产生的线索消息
            _llm.write_back(
                role=_task.task_meta.callback.role,
                name=_task.task_meta.callback.name,
                message_list=_task.message
            )
            # 插件数据响应到前端
            if _task.task_meta.callback_forward_reprocess:
                # 手动写回则禁用从 Task 数据体自动回写
                # 防止AI去启动其他函数，禁用函数
                await self._flash(
                    llm=_llm,
                    task=_task,
                    intercept_function=True,
                    disable_function=True,
                    auto_write_back=False
                )
                # 同时递交部署点
                return _task, _llm, "callback_forward_reprocess"
            # 转发函数
            __sender__.forward(
                chat_id=_task.receiver.chat_id,
                reply_to_message_id=_task.receiver.message_id,
                message=_task.message
            )
            # 同时递交部署点
            return _task, _llm, "callback_forward_reprocess"
        await self._flash(llm=_llm, task=_task, intercept_function=True)
        return None, None, None

    async def on_message(self, message: AbstractIncomingMessage):
        # 过期时间
        # print(message.expiration)
        try:
            if os.getenv("LLMBOT_STOP_REPLY") == "1":
                return None
            _task, _llm, _point = await self.deal_message(message)
            # 启动链式函数应答循环
            if _task:
                chain: Chain = await CHAIN_MANAGER.get_task(user_id=str(_task.receiver.user_id))
                if chain:
                    logger.info(f"Catch chain callback\n--callback_send_by {_point}")
                    await Task(queue=chain.address).send_task(task=chain.arg)
        except Exception as e:
            logger.exception(e)
            await message.reject(requeue=False)
        finally:
            await message.ack(multiple=False)

    async def telegram(self):
        if not BotSetting.available:
            logger.warning("Receiver Runtime:TelegramBot Setting not available")
            return None
        await self.task.consuming_task(self.on_message)
