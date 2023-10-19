# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
import asyncio
# ATTENTION:禁止调用上层任何包，否则会导致循环引用
from typing import Literal, Optional, Coroutine, List

from loguru import logger
from pydantic import BaseModel, root_validator, Field

from .error import ValidationError


def _sync(coroutine: Coroutine):
    """
    https://nemo2011.github.io/bilibili-api/#/sync-executor
    """
    try:
        asyncio.get_event_loop()
    except Exception as e:
        asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


class Function(BaseModel):
    """
    函数定义体。
    供外部模组定义并注册函数
    """

    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}

    name: str = Field(None, description="函数名称", regex=r"^[a-zA-Z0-9_]+$")
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")
    required: List[str] = []

    def add_property(self, property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.required.append(property_name)

    def parse_schema_to_properties(self, schema: BaseModel):
        """
        解析pydantic的schema
        传入一个pydantic的schema，解析成properties
        参数可以被数据模型所定义
        """
        self.parameters.properties = schema.schema()["properties"]


class File(BaseModel):
    class Data(BaseModel):
        file_name: str
        file_data: bytes = Field(None, description="文件数据")

        @property
        def pair(self):
            return self.file_name, self.file_data

    file_id: str = Field(None, description="文件ID")
    file_name: str = Field(None, description="文件名")
    file_url: str = Field(None, description="文件URL")
    caption: str = Field(default='', description="文件注释")

    # hash able
    def __eq__(self, other):
        if isinstance(other, File):
            return (self.file_id == other.file_id) and (self.file_name == other.file_name)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.file_id) + hash(self.file_name)

    @property
    def file_prompt(self):
        """
        FOR LLM
        """
        _comment = '('
        for key, value in self.dict().items():
            if value:
                _comment += f"{key}={value},"
        return f"[ReadableFile{_comment[:-1]})]"


class Message(BaseModel):
    """
    标准 API 件
    """

    class FunctionCall(BaseModel):
        name: str
        arguments: str

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: Optional[str] = None
    # speaker
    name: Optional[str] = Field(None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    # AI generated function call
    function_call: Optional[FunctionCall] = None

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        if not values.get("content") and not values.get("function_call"):
            raise ValidationError("sdk param validator:content or function_call must be specified")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}

    @property
    def message(self):
        return self

    @classmethod
    def create_short_task(cls, task_desc, refer, role: str = None):
        """
        生成task
        """
        if not role:
            role = "[RULE]Please complete the order according to the task description refer to given information, if can't complete, please reply 'give up'"
        return [
            Message(
                role="system",
                content=role,
            ),
            Message(
                role="user",
                content=f"{refer} <hint>{task_desc}<hint>",
                name="task"
            )
        ]

    @classmethod
    def create_task_message_list(cls, task_desc, refer, role: str = None):
        """
        生成task
        """
        if not role:
            role = "[Scene: chatting in real time]\nPlease complete the order according to the task description refer to given information"
        return [
            Message(
                role="system",
                content=role,
            ),
            Message(
                role="assistant",
                content=refer,
                name="information"
            ),
            Message(
                role="user",
                content=task_desc,
                name="task"
            ),
            Message(
                role="assistant",
                content="ok , i will complete the tasks you give",
            )
        ]


class TextMessage(Message):
    """
    存储类型：普通文本消息
    """

    class FunctionCall(BaseModel):
        name: str
        arguments: str

    message_type = "message"

    ##

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: Optional[str] = None
    # speaker
    name: Optional[str] = Field(None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    # AI generated function call
    function_call: Optional[FunctionCall] = None

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        if not values.get("content") and not values.get("function_call"):
            raise ValidationError("sdk param validator:content or function_call must be specified")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}

    @property
    def message(self) -> Message:
        return Message(
            role=self.role,
            name=self.name,
            content=self.content,
            function_call=self.function_call
        )


class FileMessage(Message):
    """
    多媒体消息

    :param role: 角色
    :param metadata: 元数据

    """
    message_type = "file_message"
    # 参数固定
    role: Literal["system", "assistant", "user", "function"] = "user"
    name: Optional[str] = Field("action", description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    content: str = Field(None, description="内容")

    file: File = Field(None, description="文件")
    caption: str = Field("", description="注释")
    metadata: Optional[dict] = None

    @root_validator
    def check(cls, values):
        if not values.get("file"):
            raise ValidationError("sdk param validator:file must be specified")
        return values

    @property
    def message(self) -> Message:
        assert hasattr(self.file, "file_name"), "obj not ok"
        content = f"(Operable File)[{self.file.file_name}]/{self.caption[:20]}.../"
        # 最终向API发送的消息
        return Message(
            role=self.role,
            name=self.name,
            content=content,
            function_call=None
        )


def standardise(message: Message):
    if not isinstance(message, Message):
        raise TypeError(f"message must be Message, not {type(message)}")
    if hasattr(message, "message"):
        return message.message
    else:
        return message


def parse_message_dict(item: dict):
    message_type = item.get("message_type", None)
    if message_type == "message":
        _message = TextMessage.parse_obj(item)
    elif message_type == "file_message":
        _message = FileMessage.parse_obj(item)
    else:
        try:
            _message = Message.parse_obj(item)
        except Exception as e:
            logger.error(f"parse_message_dict:Unknown message type in redis data {e}")
            # raise ValueError(f"Unknown message type in redis data {message_type}")
        else:
            return _message
