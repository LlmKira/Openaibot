# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午9:57
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from functools import wraps
from enum import Enum
from typing import Type, Union, Set, List, Callable, Any

from loguru import logger

from .schema import Builder, Parser, AbstractTransfer

__builder__: Set[Type[Builder]] = set()
__parser__: Set[Type[Parser]] = set()


class Locate(Enum):
    sender = 1
    receiver = 0


def resign_transfer():
    """
    装饰器
    """

    def decorator(func: Union[Builder, Parser, Type[Builder], Type[Parser]]):
        if issubclass(func, Builder):
            logger.success(f"📦 Plugin:resign Builder transfer {func}")
            __builder__.add(func)
        elif issubclass(func, Parser):
            logger.success(f"📦 Plugin:resign Parser transfer {func}")
            __parser__.add(func)
        else:
            raise ValueError(f"Resign Transfer Error for unknown func {type(func)} ")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(**kwargs)

        return wrapper

    return decorator


class LoopRunner(object):
    pipe_arg: Any = None

    @staticmethod
    def get_receiver_loop(platform_name: str) -> List[Type[AbstractTransfer]]:
        """
        receiver builder
        message: "RawMessage"
        :return platform
        """
        _loop = []
        for _exec_ram in __builder__:
            _exec = _exec_ram()
            if not _exec.sign:
                logger.error(f"receiver_loop metadata None:sign")
                continue
            if not _exec.sign.platform:
                logger.error(f"receiver_loop metadata None:platform")
                continue
            if _exec.sign.priority is None:
                logger.error(f"receiver_loop metadata None:priority")
                continue
            if _exec.sign.agent != "receiver":
                continue
            if _exec.sign.platform.match(platform_name):
                _loop.append(_exec_ram)
        _loop.sort(key=lambda x: x.sign.priority, reverse=True)
        return _loop

    @staticmethod
    def get_sender_loop(platform_name) -> List[Type[AbstractTransfer]]:
        """
        receiver sender
        message: list, file: List[File]
        :return platform
        """
        _loop = []
        for _exec_ram in __parser__:
            _exec = _exec_ram()
            if not _exec.sign:
                logger.error(f"sender_loop metadata None:sign")
                continue
            if not _exec.sign.platform:
                logger.error(f"sender_loop metadata None:platform")
                continue
            if _exec.sign.priority is None:
                logger.error(f"sender_loop metadata None:priority")
                continue
            if _exec.sign.agent == "sender":
                continue
            if _exec.sign.platform.match(platform_name):
                _loop.append(_exec_ram)
        _loop.sort(key=lambda x: x.sign.priority, reverse=True)
        return _loop

    @property
    def result_pipe_arg(self):
        if not self.pipe_arg:
            raise ValueError(f"pipe_arg is None")
        return self.pipe_arg

    async def exec_loop(self, pipe: List[Type[AbstractTransfer]], pipe_arg: dict, validator: Callable = None):
        """
        exec loop
        """
        self.pipe_arg = pipe_arg
        for loop in pipe:
            try:
                if validator:
                    validator(**self.pipe_arg)
                new_pipe_arg = await loop().pipe(self.pipe_arg)
            except Exception as e:
                logger.info(f"{loop} exec_loop error {e}, for sign:{loop.sign}")
                logger.debug(f"{loop} exec_loop error {e}, for sign:{loop.sign}, pipe_arg:{pipe_arg}")
                # 不更新 pipe_arg
            else:
                logger.info(f"{loop} exec_loop success, for sign:{loop.sign}")
                logger.debug(f"{loop} exec_loop success, for sign:{loop.sign}, new_pipe_arg:{new_pipe_arg}")
                self.pipe_arg = new_pipe_arg


from .default_factory import DefaultMessageBuilder, DefaultMessageParser
