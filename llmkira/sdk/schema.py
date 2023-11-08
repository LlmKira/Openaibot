# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
import asyncio
import time
# ATTENTION:禁止调用上层任何schema包，否则会导致循环引用
from typing import Literal, Optional, Coroutine, List, Type

import shortuuid
from loguru import logger
from pydantic import BaseModel, root_validator, Field, validator

from .error import ValidationError


def generate_uid():
    return shortuuid.uuid()[0:8].upper()


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

    class FunctionExtra(BaseModel):
        system_prompt: str = Field(None, description="系统提示")

        @classmethod
        def default(cls):
            return cls(system_prompt=None)

    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}

    name: str = Field(None, description="函数名称", regex=r"^[a-zA-Z0-9_]+$")
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")
    required: List[str] = []
    # 附加信息
    config: FunctionExtra = Field(default_factory=FunctionExtra.default, description="函数配置")

    def request_final(self):
        """
        标准化
        """
        return self.copy(
            include={"name", "description", "parameters", "required"}
        )

    def add_property(self, property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        """
        加注属性
        """
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.required.append(property_name)

    def parse_schema_to_properties(self, schema: Type[BaseModel]):
        """
        解析 pydantic 的 schema
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
    uploader_uid: str = Field(default=None, description="上传者")
    bytes: int = Field(default=None)
    created_at: int = Field(default=int(time.time()))

    @classmethod
    def create_file(cls, **kwargs):
        # TODO
        return cls(**kwargs)

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

    def is_user_upload(self, uid: str):
        return self.uploader_uid == uid

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


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    """
    工具调用
    """
    id: str = Field(default=None)
    type: str = Field(default=None)
    function: FunctionCall = Field(default=None)


class Message(BaseModel):
    """
    标准 API 件
    """

    class Meta(BaseModel):
        index_id: str = Field(default_factory=generate_uid, description="消息ID")
        datatime: float = Field(default=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), description="消息时间")
        msg_type: str = Field(default="message", description="文档类型")
        extra: dict = Field(default_factory=dict, description="额外信息")

        @classmethod
        def default(cls):
            return cls(docs=False)

        @validator("msg_type")
        def check_msg_type(cls, v):
            if v not in ["message", "docs"]:
                raise ValueError("msg_type must be message/docs")
            return v

    meta: Optional[Meta] = Field(default_factory=Meta.default, description="元数据")

    function_call: Optional[FunctionCall] = Field(None, description="ai generated function_call")
    """Deprecated by openai"""
    tool_calls: Optional[List[ToolCall]] = Field(None, description="tool calls")
    """a array of ???"""

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: Optional[str] = None
    name: Optional[str] = Field(None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        if not values.get("content") and not values.get("function_call"):
            raise ValidationError("sdk param validator:content or function_call must be specified")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}

    def get_functions(self) -> List[FunctionCall]:
        """
        获取插件调用函数列表，合并新旧标准。
        """
        _calls = [self.function_call]
        _calls.extend([tools.function for tools in self.tool_calls])
        # 去None
        _calls = [_x for _x in _calls if _x]
        return _calls

    @property
    def sign_function(self) -> bool:
        """
        判断是否有函数需要执行
        """
        if self.function_call:
            return True
        if self.tool_calls:
            for tol in self.tool_calls:
                if tol.function:
                    return True
        return False

    @property
    def message(self) -> dict:
        """
        标准 Openai 消息 dict
        """
        return self.dict(
            include={"role", "content", "name", "function_call"}
        )

    @property
    def request_final(self) -> "Message":
        """
        Openai 请求标准格式
        """
        return self.copy(
            include={"role", "content", "name", "function_call"}
        )

    @property
    def fold(self) -> "Message":
        """
        折叠过长特殊类型消息。消息类型为程序自有属性。
        """
        metadata_str = (f"""[FoldDocs](query_id={self.meta.index_id}"""
                        f"""\ntimestamp={self.meta.datatime}"""
                        f"""\ndescription={self.content[:20] + "..."})"""
                        )
        return self.copy(
            update={
                "content": metadata_str
            },
            include={"role", "content", "name", "function_call"}
        )

    @classmethod
    def create_short_task(cls, task_desc, refer, role: str = None):
        """
        创建单任务模板
        """
        if not role:
            role = (
                "[RULE]"
                "Please complete the order according to the task description refer to given information, "
                "if can't complete, please reply 'give up'"
            )
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
    def create_task(cls, task_desc, refer, role: str = None):
        """
        创建任务模板
        """
        if not role:
            role = str(
                "[Scene: chatting in real time]\n"
                "Please complete the order according to the task description refer to given information"
            )
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


def standardise_for_request(message: Message):
    """
    标准化转换，供请求使用
    """
    if isinstance(message, dict):
        message = Message.parse_obj(message)
    if not isinstance(message, Message):
        raise TypeError(f"message must be Message, not {type(message)}")
    if hasattr(message, "message"):
        return message.request_final
    else:
        return message


def parse_message_dict(item: dict):
    """
    将 dict 实例化，用错误hook覆盖
    """
    try:
        _message = Message.parse_obj(item)
    except Exception as e:
        logger.exception(f"parse_message_dict:Unknown message type in redis data {e}")
    else:
        return _message
