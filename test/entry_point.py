# -*- coding: utf-8 -*-
# @Time    : 2023/10/12 下午9:48
# @Author  : sudoskys
# @File    : entry_point.py
# @Software: PyCharm

import importlib_metadata

_result = importlib_metadata.entry_points().select(group="llmkira.extra.plugin")
print(type(_result))
for item in _result:
    print(item.module)
    rs = item.load()
    print(rs)

print(_result)
# importlib.import_module(_result.module)

