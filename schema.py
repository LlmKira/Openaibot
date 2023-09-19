# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import hashlib
import time
from io import BytesIO
from typing import Union, List, Any, Literal, Optional

from pydantic import Field, BaseModel, validator
from telebot import types

from cache.redis import cache


def generate_md5_short_id(data):
    # 检查输入数据是否是一个文件
    is_file = False
    if isinstance(data, str):
        is_file = True
    if isinstance(data, BytesIO):
        data = data.getvalue()
    # 计算 MD5 哈希值
    md5_hash = hashlib.md5()
    if is_file:
        with open(data, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
    else:
        md5_hash.update(data)
    # 获取哈希值的 16 进制表示
    hex_digest = md5_hash.hexdigest()
    # 生成唯一的短ID
    short_id = hex_digest[:8]
    return short_id


class File(BaseModel):
    file_id: str = Field(None, description="文件ID")
    file_name: str = Field(None, description="文件名")
    file_url: str = Field(None, description="文件URL")

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


class RawMessage(BaseModel):
    user_id: int = Field(None, description="用户ID")
    chat_id: int = Field(None, description="群组ID")
    text: str = Field(None, description="文本")
    file: List[File] = Field([], description="文件")
    created_at: int = Field(None, description="创建时间")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @validator("text")
    def check_text(cls, v):
        if v == "":
            v = "message is empty"
        if len(v) > 4096:
            v = v[:4090]
        return v

    @staticmethod
    async def download_file(file_id):
        return await cache.read_data(file_id)

    @staticmethod
    async def upload_file(name, data):
        _key = str(generate_md5_short_id(data))
        await cache.set_data(key=_key, value=data, timeout=60 * 60 * 24 * 7)
        return File(file_id=_key, file_name=name)

    @classmethod
    def from_telegram(cls, message: Union[types.Message, types.CallbackQuery]):
        if isinstance(message, types.Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text
            created_at = message.date
        elif isinstance(message, types.CallbackQuery):
            user_id = message.from_user.id
            chat_id = message.message.chat.id
            text = message.data
            created_at = message.message.date
        else:
            raise ValueError(f"Unknown message type {type(message)}")
        return cls(
            user_id=user_id,
            text=text,
            chat_id=chat_id,
            created_at=created_at
        )


class TaskHeader(BaseModel):
    class Meta(BaseModel):
        # Meta 信息混乱，我很担心
        class Callback(BaseModel):
            role: Literal["user", "system", "function", "assistant"] = Field("user", description="角色")
            name: str = Field(None, description="功能名称", regex=r"^[a-zA-Z0-9_]+$")

        function_enable: bool = Field(False, description="功能开关")

        callback_forward: bool = Field(False, description="非 LLM 转发")
        reprocess_needed: bool = Field(False, description="追加LLM回复,追加存储处理后再回复")

        verify_needed: bool = Field(False, description="此请求被分流标记需要平台的权限验证才能被执行")
        parent_call: Any = Field(None, description="存储上一个节点的父消息，用于插件的原始消息信息存储")
        callback: Callback = Field(Callback(), description="插件返回的消息头，标识了 function 的名字")
        extra_args: dict = Field({}, description="任何额外参数")

        class Config:
            arbitrary_types_allowed = True

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

        if trace_back_message is None:
            trace_back_message = []
        if file is None:
            file = []

        def _convert(_message: types.Message) -> Optional[RawMessage]:
            if not _message or not _message.text:
                return None
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
                text=text,
                created_at=created_at
            )

        _file_name = []
        if file:
            for _file in file:
                _file_name.append(f"![{_file.file_name}]")
        head_message = _convert(message)
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
    def from_function(cls, parent_call: Any, task_meta: Meta, receiver: Location, message: List[RawMessage] = None):
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


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner
