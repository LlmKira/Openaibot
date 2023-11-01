# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:18
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
__area__ = "sender"


def run():
    import asyncio

    from llmkira import load_plugins
    from llmkira.sdk import load_from_entrypoint, get_entrypoint_plugins
    from llmkira.setting import StartSetting
    from .rss import RssAppRunner

    start_setting = StartSetting.from_subdir()
    wait_list = [RssAppRunner().run(interval=60 * 60 * 1)]
    if start_setting.telegram:
        from .telegram import TelegramBotRunner
        wait_list.append(TelegramBotRunner().run())
    if start_setting.discord:
        from .discord import DiscordBotRunner
        wait_list.append(DiscordBotRunner().run())
    if start_setting.kook:
        from .kook import KookBotRunner
        wait_list.append(KookBotRunner().run())
    if start_setting.slack:
        from .slack import SlackBotRunner
        wait_list.append(SlackBotRunner().run())

    # 初始化插件系统
    load_plugins("llmkira/extra/plugins")
    load_from_entrypoint("llmkira.extra.plugin")

    loaded_message = "\n >>".join(get_entrypoint_plugins())
    logger.success(f"\n===========Third Party Plugins Loaded==========\n >>{loaded_message}")

    async def _main(wait_list_):
        await asyncio.gather(
            *wait_list_
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(wait_list_=wait_list))
