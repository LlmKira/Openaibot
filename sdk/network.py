import asyncio
import atexit
import json
from typing import Any

import httpx

from .error import RateLimitError, ServiceUnavailableError, AuthenticationError

__session_pool = {}


def llm_error_handler(code, message: str):
    if code == 429:
        raise RateLimitError(message)
    elif code == 500 or code != 401:
        raise ServiceUnavailableError(message)
    else:
        raise AuthenticationError(message)


async def request(
        method: str,
        url: str,
        params: dict = None,
        data: Any = None,
        headers: dict = None,
        json_body: bool = False,
        proxy: str = "",
        call_func=None,
        **kwargs,
):
    """
    请求
    :param call_func: 回调函数，用于调整结构
    :param method:
    :param url:
    :param params:
    :param data:
    :param headers:
    :param json_body:
    :param proxy:
    :param kwargs: 参数
    :return:
    """
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    config = {
        "method": method.upper(),
        "url": url,
        "params": params,
        "data": data,
        "headers": headers,
    }

    # 更新
    config.update(kwargs)
    if json_body:
        config["headers"]["Content-Type"] = "application/json"
        config["data"] = json.dumps(config["data"]).encode()

    # SSL
    # config["ssl"] = False

    session = get_session(proxy=proxy)
    resp = await session.request(**config)

    # 检查响应头 Content-Length
    content_length = resp.headers.get("content-length")
    if content_length and int(content_length) == 0:
        return None

    # 检查响应头 Content-Type
    content_type = resp.headers.get("content-type")

    # Not application/json
    if content_type.lower().index("application/json") == -1:
        raise Exception("请求不是 application/json 类型")

    # 提取内容
    raw_data = resp.text
    req_data: dict
    req_data = json.loads(raw_data)

    # Error
    if req_data.get("error"):
        # if ERROR.get('type') == "insufficient_quota":
        if call_func:
            call_func(
                req_data,
                headers
            )
        _error = req_data.get("error")
        llm_error_handler(
            code=resp.status_code,
            message=f"{resp.status_code}:{_error.get('type')}:{_error.get('message')}"
        )
    return req_data


def get_session(proxy: str = ""):
    global __session_pool
    loop = asyncio.get_event_loop()
    session = __session_pool.get(loop, None)
    if session is None:
        if proxy:
            proxies = {"all://": proxy}
            session = httpx.AsyncClient(timeout=300, proxies=proxies)
        else:
            session = httpx.AsyncClient(timeout=300)
        __session_pool[loop] = session
    return session


@atexit.register
def __clean():
    """
    程序退出清理操作。
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return

    async def __clean_task():
        await __session_pool[loop].close()

    if loop.is_closed():
        loop.run_until_complete(__clean_task())
    else:
        loop.create_task(__clean_task())



