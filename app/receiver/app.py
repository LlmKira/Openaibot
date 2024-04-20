# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

__area__ = "receiver"


# import nest_asyncio
# nest_asyncio.apply()


def run():
    import asyncio
    from .aps import aps_start
    from .function import FunctionReceiver
    from llmkira import (
        load_plugins,
        load_from_entrypoint,
        get_entrypoint_plugins,
    )
    from app.setting import PlatformSetting

    start_setting = PlatformSetting.from_subdir()
    func = [
        aps_start(),
        FunctionReceiver().function(),
    ]

    if start_setting.telegram:
        from .telegram import TelegramReceiver

        func.append(TelegramReceiver().telegram())
    if start_setting.discord:
        from .discord import DiscordReceiver

        func.append(DiscordReceiver().discord())
    if start_setting.kook:
        from .kook import KookReceiver

        func.append(KookReceiver().kook())
    if start_setting.slack:
        from .slack import SlackReceiver

        func.append(SlackReceiver().slack())

    async def _main(_func):
        await asyncio.gather(*_func)

    # 导入插件
    load_plugins("llmkira/extra/plugins")
    load_from_entrypoint("llmkira.extra.plugin")
    import llmkira.extra.voice_hook  # noqa

    loaded_message = "\n >>".join(get_entrypoint_plugins())
    logger.success(
        f"\n===========Third Party Plugins Loaded==========\n >>{loaded_message}"
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(func))
