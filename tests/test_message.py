# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午8:05
# @Author  : sudoskys
# @File    : test_message.py
# @Software: PyCharm
import sys

sys.path.append("..")

from llmkira.sdk.schema import Message, UserMessage


def test_schema():
    try:
        Message(role="user", content="test")
    except TypeError as e:
        pass
    else:
        assert False, "Should Raise Error"
    UserMessage(content="test")
