# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午6:25
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import ssl
from typing import List

from loguru import logger
from slack_sdk.web.async_client import AsyncWebClient

from app.middleware.llm_task import OpenaiMiddleware
from app.receiver import function
from app.receiver.receiver_client import BaseReceiver, BaseSender
from app.receiver.slack.creat_message import ChatMessageCreator
from app.setting.slack import BotSetting
from llmkira.kv_manager.file import File
from llmkira.openai import OpenAIResult
from llmkira.openai.cell import AssistantMessage
from llmkira.task import Task, TaskHeader

__receiver__ = "slack"

from llmkira.task.schema import Location, EventMessage


# import nest_asyncio
# nest_asyncio.apply()


class SlackSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        if not BotSetting.available:
            return
        ssl_cert = ssl.SSLContext()
        if BotSetting.proxy_address:
            self.proxy = BotSetting.proxy_address
            logger.info("SlackBot proxy_tunnels being used in `AsyncWebClient`!")
        self.bot = AsyncWebClient(
            token=BotSetting.bot_token, ssl=ssl_cert, proxy=BotSetting.proxy_address
        )

    async def file_forward(self, receiver: Location, file_list: List[File]):
        for file_obj in file_list:
            # DATA
            file_data: bytes = await file_obj.download_file()
            if not file_data:
                logger.error(f"file not found {receiver.user_id}")
                continue
            try:
                await self.bot.files_upload_v2(
                    file=file_data,
                    filename=file_obj.file_name,
                    channels=receiver.chat_id,
                    thread_ts=receiver.message_id,
                )
            except Exception as e:
                logger.error(e)
                logger.error(f"file upload failed {file_obj.file_name}")
                await self.bot.chat_postMessage(
                    channel=receiver.chat_id,
                    thread_ts=receiver.message_id,
                    text=str(
                        "Failed,Server down,or bot do not have *Bot Token Scopes* "
                        "of `files:write` scope to upload file."
                    ),
                )

    async def forward(self, receiver: Location, message: List[EventMessage]):
        """
        插件专用转发，是Task通用类型
        """
        for item in message:
            await self.file_forward(receiver=receiver, file_list=item.files)
            _message = (
                ChatMessageCreator(
                    channel=receiver.chat_id, thread_ts=receiver.message_id
                )
                .update_content(message_text=item.text)
                .get_message_payload(message_text=item.text)
            )
            await self.bot.chat_postMessage(**_message)

    async def reply(
        self,
        receiver: Location,
        messages: List[AssistantMessage],
        reply_to_message: bool = True,
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
            _message = (
                ChatMessageCreator(
                    channel=receiver.chat_id, thread_ts=receiver.message_id
                )
                .update_content(message_text=event.text)
                .get_message_payload(message_text=event.text)
            )
            await self.bot.chat_postMessage(
                channel=receiver.chat_id,
                thread_ts=receiver.message_id,
                text=event.text,
            )
        return logger.trace("reply message")

    async def error(self, receiver: Location, text):
        _message = (
            ChatMessageCreator(channel=receiver.chat_id, thread_ts=receiver.message_id)
            .update_content(message_text=text)
            .get_message_payload(message_text=text)
        )
        await self.bot.chat_postMessage(**_message)

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


__sender__ = SlackSender()


class SlackReceiver(BaseReceiver):
    """
    receive message from telegram
    """

    async def slack(self):
        self.set_core(sender=__sender__, task=Task(queue=__receiver__))
        if not BotSetting.available:
            logger.warning("Receiver Runtime:Slack Setting empty")
            return None
        try:
            logger.success("Receiver Runtime:Slack start")
            await self.task.consuming_task(self.on_message)
        except KeyboardInterrupt:
            logger.warning("Slack Receiver shutdown")
        except Exception as e:
            logger.exception(e)
            raise e
