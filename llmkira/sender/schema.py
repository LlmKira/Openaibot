# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 下午10:02
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import abstractmethod, ABC


class Runner(ABC):

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
