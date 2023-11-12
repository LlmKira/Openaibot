# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午6:25
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import ssl
from typing import List

from loguru import logger
from slack_sdk.web.async_client import AsyncWebClient

from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.receiver import function
from llmkira.receiver.receiver_client import BaseReceiver, BaseSender
from llmkira.receiver.slack.creat_message import ChatMessageCreator
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.schema import File, Message
from llmkira.setting.slack import BotSetting
from llmkira.task import Task, TaskHeader

__receiver__ = "slack"

from llmkira.middleware.router.schema import router_set

# 魔法
import nest_asyncio

nest_asyncio.apply()
# 设置路由系统
router_set(role="receiver", name=__receiver__)


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
            token=BotSetting.bot_token,
            ssl=ssl_cert,
            proxy=BotSetting.proxy_address
        )

    async def file_forward(self, receiver: TaskHeader.Location, file_list: List[File]):
        for file_obj in file_list:
            # URL FIRST
            if file_obj.file_url:
                await self.bot.files_upload_v2(
                    file=file_obj.file_url,
                    channels=receiver.chat_id,
                    thread_ts=receiver.message_id,
                    filename=file_obj.file_name,
                )
            # DATA
            _data: File.Data = await file_obj.raw_file()
            if not _data:
                logger.error(f"file download failed {file_obj.file_id}")
                continue
            try:
                await self.bot.files_upload_v2(
                    file=_data.file_data,
                    filename=_data.file_name,
                    channels=receiver.chat_id,
                    thread_ts=receiver.message_id,
                )
            except Exception as e:
                logger.error(e)
                logger.error(f"file upload failed {file_obj.file_id}")
                await self.bot.chat_postMessage(
                    channel=receiver.chat_id,
                    thread_ts=receiver.message_id,
                    text=str(f"Failed,Server down,or bot do not have *Bot Token Scopes* "
                             f"of `files:write` scope to upload file.")
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
            _message = ChatMessageCreator(
                channel=receiver.chat_id,
                thread_ts=receiver.message_id
            ).update_content(message_text=item.text).get_message_payload(message_text=item.text)
            await self.bot.chat_postMessage(
                **_message
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
            _message = ChatMessageCreator(
                channel=receiver.chat_id,
                thread_ts=receiver.message_id
            ).update_content(message_text=item.content).get_message_payload(message_text=item.content)
            await self.bot.chat_postMessage(
                channel=receiver.chat_id,
                thread_ts=receiver.message_id,
                text=raw_message.text
            )
        return logger.trace(f"reply message")

    async def error(self, receiver: TaskHeader.Location, text):
        _message = ChatMessageCreator(
            channel=receiver.chat_id,
            thread_ts=receiver.message_id
        ).update_content(message_text=text).get_message_payload(message_text=text)
        await self.bot.chat_postMessage(
            **_message
        )

    async def function(self,
                       receiver: TaskHeader.Location,
                       task: TaskHeader,
                       llm: OpenaiMiddleware,
                       llm_result: LlmResult,
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
