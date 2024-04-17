# -*- coding: utf-8 -*-
# @Time    : 2023/10/22 下午7:37
# @Author  : sudoskys
# @File    : trans.py
# @Software: PyCharm
from typing import List, Any

from llmkira.sdk.schema import File
from llmkira.openapi.transducer import resign_transfer, Builder, Parser

__receiver_name__ = "discord"


@resign_transfer()
class Builder(Builder):
    def build(self, message, *args) -> (bool, List[File]):
        """
        仅仅 hook LLM 的正常回复，即 reply 函数。
        :param message: 单条通用消息 (RawMessage)
        :param args: 其他参数
        :return: 是否放弃发送文本, 需要发送的文件列表(RawMessage.upload)
        """
        return False, []


"""
            _transfer = TransferManager().receiver_builder(agent_name=__receiver__)
            only_send_file, file_list = _transfer().build(message=item)
"""


@resign_transfer(agent_name=__receiver_name__)
class Parser(Parser):
    async def pipe(self, arg: dict) -> Any:
        pass

    def parse(self, message, file: List[File], *args) -> (list, List[File]):
        """
        接收 sender 平台的 **原始** 消息，返回文件。
        需要注意的是，这里的 message 是原始消息，不是我们转换后的通用消息类型。
        :param message: 单条原始消息
        :param file: 文件列表
        :param args: 其他参数
        :return: 返回 **追加的** 消息列表,返回文件列表,
        """
        return [], file


"""
                # 转析器
                _transfer = TransferManager().sender_parser(agent_name=__sender__)
                deliver_back_message, _file = _transfer().parse(message=message, file=_file)
"""
