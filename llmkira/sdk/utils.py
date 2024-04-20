# -*- coding: utf-8 -*-

"""
bilibili_api.utils.sync

同步执行异步函数
"""
import asyncio
import hashlib
import tempfile
from bisect import bisect_left
from typing import Coroutine, Optional
from urllib.parse import urlparse

import aiohttp
import ffmpeg
import shortuuid
from loguru import logger


# import nest_asyncio
# nest_asyncio.apply()


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def __ensure_event_loop():
    try:
        asyncio.get_event_loop()
    except Exception as e:  # noqa
        asyncio.set_event_loop(asyncio.new_event_loop())


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

    sha = hashlib.sha1(string.encode("utf-8"))
    encrypts = sha.hexdigest()
    return encrypts[:8]


def generate_uid():
    return shortuuid.uuid()[0:8].upper()


async def aiohttp_download_file(
    url,
    session: aiohttp.ClientSession = None,
    timeout=None,
    size_limit=None,
    headers=None,
    **kwargs,
):
    if not session:
        session = aiohttp.ClientSession()
    async with session as session:
        async with session.get(
            url, timeout=timeout, headers=headers, **kwargs
        ) as response:
            if response.status != 200:
                raise Exception("无法下载文件")

            content_length = response.content_length
            if size_limit and content_length and content_length > size_limit:
                raise Exception("文件大小超过限制")

            contents = await response.read()
            return contents


class Ffmpeg(object):
    @staticmethod
    def convert(
        *,
        input_c: str = "mp3",
        output_c: str = "ogg",
        stream_data: bytes = None,
        quiet=False,
    ) -> Optional[bytes]:
        """
        使用ffmpeg转换音频格式
        :param input_c: 输入音频格式
        :param output_c: 输出音频格式
        :param stream_data: 输入音频流
        :param quiet: 是否静默
        """
        if not input_c.startswith("."):
            input_c = "." + input_c
        if not output_c.startswith("."):
            output_c = "." + output_c
        in_fd, temp_filename = tempfile.mkstemp(
            suffix=input_c, prefix=None, dir=None, text=False
        )
        out_fd, out_temp_filename = tempfile.mkstemp(
            suffix=output_c, prefix=None, dir=None, text=False
        )
        _bytes = None
        try:
            # 写入文件
            with open(temp_filename, "wb") as f:
                f.write(stream_data)
            stream = ffmpeg.input(filename=temp_filename)
            if output_c == ".ogg":
                stream = ffmpeg.output(
                    stream, filename=out_temp_filename, acodec="libopus"
                )
            else:
                stream = ffmpeg.output(stream, filename=out_temp_filename)
            stream = ffmpeg.overwrite_output(stream)
            _ = ffmpeg.run(stream_spec=stream, quiet=quiet)
            # 读取文件
            import os

            _bytes = os.read(out_fd, os.path.getsize(out_temp_filename))
            assert _bytes, "ffmpeg convert failed"
        except Exception as e:
            logger.error(f"ffmpeg convert failed {e}")
            raise e
        finally:
            import os

            os.close(in_fd)
            os.close(out_fd)
            os.remove(out_temp_filename)
            os.remove(temp_filename)
        return _bytes


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
