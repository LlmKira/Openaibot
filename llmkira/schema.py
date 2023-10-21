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
    user_id: Union[int, str] = Field(None, description="user id")
    chat_id: Union[int, str] = Field(None, description="guild id(channel in dm)/Telegram chat id")
    thread_id: Union[int, str] = Field(None, description="channel id/Telegram thread")

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


class SlackMessageEvent(BaseModel):
    """
    https://api.slack.com/events/message.im
    {'type': 'message', 'text': '<@U061ZRKSHPY>', 'files': [{'id': 'F061SBFUDPZ', 'created': 1697884329, 'timestamp': 1697884329, 'name': 'Screenshot_20230427_131106.png', 'title': 'Screenshot_20230427_131106.png', 'mimetype': 'image/png', 'filetype': 'png', 'pretty_type': 'PNG', 'user': 'U0628TSTVN0', 'user_team': 'T0626BTG17D', 'editable': False, 'size': 699907, 'mode': 'hosted', 'is_external': False, 'external_type': '', 'is_public': False, 'public_url_shared': False, 'display_as_bot': False, 'username': '', 'url_private': 'https://files.slack.com/files-pri/T0626BTG17D-F061SBFUDPZ/screenshot_20230427_131106.png', 'url_private_download': 'https://files.slack.com/files-pri/T0626BTG17D-F061SBFUDPZ/download/screenshot_20230427_131106.png', 'media_display_type': 'unknown', 'thumb_64': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_64.png', 'thumb_80': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_80.png', 'thumb_360': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_360.png', 'thumb_360_w': 360, 'thumb_360_h': 303, 'thumb_480': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_480.png', 'thumb_480_w': 480, 'thumb_480_h': 404, 'thumb_160': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_160.png', 'thumb_720': 'https://files.slack.com/files-tmb/T0626BTG17D-F061SBFUDPZ-3211e7c916/screenshot_20230427_131106_720.png', 'thumb_720_w': 720, 'thumb_720_h': 606, 'original_w': 786, 'original_h': 662, 'thumb_tiny': 'AwAoADA8xsYKdO+aTdlzkYOKkUA9TzTSnzE59qVyrEkQBVqhbgkVKhwMcfWmSgEbgc+/akAzNITxSZppamItrC3XoPemE4U4XcfSpbqVQpUNzVRWBPyn6jNIZNnKncNpI6U7aFGBwB2qLzgPlZfrTmbf0GfakMPMUHDRilDQt/CB+FNKFgAD04+tQtwSMYpiJpSfM3IOtNaMO2RJlx9Kk9PxqGD/AFx+tDAlETjHG4e4qQRtjAUAd6lFOFICqI2j4bkZyDT1iRzuIJP1p8vaiLov40Af/9k=', 'permalink': 'https://w1697860710-etj695090.slack.com/files/U0628TSTVN0/F061SBFUDPZ/screenshot_20230427_131106.png', 'permalink_public': 'https://slack-files.com/T0626BTG17D-F061SBFUDPZ-7bdcfcc092', 'has_rich_preview': False, 'file_access': 'visible'}], 'upload': False, 'user': 'U0628TSTVN0', 'display_as_bot': False, 'ts': '1697884336.401129', 'blocks': [{'type': 'rich_text', 'block_id': 'fdKCA', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'user', 'user_id': 'U061ZRKSHPY'}]}]}], 'client_msg_id': '68c32ab4-796b-4908-b3d7-de59b4edf4ae', 'channel': 'D062K3ZUCC9', 'subtype': 'file_share', 'event_ts': '1697884336.401129', 'channel_type': 'im'}
    """

    class SlackFile(BaseModel):
        """
        {'id': 'F062405Q9GV', 'created': 1697884518, 'timestamp': 1697884518, 'name': 'Screenshot_20230427_003637.png', 'title': 'Screenshot_20230427_003637.png', 'mimetype': 'image/png', 'filetype': 'png', 'pretty_type': 'PNG', 'user': 'U0628TSTVN0', 'user_team': 'T0626BTG17D', 'editable': False, 'size': 64398, 'mode': 'hosted', 'is_external': False, 'external_type': '', 'is_public': False, 'public_url_shared': False, 'display_as_bot': False, 'username': '', 'url_private': 'https://files.slack.com/files-pri/T0626BTG17D-F062405Q9GV/screenshot_20230427_003637.png', 'url_private_download': 'https://files.slack.com/files-pri/T0626BTG17D-F062405Q9GV/download/screenshot_20230427_003637.png', 'media_display_type': 'unknown', 'thumb_64': 'https://files.slack.com/files-tmb/T0626BTG17D-F062405Q9GV-73b74d7cb9/screenshot_20230427_003637_64.png', 'thumb_80': 'https://files.slack.com/files-tmb/T0626BTG17D-F062405Q9GV-73b74d7cb9/screenshot_20230427_003637_80.png', 'thumb_360': 'https://files.slack.com/files-tmb/T0626BTG17D-F062405Q9GV-73b74d7cb9/screenshot_20230427_003637_360.png', 'thumb_360_w': 360, 'thumb_360_h': 354, 'thumb_160': 'https://files.slack.com/files-tmb/T0626BTG17D-F062405Q9GV-73b74d7cb9/screenshot_20230427_003637_160.png', 'original_w': 454, 'original_h': 446, 'thumb_tiny': 'AwAvADDOoooBwc0AFFSOmSrIOH6AevpT7iIRJGDgSEcgUAQUUUUAFFFFAE1u+Dsz16exqaS3aSIyg5IGcZ5qQNaOi7mC46YHSmXs6yxKIuUBwTQBSooooAKKKKAFXqKdGwBIP3TwaZRQAHrRRRTA/9k=', 'permalink': 'https://w1697860710-etj695090.slack.com/files/U0628TSTVN0/F062405Q9GV/screenshot_20230427_003637.png', 'permalink_public': 'https://slack-files.com/T0626BTG17D-F062405Q9GV-073cd09a8b', 'has_rich_preview': False, 'file_access': 'visible'}
        """
        id: str = Field(None, description="id")
        created: int = Field(None, description="created")
        timestamp: int = Field(None, description="timestamp")
        name: str = Field(None, description="name")
        title: str = Field(None, description="title")
        mimetype: str = Field(None, description="mimetype")
        filetype: str = Field(None, description="filetype")
        pretty_type: str = Field(None, description="pretty_type")
        user: str = Field(None, description="user")
        user_team: str = Field(None, description="user_team")
        editable: bool = Field(None, description="editable")
        size: int = Field(None, description="size")
        mode: str = Field(None, description="mode")
        is_external: bool = Field(None, description="is_external")
        external_type: str = Field(None, description="external_type")
        is_public: bool = Field(None, description="is_public")
        public_url_shared: bool = Field(None, description="public_url_shared")
        display_as_bot: bool = Field(None, description="display_as_bot")
        username: str = Field(None, description="username")
        url_private: str = Field(None, description="url_private")
        url_private_download: str = Field(None, description="url_private_download")
        media_display_type: str = Field(None, description="media_display_type")
        thumb_64: str = Field(None, description="thumb_64")
        thumb_80: str = Field(None, description="thumb_80")
        thumb_360: str = Field(None, description="thumb_360")
        thumb_360_w: int = Field(None, description="thumb_360_w")
        thumb_360_h: int = Field(None, description="thumb_360_h")
        thumb_160: str = Field(None, description="thumb_160")
        original_w: int = Field(None, description="original_w")
        original_h: int = Field(None, description="original_h")
        thumb_tiny: str = Field(None, description="thumb_tiny")
        permalink: str = Field(None, description="permalink")
        permalink_public: str = Field(None, description="permalink_public")
        has_rich_preview: bool = Field(None, description="has_rich_preview")
        file_access: str = Field(None, description="file_access")

    client_msg_id: str = Field(None, description="client_msg_id")
    type: str = Field(None, description="type")
    text: str = Field(None, description="text")
    user: str = Field(None, description="user")
    ts: str = Field(None, description="ts")
    blocks: List[dict] = Field([], description="blocks")
    team: str = Field(None, description="team")
    thread_ts: str = Field(None, description="thread_ts")
    parent_user_id: str = Field(None, description="parent_user_id")
    channel: str = Field(None, description="channel")
    event_ts: str = Field(None, description="event_ts")
    channel_type: str = Field(None, description="channel_type")
    files: List[SlackFile] = Field(default=[], description="files")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
