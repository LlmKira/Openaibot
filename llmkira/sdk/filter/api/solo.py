# -*- coding: utf-8 -*-
# @Time    : 2023/9/6 下午4:58
# @Author  : sudoskys
# @File    : solo.py
# @Software: PyCharm
def singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton
