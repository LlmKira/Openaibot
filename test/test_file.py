# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午8:05
# @Author  : sudoskys
# @File    : test_file.py
# @Software: PyCharm
import sys

sys.path.append("..")

from llmkira.sdk.schema import File


def test_schema():
    File(
        file_id=None, file_name="test"
    )
