# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午4:01
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm


######
# 管道前置触发管理器，注册触发词或禁止触发词
######


import inspect
from functools import wraps
from typing import Literal, List, Callable
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class Trigger(BaseModel):
    on_func: Callable = None
    on_platform: str
    action: Literal["allow", "deny"] = "allow"
    priority: int = Field(default=0, ge=-100, le=100)
    message: str = Field(default="Trigger deny your message")
    function_enable: bool = Field(default=False)

    def update_func(self, func: callable):
        self.on_func = func
        return self


__trigger_phrases__: List[Trigger] = []


async def get_trigger_loop(platform_name: str, message: str, uid: str = None):
    """
    receiver builder
    message: Message Content
    :return 如果有触发，则返回触发的action，否则返回None 代表没有操作
    """
    trigger_sorted = sorted(__trigger_phrases__, key=lambda x: x.priority)
    if not message:
        message = ""
    for trigger in trigger_sorted:
        if trigger.on_platform == platform_name:
            try:
                if await trigger.on_func(message, uid):
                    return trigger
            except Exception as e:
                logger.error(f"📦 Plugin:trigger error: {e}")
                pass
    return None


def resign_trigger(trigger: Trigger):
    """
    装饰器
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            __trigger_phrases__.append(trigger.update_func(func))
            logger.success(f"📦 [Plugin trigger hook] {trigger.__repr__()}")
        else:
            raise ValueError(
                f"Resign Trigger Error for func {func} is not async function"
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(*args, **kwargs)

        return wrapper

    return decorator
