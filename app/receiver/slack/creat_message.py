# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午8:02
# @Author  : sudoskys
# @File    : creat_message.py
# @Software: PyCharm
from enum import Enum
from typing import Union

import emoji


class SlackEmoji(Enum):
    robot = ":robot_face:"
    check = ":white_check_mark:"
    error = ":x:"
    pin = ":pushpin:"
    thumbs_up = ":thumbsup:"
    thumbs_down = ":thumbsdown:"
    eyes = ":eyes:"
    gear = ":gear:"
    pencil = ":pencil:"
    moai = ":moai:"
    telescope = ":telescope:"
    hammer = ":hammer:"
    warning = ":warning:"


class ChatMessageCreator(object):
    WELCOME_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Welcome to Slack! :wave: We're so glad you're here. :blush:\n\n"
                "*Get started by completing the steps below:*"
            ),
        },
    }
    DIVIDER_BLOCK = {"type": "divider"}

    def __init__(
        self,
        channel,
        user_name: str = None,
        thread_ts: str = None,
    ):
        self.channel = channel
        self.username = user_name if user_name else "OAIbot"
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.thread_ts = thread_ts
        self.blocks = []

    @staticmethod
    def build_block(text, msg_type: str = "section"):
        """
        create a section block
        """
        _block = {
            "type": msg_type,
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        }
        return _block

    def update_content(self, message_text):
        """
        Message text in markdown format
        """
        self.blocks.append(self.build_block(message_text))
        return self

    def update_emoji(self, emoji_name: Union[str, SlackEmoji]):
        if isinstance(emoji_name, SlackEmoji):
            self.icon_emoji = emoji_name.value
            return self
        emoji_name = emoji_name.strip()
        if ":" in emoji_name:
            self.icon_emoji = emoji_name
        else:
            _emoji = emoji.demojize(emoji_name)
            if _emoji.endswith(":"):
                self.icon_emoji = _emoji
        return self

    def get_message_payload(self, message_text=None):
        if not self.blocks:
            raise ValueError("Message cannot be empty")
        _arg = {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": self.blocks,
        }
        if self.thread_ts:
            _arg["thread_ts"] = self.thread_ts
        if message_text:
            _arg["text"] = message_text
        return _arg
