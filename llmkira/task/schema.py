# -*- coding: utf-8 -*-
# @Time    : 2023/10/14 下午2:16
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import copy
import time
from typing import Literal, Tuple, List, Union, Optional

from dotenv import load_dotenv
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.schema import File
from llmkira.utils import sync
from loguru import logger
from pydantic import BaseSettings, Field, BaseModel, root_validator
from telebot import types


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
        platform: str = Field(None, description="平台")
        chat_id: int = Field(None, description="群组ID")
        user_id: int = Field(None, description="用户ID")
        message_id: int = Field(None, description="消息ID")

    class Plugin(BaseModel):
        name: str = Field(None, description="插件名称")
        is_run_out: bool = Field(False, description="是否运行完毕")
        token_usage: int = Field(0, description="Token 用量")

    task_meta: Meta = Field(Meta(), description="任务元数据")
    sender: Location = Field(None, description="发信人")
    receiver: Location = Field(None, description="接收人")
    message: List[RawMessage] = Field(None, description="消息内容")

    @classmethod
    def from_telegram(cls, message: Union[types.Message],
                      task_meta: Meta,
                      file: List[File] = None,
                      reply: bool = True,
                      hide_file_info: bool = False,
                      trace_back_message: List[types.Message] = None
                      ):
        """
        从telegram消息中构建任务
        """

        if (trace_back_message is None) or (not all(trace_back_message)):
            trace_back_message = []
        if file is None:
            file = []

        def _convert(_message: types.Message) -> Optional[RawMessage]:
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
                text=text if text else f"(hi)",  # Empty Message
                created_at=created_at
            )

        _file_name = []
        if file:
            for _file in file:
                _file_name.append(_file.file_prompt)
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        head_message.file = file
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                message_list.append(_convert(item))
        message_list.append(head_message)
        message_list = [item for item in message_list if item]
        # 去掉 None
        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="telegram",
                chat_id=message.chat.id,
                user_id=message.from_user.id,
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
            message=[RawMessage(
                user_id=user_id,
                chat_id=user_id,
                text=message_text,
                created_at=int(time.time())
            )]
        )
