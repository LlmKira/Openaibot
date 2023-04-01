# -*- coding: utf-8 -*-
# @Time    : 2023/3/31 下午9:46
# @Author  : sudoskys
# @File    : __init__.py
# @Software: PyCharm
from Component.data.file import FileClientWrapper, file_client
from Component.data.mongo import MongoClientWrapper, mongo_client

__all__ = ["MongoClientWrapper", "mongo_client", "FileClientWrapper", "file_client"]
