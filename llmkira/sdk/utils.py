# -*- coding: utf-8 -*-

"""
bilibili_api.utils.sync

同步执行异步函数
"""
import asyncio
import hashlib
from bisect import bisect_left
from typing import Coroutine, Dict, List

import aiohttp
import nest_asyncio
import shortuuid
from telebot import formatting
from telebot.formatting import escape_markdown

nest_asyncio.apply()


def __ensure_event_loop():
    try:
        asyncio.get_event_loop()
    except Exception:
        asyncio.set_event_loop(asyncio.new_event_loop())


def dict2message(data: Dict[str, str]) -> List[str]:
    _res = []
    for key, value in data.items():
        _res.append("".join([formatting.mitalic(key), escape_markdown("="), f"`{escape_markdown(value)}`"]))
    return _res


def sync(coroutine: Coroutine):
    """
    同步执行异步函数，使用可参考 [同步执行异步代码](https://nemo2011.github.io/bilibili-api/#/sync-executor)

    Args:
        coroutine (Coroutine): 异步函数

    Returns:
        该异步函数的返回值
    """
    __ensure_event_loop()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


def sha1_encrypt(string):
    """
    sha1加密算法
    """

    sha = hashlib.sha1(string.encode('utf-8'))
    encrypts = sha.hexdigest()
    return encrypts[:8]


def generate_uid():
    return shortuuid.uuid()[0:8].upper()


async def download_file(url, timeout=None, size_limit=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout, headers=headers) as response:
            if response.status != 200:
                raise Exception("无法下载文件")

            content_length = response.content_length
            if size_limit and content_length and content_length > size_limit:
                raise Exception("文件大小超过限制")

            contents = await response.read()
            return contents


def prefix_search(wordlist, prefix):
    """
    在有序列表中二分查找前缀
    :param wordlist: 有序列表
    :param prefix: 前缀
    """
    try:
        index = bisect_left(wordlist, prefix)
        return wordlist[index].startswith(prefix)
    except IndexError:
        return False
