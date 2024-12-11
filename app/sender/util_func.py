# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : util_func.py
# @Software: PyCharm
import time
from typing import Tuple, Optional, Union
from urllib.parse import urlparse

import telegramify_markdown
from loguru import logger

from app.components.credential import Credential, ProviderError
from app.components.user_manager import USER_MANAGER
from llmkira.kv_manager.instruction import InstructionManager
from llmkira.task import Task
from llmkira.task.snapshot import SnapData, global_snapshot_storage


def uid_make(platform: str, user_id: Union[int, str]):
    return f"{platform}:{user_id}"


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


def split_setting_string(input_string):
    """
    Split setting string
    :param input_string: input string
    :return: list or None
    """
    if not isinstance(input_string, str):
        return None
    segments = input_string.split("$")

    # 开头为链接的情况
    if is_valid_url(segments[0]) and len(segments) >= 3:
        return segments[:3]
    # 第二个元素为链接，第一个元素为字符串的情况
    elif (
        len(segments) == 2
        and not is_valid_url(segments[0])
        and is_valid_url(segments[1])
    ):
        return segments
    # 其他情况
    else:
        return None


async def save_credential(uid, credential: Credential):
    user = await USER_MANAGER.read(user_id=uid)
    user.credential = credential
    await USER_MANAGER.save(user_model=user)


async def learn_instruction(uid: str, instruction: str) -> str:
    """
    Set instruction text
    :param uid: uid_make
    :param instruction: instruction text
    :return: str message
    """
    if len(instruction) > 1500:
        return "your instruction text length should be less than 1500"
    manager = InstructionManager(user_id=uid)
    if len(instruction) < 7:
        instruction = ""
        await manager.set_instruction(instruction)
        return "I already reset your instruction to default..."
    else:
        await manager.set_instruction(instruction)
        return "I keep it in my mind!"


async def login(uid: str, arg_string) -> str:
    """
    Login as provider or model
    :param uid: uid_make
    :param arg_string: input string
    :return: str message
    """
    error = telegramify_markdown.markdownify(
        "🔑 **Incorrect format.**\n"
        "You can set it via `/login https://<something api.openai.com>/v1$<api key>"
        "$<model such as gpt-4-turbo>$<tool_model such as gpt-4o-mini>` format, "
        "or you can log in via URL using `/login token$https://provider.com`.\n"
        "Use $ to separate the parameters."
    )
    settings = split_setting_string(arg_string)
    if not settings:
        return error
    if len(settings) == 2:
        try:
            credential = Credential.from_provider(
                token=settings[0], provider_url=settings[1]
            )
        except ProviderError as e:
            return telegramify_markdown.markdownify(f"Login failed, website return {e}")
        except Exception as e:
            logger.error(f"Login failed {e}")
            return telegramify_markdown.markdownify(f"Login failed, because {type(e)}")
        else:
            await save_credential(
                uid=uid,
                credential=credential,
            )
            return telegramify_markdown.markdownify(
                "Login success as provider! Welcome master!"
            )
    elif len(settings) == 3 or len(settings) == 4:
        api_endpoint = settings[0]
        api_key = settings[1]
        api_model = settings[2]
        if len(settings) == 4:
            api_tool_model = settings[3]
        else:
            api_tool_model = "gpt-4o-mini"
        credential = Credential(
            api_endpoint=api_endpoint,
            api_key=api_key,
            api_model=api_model,
            api_tool_model=api_tool_model,
        )
        await save_credential(
            uid=uid,
            credential=credential,
        )
        return telegramify_markdown.markdownify(
            f"Login success as {settings[2]}! Welcome master!"
        )
    else:
        return error


async def logout(uid: str) -> str:
    """
    Logout
    :param uid: uid_make
    :return: str message
    """
    user = await USER_MANAGER.read(user_id=uid)
    user.credential = None
    await USER_MANAGER.save(user_model=user)
    return telegramify_markdown.markdownify("Logout success! Welcome back master!")


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


def dict2markdown(maps: dict):
    content = "**🦴 Env**\n"
    for key, value in maps.items():
        content += f"- **`{key}`**: `{value}`\n"
    return content
