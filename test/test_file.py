# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午8:05
# @Author  : sudoskys
# @File    : test_file.py
# @Software: PyCharm
import sys

from llmkira.sdk.schema import File

sys.path.append("..")


def test_schema():
    File(
        file_id=None, file_name="test"
    )
