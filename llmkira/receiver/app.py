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
    from .aps import aps_start
    from .function import FunctionReceiver

    func = [
        aps_start(),
        FunctionReceiver().function(),
    ]

    from llmkira.sdk.func_calling import load_plugins, load_from_entrypoint, get_entrypoint_plugins

    from llmkira.setting import StartSetting
    start_setting = StartSetting.from_subdir()
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
        await asyncio.gather(
            *_func
        )

    # 导入插件
    load_plugins("llmkira/extra/plugins")
    load_from_entrypoint("llmkira.extra.plugin")

    loaded_message = "\n >>".join(get_entrypoint_plugins())
    logger.success(f"\n===========Third Party Plugins Loaded==========\n >>{loaded_message}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(func))
