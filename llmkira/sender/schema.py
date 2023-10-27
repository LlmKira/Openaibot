# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import abstractmethod, ABC

from llmkira.sdk.openapi.transducer import LoopRunner
from loguru import logger


class Runner(ABC):

    async def loop_turn_only_message(self, platform_name, message, file_list) -> tuple:
        """
        将 Openai 消息传入 Loop 进行修饰
        此过程将忽略掉其他属性。只留下 content
        """
        loop_runner = LoopRunner()
        trans_loop = loop_runner.get_sender_loop(platform_name=platform_name)
        await loop_runner.exec_loop(
            pipe=trans_loop,
            # sender Parser 约定的参数组合
            pipe_arg={
                "message": message,
                "files": file_list
            }
        )
        _arg = loop_runner.result_pipe_arg
        if not _arg.get("message"):
            logger.error("Message Loop Lose Message")
        new_message, new_file_list = _arg.get("message", message), _arg.get("files", file_list)
        return new_message, new_file_list

    @abstractmethod
    async def upload(self, *args, **kwargs):
        ...

    @abstractmethod
    def run(self, *args, **kwargs):
        ...
