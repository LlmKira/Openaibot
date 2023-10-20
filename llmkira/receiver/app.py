# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio
import os
import sys

from dotenv import load_dotenv
from llmkira.receiver.telegram import TelegramReceiver
from loguru import logger

from llmkira.sdk.func_calling import load_plugins, load_from_entrypoint, get_entrypoint_plugins
from .aps import aps_start
from .discord import DiscordReceiver
from .function import FunctionReceiver
from .kook import KookReceiver

load_dotenv()
logger.remove()
logger.add(sys.stderr,
           level="INFO" if os.getenv("LLMBOT_LOG_OUTPUT") != "DEBUG" else "DEBUG",
           colorize=True,
           enqueue=True
           )

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
    TelegramReceiver().telegram(),
    DiscordReceiver().discord(),
    KookReceiver().kook(),
]

# 导入插件
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
