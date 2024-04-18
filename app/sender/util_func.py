# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : util_func.py
# @Software: PyCharm
import time
from typing import Tuple, Optional, Union
from urllib.parse import urlparse

from loguru import logger

from app.components.credential import Credential
from app.components.user_manager import USER_MANAGER
from llmkira.task import Task
from llmkira.task.snapshot import SnapData, global_snapshot_storage


def uid_make(platform: str, user_id: Union[int, str]):
    return f"{platform}:{user_id}"


async def login(uid, credential: Credential):
    user = await USER_MANAGER.read(user_id=uid)
    user.credential = credential
    await USER_MANAGER.save(user_model=user)


def parse_command(command: str) -> Tuple[Optional[str], Optional[str]]:
    """
    :param command like `/chat something`
    :return command_head,command_body
    """
    assert isinstance(command, str), "Command Must Be Str"
    if not command:
        return None, None
    parts = command.split(" ", 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None


def is_valid_url(url) -> bool:
    """
    :param url url
    :return bool
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_command(
    text: str, command: str, at_bot_username: str = None, check_empty=False
) -> bool:
    """
    :param text: message text
    :param command: command
    :param at_bot_username: check /command@bot_username
    :param check_empty: check /command -> False
    :return: bool
    """
    assert text, "text is empty"
    if check_empty:
        if len(text.split(" ")) == 1:
            return False
    if text.startswith(f"{command} "):
        return True
    if at_bot_username:
        if text.startswith(f"{command}@{at_bot_username}"):
            return True
    if text == command:
        return True
    return False


def is_empty_command(text: str) -> bool:
    assert text, "Command Input Must Be Str"
    if not text.startswith("/"):
        return False
    if len(text.split(" ")) == 1:
        return True
    return False


async def auth_reloader(snapshot_credential: str, platform: str, user_id: str) -> None:
    """
    :param snapshot_credential: verify id
    :param platform: message channel
    :param user_id: raw user id
    :raise LookupError Not Found
    :return None
    """
    assert isinstance(snapshot_credential, str), "`uuid` Must Be Str"
    assert isinstance(platform, str), "`platform` Must Be Str"
    assert isinstance(user_id, str), "`user_id` Must Be Str"
    snap_shot: SnapData = await global_snapshot_storage.read(
        user_id=uid_make(platform, user_id)
    )
    if not snap_shot:
        raise LookupError("Auth Task Not Found")
    if not snap_shot.data:
        raise LookupError("Auth Task Data Not Found")
    logger.info(f"Snap Auth:{snapshot_credential},by user {user_id}")
    for snap in snap_shot.data:
        if snap.snapshot_credential == snapshot_credential:
            return await Task.create_and_send(
                queue_name=snap.channel,
                task=snap.snapshot_data,
            )


class TimerObjectContainer:
    def __init__(self):
        self.users = {}

    def add_object(self, user_id, obj):
        if user_id not in self.users:
            self.users[user_id] = {}
        self.users[user_id][obj] = time.time()

    def get_objects(self, user_id, second=1200) -> list:  # 20 minutes = 1200 seconds
        """
        获取特定用户的对象列表，并自动删除在指定时间内添加的对象
        :param user_id: 用户ID
        :param second: 时间（秒）
        """
        if user_id not in self.users:
            return []

        user_objs = self.users[user_id]
        valid_objects = {
            obj: add_time
            for obj, add_time in user_objs.items()
            if time.time() - add_time < second
        }

        self.users[user_id] = valid_objects
        return list(valid_objects.keys())

    def clear_objects(self, user_id):
        """
        清空特定用户的对象
        :param user_id: 用户ID
        """
        if user_id in self.users:
            self.users[user_id] = {}
