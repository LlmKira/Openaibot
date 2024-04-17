# -*- coding: utf-8 -*-
# @Time    : 2023/11/9 下午2:05
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import List, Optional

from pydantic import ConfigDict, BaseModel, Field


class SlackFile(BaseModel):
    id: Optional[str] = Field(None, description="id")
    created: int = Field(None, description="created")
    timestamp: int = Field(None, description="timestamp")
    name: Optional[str] = Field(None, description="name")
    title: Optional[str] = Field(None, description="title")
    mimetype: Optional[str] = Field(None, description="mimetype")
    filetype: Optional[str] = Field(None, description="filetype")
    pretty_type: Optional[str] = Field(None, description="pretty_type")
    user: Optional[str] = Field(None, description="user")
    user_team: Optional[str] = Field(None, description="user_team")
    editable: bool = Field(None, description="editable")
    size: int = Field(None, description="size")
    mode: Optional[str] = Field(None, description="mode")
    is_external: bool = Field(None, description="is_external")
    external_type: Optional[str] = Field(None, description="external_type")
    is_public: bool = Field(None, description="is_public")
    public_url_shared: bool = Field(None, description="public_url_shared")
    display_as_bot: bool = Field(None, description="display_as_bot")
    username: Optional[str] = Field(None, description="username")
    url_private: Optional[str] = Field(None, description="url_private")
    url_private_download: Optional[str] = Field(
        None, description="url_private_download"
    )
    media_display_type: Optional[str] = Field(None, description="media_display_type")
    thumb_64: Optional[str] = Field(None, description="thumb_64")
    thumb_80: Optional[str] = Field(None, description="thumb_80")
    thumb_360: Optional[str] = Field(None, description="thumb_360")
    thumb_360_w: int = Field(None, description="thumb_360_w")
    thumb_360_h: int = Field(None, description="thumb_360_h")
    thumb_160: Optional[str] = Field(None, description="thumb_160")
    original_w: int = Field(None, description="original_w")
    original_h: int = Field(None, description="original_h")
    thumb_tiny: Optional[str] = Field(None, description="thumb_tiny")
    permalink: Optional[str] = Field(None, description="permalink")
    permalink_public: Optional[str] = Field(None, description="permalink_public")
    has_rich_preview: bool = Field(None, description="has_rich_preview")
    file_access: Optional[str] = Field(None, description="file_access")


class SlackMessageEvent(BaseModel):
    """
    https://api.slack.com/events/message.im
    """

    client_msg_id: Optional[str] = Field(None, description="client_msg_id")
    type: Optional[str] = Field(None, description="type")
    text: Optional[str] = Field(None, description="text")
    user: Optional[str] = Field(None, description="user")
    ts: Optional[str] = Field(None, description="ts")
    blocks: List[dict] = Field([], description="blocks")
    team: Optional[str] = Field(None, description="team")
    thread_ts: Optional[str] = Field(None, description="thread_ts")
    parent_user_id: Optional[str] = Field(None, description="parent_user_id")
    channel: Optional[str] = Field(None, description="channel")
    event_ts: Optional[str] = Field(None, description="event_ts")
    channel_type: Optional[str] = Field(None, description="channel_type")
    files: List[SlackFile] = Field(default=[], description="files")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
