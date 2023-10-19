# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import hashlib
import pickle
import time
from io import BytesIO
from typing import Union, List, Optional

import nest_asyncio
from pydantic import Field, BaseModel, validator
from telebot import types

from .sdk.schema import File

nest_asyncio.apply()


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


class RawMessage(BaseModel):
    user_id: int = Field(None, description="user id")
    chat_id: int = Field(None, description="guild id(channel in dm)/Telegram chat id")
    thread_id: int = Field(None, description="channel id/Telegram thread")

    text: str = Field(None, description="文本")
    file: List[File] = Field([], description="文件")

    created_at: Union[int, float] = Field(default=int(time.time()), description="创建时间")
    just_file: bool = Field(default=False, description="Send file only")

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
    async def download_file(file_id) -> Optional[File.Data]:
        from llmkira.cache.redis import cache
        file = await cache.read_data(file_id)
        if not file:
            return None
        file_obj: File.Data = pickle.loads(file)
        return file_obj

    @staticmethod
    async def upload_file(name, data):
        from llmkira.cache.redis import cache
        _key = str(generate_md5_short_id(data))
        await cache.set_data(key=_key, value=pickle.dumps(File.Data(file_name=name, file_data=data)),
                             timeout=60 * 60 * 24 * 7)
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


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner
