# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:53
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

from khl import HTTPRequester, Cert, api, MessageTypes
from loguru import logger

from llmkira.middleware.llm_task import OpenaiMiddleware
from llmkira.receiver import function
from llmkira.receiver.receiver_client import BaseReceiver, BaseSender
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.schema import File, Message
from llmkira.setting.kook import BotSetting
from llmkira.task import Task, TaskHeader

__receiver__ = "kook"

from llmkira.middleware.router.schema import router_set

# 魔法
import nest_asyncio

nest_asyncio.apply()
# 设置路由系统
router_set(role="receiver", name=__receiver__)


class KookSender(BaseSender):
    """
    平台路由
    """

    def __init__(self):
        if not BotSetting.available:
            return
        self.bot = HTTPRequester(cert=Cert(token=BotSetting.token))

    async def create_asset(self, file: File.Data) -> str:
        return (await self.bot.exec_req(api.Asset.create(file=file.pair)))['url']

    async def send_message(self,
                           channel_id: str,
                           user_id: str,
                           dm: bool,
                           message_type: MessageTypes,
                           content: str,
                           ephemeral: bool = False,
                           reply_message_id: str = None
                           ):
        try:
            if dm:
                message = api.DirectMessage.create(
                    target_id=user_id,
                    type=message_type,
                    content=content,
                    quote=reply_message_id
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

    async def file_forward(self, receiver: TaskHeader.Location, file_list: List[File]):
        for file_obj in file_list:
            # URL FIRST
            if file_obj.file_url:
                await self.send_message(
                    channel_id=receiver.thread_id,
                    user_id=receiver.user_id,
                    dm=receiver.thread_id == receiver.chat_id,
                    message_type=MessageTypes.FILE,
                    content=file_obj.file_url
                )
            # DATA
            _data: File.Data = await file_obj.raw_file()
            if not _data:
                logger.error(f"file download failed {file_obj.file_id}")
                continue
            if file_obj.file_name.endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")):
                await self.send_message(
                    channel_id=receiver.thread_id,
                    user_id=receiver.user_id,
                    dm=receiver.thread_id == receiver.chat_id,
                    message_type=MessageTypes.IMG,
                    content=await self.create_asset(file=_data)
                )
            else:
                await self.send_message(
                    channel_id=receiver.thread_id,
                    user_id=receiver.user_id,
                    dm=receiver.thread_id == receiver.chat_id,
                    message_type=MessageTypes.FILE,
                    content=await self.create_asset(file=_data)
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
            await self.send_message(
                channel_id=receiver.thread_id,
                user_id=receiver.user_id,
                dm=receiver.thread_id == receiver.chat_id,
                message_type=MessageTypes.KMD,
                content=item.text
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
            await self.send_message(
                channel_id=receiver.thread_id,
                user_id=receiver.user_id,
                dm=receiver.thread_id == receiver.chat_id,
                message_type=MessageTypes.KMD,
                content=raw_message.text
            )
        return logger.trace(f"reply message")

    async def error(self, receiver: TaskHeader.Location, text):
        await self.send_message(
            channel_id=receiver.thread_id,
            user_id=receiver.user_id,
            dm=receiver.thread_id == receiver.chat_id,
            message_type=MessageTypes.TEXT,
            content=text
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
