# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:18
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio
import os
import sys

from dotenv import load_dotenv
from llmkira import load_plugins
from llmkira.sdk.func_calling import load_from_entrypoint, get_entrypoint_plugins
from loguru import logger

from .rss import RssApp
from .telegram import TelegramBotRunner

load_dotenv()
logger.remove()
handler_id = logger.add(sys.stderr,
                        level="INFO" if os.getenv("LLMBOT_LOG_OUTPUT") != "DEBUG" else "DEBUG",
                        enqueue=True
                        )
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
load_plugins("llmkira/extra/plugins")
load_from_entrypoint("llmkira.extra.plugin")

loaded_message = "\n >>".join(get_entrypoint_plugins())
logger.success(f"\n===========Third Party Plugins Loaded==========\n >>{loaded_message}")


async def _main():
    await asyncio.gather(
        *func
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(_main())
