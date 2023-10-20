# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : util_func.py
# @Software: PyCharm
from urllib.parse import urlparse

from loguru import logger

from ..middleware.chain_box import Chain, AuthReloader
from ..task import Task


def parse_command(command):
    if not command:
        return None, None
    parts = command.split(" ", 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_command(text: str, command: str, at_bot_username: str = None, check_empty=False):
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


def is_empty_command(text: str):
    if not text.startswith("/"):
        return False
    if len(text.split(" ")) == 1:
        return True
    return False


async def auth_reloader(uuid: str, platform: str, user_id: str):
    chain: Chain = await AuthReloader.from_meta(platform=platform, user_id=user_id).get_auth(uuid=uuid)
    if not chain:
        raise Exception(f"Auth Task not found")
    logger.info(f"Auth Task be sent\n--uuid {uuid} --user {user_id}")
    await Task(queue=chain.address).send_task(task=chain.arg)
