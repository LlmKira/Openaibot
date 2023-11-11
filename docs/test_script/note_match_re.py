# -*- coding: utf-8 -*-
# @Time    : 2023/11/11 下午11:09
# @Author  : sudoskys
# @File    : match.py
# @Software: PyCharm
import re
from pprint import pprint

if __name__ == '__main__':
    result = re.compile(r"(.+).jpg|(.+).png|(.+).jpeg|(.+).gif|(.+).webp|(.+).svg").match("1.webp")
    pprint(result)
