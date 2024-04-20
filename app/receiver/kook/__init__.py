# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:53
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

from khl import HTTPRequester, Cert, api, MessageTypes
from loguru import logger

from app.middleware.llm_task import OpenaiMiddleware
from app.receiver import function
from app.receiver.receiver_client import BaseReceiver, BaseSender
from app.setting.kook import BotSetting
from llmkira.kv_manager.file import File
from llmkira.openai import OpenAIResult
from llmkira.openai.cell import Message
from llmkira.task import Task, TaskHeader

__receiver__ = "kook"

from llmkira.task.schema import Location, EventMessage


# import nest_asyncio
# nest_asyncio.apply()


class KookSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        if not BotSetting.available:
            return
        self.bot = HTTPRequester(cert=Cert(token=BotSetting.token), ratelimiter=None)

    async def create_asset(self, file) -> str:
        return (await self.bot.exec_req(api.Asset.create(file=file)))["url"]

    async def send_message(
        self,
        channel_id: str,
        user_id: str,
        dm: bool,
        message_type: MessageTypes,
        content: str,
        ephemeral: bool = False,
        reply_message_id: str = None,
    ):
        try:
            if dm:
                message = api.DirectMessage.create(
                    target_id=user_id,
                    type=message_type,
                    content=content,
                    quote=reply_message_id,
                )
            else:
                message = api.Message.create(
                    target_id=channel_id,
                    type=message_type,
                    content=content,
                    quote=reply_message_id,
                    temp_target_id=user_id if ephemeral else None,
                )
            _msg = await self.bot.exec_req(message)
        except Exception as e:
            raise ValueError(f"Kook msg send failed,{e}")
        return _msg

    async def file_forward(self, receiver: Location, file_list: List[File]):
        for file_obj in file_list:
            file_data: bytes = await file_obj.download_file()
            if not file_data:
                logger.error(f"File {receiver.user_id} not found")
                continue
            if file_obj.file_name.endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")):
                await self.send_message(
                    channel_id=receiver.thread_id,
                    user_id=receiver.user_id,
                    dm=receiver.thread_id == receiver.chat_id,
                    message_type=MessageTypes.IMG,
                    content=await self.create_asset(
                        file=(file_data, file_obj.file_name)
                    ),
                )
            else:
                await self.send_message(
                    channel_id=receiver.thread_id,
                    user_id=receiver.user_id,
                    dm=receiver.thread_id == receiver.chat_id,
                    message_type=MessageTypes.FILE,
                    content=await self.create_asset(
                        file=(file_data, file_obj.file_name)
                    ),
                )

    async def forward(self, receiver: Location, message: List[EventMessage]):
        """
        插件专用转发，是Task通用类型
        """
        for item in message:
            await self.file_forward(receiver=receiver, file_list=item.files)
            await self.send_message(
                channel_id=receiver.thread_id,
                user_id=receiver.user_id,
                dm=receiver.thread_id == receiver.chat_id,
                message_type=MessageTypes.KMD,
                content=item.text,
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
            await self.send_message(
                channel_id=receiver.thread_id,
                user_id=receiver.user_id,
                dm=receiver.thread_id == receiver.chat_id,
                message_type=MessageTypes.KMD,
                content=event.text,
            )
        return logger.trace("reply message")

    async def error(self, receiver: Location, text):
        await self.send_message(
            channel_id=receiver.thread_id,
            user_id=receiver.user_id,
            dm=receiver.thread_id == receiver.chat_id,
            message_type=MessageTypes.TEXT,
            content=text,
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


__sender__ = KookSender()


class KookReceiver(BaseReceiver):
    """
    receive message from telegram
    """

    async def kook(self):
        self.set_core(sender=__sender__, task=Task(queue=__receiver__))
        if not BotSetting.available:
            logger.warning("Receiver Runtime:Kook Setting empty")
            return None
        try:
            logger.success("Receiver Runtime:Kook start")
            await self.task.consuming_task(self.on_message)
        except KeyboardInterrupt:
            logger.warning("Kook Receiver shutdown")
        except Exception as e:
            logger.exception(e)
            raise e
