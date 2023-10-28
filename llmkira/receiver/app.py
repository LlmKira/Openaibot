# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

__area__ = "receiver"


def run():
    import asyncio

    from llmkira.receiver.telegram import TelegramReceiver
    from llmkira.sdk.func_calling import load_plugins, load_from_entrypoint, get_entrypoint_plugins
    from .aps import aps_start
    from .discord import DiscordReceiver
    from .function import FunctionReceiver
    from .kook import KookReceiver
    from .slack import SlackReceiver

    func = [
        aps_start(),
        FunctionReceiver().function(),
        TelegramReceiver().telegram(),
        DiscordReceiver().discord(),
        KookReceiver().kook(),
        SlackReceiver().slack(),
    ]

    async def _main():
        await asyncio.gather(
            *func
        )

    # 导入插件
    load_plugins("llmkira/extra/plugins")
    load_from_entrypoint("llmkira.extra.plugin")

    loaded_message = "\n >>".join(get_entrypoint_plugins())
    logger.success(f"\n===========Third Party Plugins Loaded==========\n >>{loaded_message}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main())
