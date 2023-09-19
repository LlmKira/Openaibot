# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 下午11:27
# @Author  : sudoskys
# @File    : utils.py
# @Software: PyCharm
from urllib.parse import urlparse


def parse_command(command):
    if not command:
        return None, None
    parts = command.split(" ", 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        return None, None


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
