# -*- coding: utf-8 -*-
# @Time    : 12/28/22 10:20 AM
# @FileName: test_module.py
# @Software: PyCharm
# @Github    ：sudoskys
from module.main import test_plugin
# 日志追踪调试
from loguru import logger
import sys

logger.remove()
handler_id = logger.add(sys.stderr, level="TRACE")
# 日志追踪调试


prompt = "孤独摇滚?"
table = {
    "search": [
        "https://www.bihu.com/search?type=content&q={}"
    ]
}
plugins = ["search"]
# Exec
result = test_plugin(prompt=prompt, table=table, plugins=plugins)
print(result)
