# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 下午1:47
# @Author  : sudoskys
# @File    : __init__.py
# @Software: PyCharm

"""
这里的 schema 是为服务商的sdk照应而写的。
包含请求体，响应体，以及对齐的数据结构。
我们自己的数据结构在 sdk/schema.py 中定义。
请求时，我们需要将自己的数据结构转换为这里的数据结构。
"""
from .tee import Driver
from .tokenizer import get_tokenizer
