# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio
import sys

from loguru import logger

import plugins
from .aps import aps_start
from .function import FunctionReceiver
from .telegram import TelegramReceiver

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True
           )
__area__ = "receiver"
func = [
    aps_start(),
    FunctionReceiver().function(),
    TelegramReceiver().telegram()
]

# 初始化插件系统
plugins.setup()


async def _main():
    await asyncio.gather(
        *func
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(_main())
