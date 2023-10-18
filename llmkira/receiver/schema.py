# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import ABCMeta, abstractmethod


class ReplyRunner(object, metaclass=ABCMeta):
    @abstractmethod
    def file_forward(self, chat_id, reply_to_message_id, file_list, **kwargs):
        pass

    @abstractmethod
    def forward(self, chat_id, reply_to_message_id, message, **kwargs):
        """
        插件专用转发，是Task通用类型
        """
        pass

    @abstractmethod
    def reply(self, chat_id, reply_to_message_id, message, **kwargs):
        """
        模型直转发，Message是Openai的类型
        """
        pass

    @abstractmethod
    def error(self, chat_id, reply_to_message_id, text, **kwargs):
        pass

    @abstractmethod
    def function(self, chat_id, reply_to_message_id, task, llm, result, message, **kwargs):
        pass
