# -*- coding: utf-8 -*-
# @Time    : 2023/11/9 下午2:05
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import List

from pydantic import BaseModel, Field


class SlackMessageEvent(BaseModel):
    """
    https://api.slack.com/events/message.im
    """

    class SlackFile(BaseModel):
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
    files: List["SlackFile"] = Field(default=[], description="files")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
