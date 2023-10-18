# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 上午11:47
# @Author  : sudoskys
# @File    : default_factory.py
# @Software: PyCharm
from typing import List

from llmkira.sdk.schema import File

from .schema import Builder, Parser


class DefaultBuilder(Builder):
    def build(self, message, *args) -> (bool, List[File]):
        return False, []


class DefaultParser(Parser):
    def parse(self, message, file: List[File], *args) -> (list, List[File]):
        return [], file
