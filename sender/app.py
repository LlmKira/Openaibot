# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:18
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio
import sys

from loguru import logger

import plugins
from .rss import RssApp
from .telegram import TelegramBotRunner

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True
           )

__area__ = "sender"

# 注册机器人事件
telegram_bot = TelegramBotRunner().telegram()
rss_app = RssApp()

func = [
    telegram_bot,
    rss_app.rss_polling(interval=60 * 60 * 1),
]

# 初始化插件系统
plugins.setup()


async def _main():
    await asyncio.gather(
        *func
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(_main())
