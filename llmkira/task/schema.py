# -*- coding: utf-8 -*-
# @Time    : 2023/10/14 下午2:16
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import copy
import time
from typing import Literal, Tuple, List, Union, Optional

import hikari
import khl
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseSettings, Field, BaseModel, root_validator
from telebot import types

from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.schema import File
from llmkira.utils import sync


class RabbitMQ(BaseSettings):
    """
    代理设置
    """
    amqp_dsn: str = Field("amqp://admin:admin@localhost:5672", env='AMQP_DSN')
    _verify_status: bool = Field(False, env='VERIFY_STATUS')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @root_validator()
    def is_connect(cls, values):
        import aio_pika
        try:
            sync(aio_pika.connect_robust(
                values['amqp_dsn']
            ))
        except Exception as e:
            values['_verify_status'] = False
            logger.warning(f'RabbitMQ DISCONNECT, pls set AMQP_DSN in .env\n--error {e}')
        else:
            values['_verify_status'] = True
            logger.success(f"RabbitMQ connect success")
        return values

    def check_connection(self, values):
        import aio_pika
        try:
            sync(aio_pika.connect_robust(
                self.amqp_dsn
            ))
        except Exception as e:
            logger.warning('RabbitMQ DISCONNECT, pls set AMQP_DSN in ENV')
            raise ValueError('RabbitMQ connect failed')
        else:
            logger.success(f"RabbitMQ connect success")
        return values

    @property
    def task_server(self):

        return self.amqp_dsn


load_dotenv()
RabbitMQSetting = RabbitMQ()


class TaskHeader(BaseModel):
    """
    任务链节点
    """

    class Meta(BaseModel):
        class Callback(BaseModel):
            role: Literal["user", "system", "function", "assistant"] = Field("user", description="角色")
            name: str = Field(None, description="功能名称", regex=r"^[a-zA-Z0-9_]+$")

        sign_as: Tuple[int, str, str] = Field((0, "root", "default"), description="签名")

        function_enable: bool = Field(False, description="功能开关")
        function_list: List[openai.Function] = Field([], description="功能列表")
        function_salvation_list: List[openai.Function] = Field([], description="上回合的功能列表，用于容错")

        direct_reply: bool = Field(False, description="直接回复,跳过函数处理等")
        callback_forward: bool = Field(False, description="非 LLM 转发")
        callback_forward_reprocess: bool = Field(False, description="追加LLM回复,追加存储处理后再回复")
        continue_step: int = Field(0, description="继续执行的步骤,发送启用 function call 的 continue")
        limit_child: int = Field(4, description="限制子节点数量")

        verify_uuid: str = Field(None, description="用于验证重发")
        parent_call: openai.OpenaiResult = Field(None, description="存储上一个节点的父消息，用于插件的原始消息信息存储")
        callback: Callback = Field(Callback(), description="用于回写，插件返回的消息头，标识 function 的名字")
        extra_args: dict = Field({}, description="用于提供额外参数")

        class Config:
            arbitrary_types_allowed = True

        def child(self, name):
            self.sign_as = (self.sign_as[0] + 1, "child", name)
            self.limit_child -= 1
            return copy.deepcopy(self)

    class Location(BaseModel):
        """
        Union[str, int]
        here .... address
        """
        platform: str = Field(None, description="platform")
        user_id: Union[str, int] = Field(None, description="user id")
        chat_id: Union[str, int] = Field(None, description="guild id(channel in dm)/Telegram chat id")
        thread_id: Union[str, int] = Field(None, description="channel id/Telegram thread")
        message_id: Union[str, int] = Field(None, description="message id")

        @root_validator()
        def to_string(cls, values):
            for key in values:
                if isinstance(values[key], int):
                    values[key] = str(values[key])
            return values

        @property
        def uid(self):
            return f"{self.platform}:{self.user_id}"

    class Plugin(BaseModel):
        name: str = Field(None, description="插件名称")
        is_run_out: bool = Field(False, description="是否运行完毕")
        token_usage: int = Field(0, description="Token 用量")

    task_meta: Meta = Field(Meta(), description="任务元数据")
    sender: Location = Field(..., description="发信人")
    receiver: Location = Field(..., description="接收人")
    message: List[RawMessage] = Field(None, description="消息内容")

    @classmethod
    def from_telegram(cls,
                      message: Union[types.Message],
                      task_meta: Meta,
                      file: List[File] = None,
                      reply: bool = True,
                      hide_file_info: bool = False,
                      deliver_back_message: List[types.Message] = None,
                      trace_back_message: List[types.Message] = None
                      ):
        """
        从telegram消息中构建任务
        """

        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: types.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, types.Message):
                user_id = _message.from_user.id
                chat_id = _message.chat.id
                text = _message.text if _message.text else _message.caption
                created_at = _message.date
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                text=text if text else f"(empty message)",
                created_at=created_at
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="telegram",
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                # dm=message.chat.type == "private",
                message_id=message.message_id if reply else None
            ),
            receiver=cls.Location(
                platform="telegram",
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                message_id=message.message_id if reply else None
            ),
            message=message_list
        )

    @classmethod
    def from_function(cls,
                      parent_call: openai.OpenaiResult,
                      task_meta: Meta,
                      receiver: Location,
                      message: List[RawMessage] = None
                      ):
        """
        从 Openai LLM Task中构建任务
        'function_call': {'name': 'set_alarm_reminder', 'arguments': '{\n  "delay": "5",\n  "content": "该吃饭了"\n}'}}
        """
        task_meta.parent_call = parent_call
        return cls(
            task_meta=task_meta,
            sender=receiver,
            receiver=receiver,
            message=message
        )

    @classmethod
    def from_router(cls, from_, to_, user_id, method, message_text):
        _meta_arg = {}
        if method == "task":
            _meta_arg["function_enable"] = True
        elif method == "push":
            _meta_arg["callback_forward"] = True
        elif method == "chat":
            _meta_arg["function_enable"] = False
        meta = cls.Meta(
            **_meta_arg
        )
        return cls(
            task_meta=meta,
            sender=cls.Location(
                platform=from_,
                chat_id=user_id,
                user_id=user_id,
                message_id=None
            ),
            receiver=cls.Location(
                platform=to_,
                chat_id=user_id,
                user_id=user_id,
                message_id=None
            ),
            message=[
                RawMessage(
                    user_id=user_id,
                    chat_id=user_id,
                    text=message_text,
                    created_at=int(time.time())
                )
            ]
        )

    @classmethod
    def from_discord_hikari(cls,
                            message: hikari.Message,
                            task_meta: Meta,
                            file: List[File] = None,
                            reply: bool = True,
                            hide_file_info: bool = False,
                            deliver_back_message: List[hikari.Message] = None,
                            trace_back_message: List[hikari.Message] = None
                            ):
        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: hikari.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, hikari.Message):
                user_id = message.author.id
                chat_id = message.guild_id if message.guild_id else message.channel_id
                thread_id = message.channel_id
                text = _message.content
                created_at = _message.created_at.timestamp()
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                text=text if text else f"(empty message)",
                created_at=created_at
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="discord_hikari",
                thread_id=message.channel_id,
                chat_id=message.guild_id if message.guild_id else message.channel_id,
                user_id=message.author.id,
                message_id=message.id if reply else None
            ),
            receiver=cls.Location(
                platform="discord_hikari",
                thread_id=message.channel_id,
                chat_id=message.guild_id if message.guild_id else message.channel_id,
                user_id=message.author.id,
                message_id=message.id if reply else None
            ),
            message=message_list
        )

    @classmethod
    def from_kook(cls,
                  message: khl.Message,
                  deliver_back_message: List[khl.Message],
                  task_meta: Meta,
                  trace_back_message: List[khl.Message],
                  hide_file_info: bool = False,
                  file: List[File] = None,
                  reply: bool = True,
                  ):
        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: khl.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, khl.Message):
                user_id = message.author_id
                chat_id = message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id
                thread_id = message.ctx.channel.id
                text = _message.content
                created_at = _message.msg_timestamp
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                text=text if text else f"(empty message)",
                created_at=created_at
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]
        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="kook",
                thread_id=message.ctx.channel.id,
                chat_id=message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id,
                user_id=message.author_id,
                message_id=message.id if reply else None
            ),
            receiver=cls.Location(
                platform="kook",
                thread_id=message.ctx.channel.id,
                chat_id=message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id,
                user_id=message.author_id,
                message_id=message.id if reply else None
            ),
            message=message_list
        )
