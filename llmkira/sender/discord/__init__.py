# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 下午10:22
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import crescent
import hikari
from hikari import Message
from hikari.impl import ProxySettings
from loguru import logger

from llmkira.setting.discord import BotSetting
from llmkira.task import Task, TaskHeader
from llmkira.transducer import TransferManager
from ..schema import Runner

__sender__ = "discord"
__default_function_enable__ = True

from ..util_func import is_command

DiscordTask = Task(queue=__sender__)


class DiscordBotRunner(Runner):

    def __init__(self):
        self.bot = None
        self.proxy = None

    async def upload(self, *args, **kwargs):
        pass

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:Discord Setting not available")
            return None
        self.bot = hikari.GatewayBot(
            token=BotSetting.token,
            proxy_settings=ProxySettings(
                url=BotSetting.proxy_address
            ) if BotSetting.proxy_address else None
        )
        self.proxy = BotSetting.proxy_address
        # prepare
        bot = self.bot
        client = crescent.Client(bot)

        # TODO FILE UPLOADER

        # Task Creator
        async def create_task(message: Message, funtion_enable: bool = False):
            _file = []
            if message.content:
                message.content = message.content.lstrip("/chat").lstrip("/task")
            message.content = message.content if message.content else ""
            logger.info(
                f"discord:create task from {message.channel_id} {message.content[:300]} funtion_enable:{funtion_enable}"
            )
            # 任务构建
            try:
                # 转析器
                _transfer = TransferManager().sender_parser(agent_name=__sender__)
                deliver_back_message, _file = _transfer().parse(message=message, file=_file)
                # Reply
                success, logs = await DiscordTask.send_task(
                    task=TaskHeader.from_discord(
                        message,
                        file=_file,
                        deliver_back_message=deliver_back_message,
                        task_meta=TaskHeader.Meta(function_enable=funtion_enable, sign_as=(0, "root", "discord")),
                        trace_back_message=[]
                    )
                )
                if not success:
                    pass
            except Exception as e:
                logger.exception(e)

        def tool_message():

            _tool = ToolRegister().functions
            _paper = [[c.name, c.description] for name, c in _tool.items()]
            arg = [
                formatting.mbold(item[0]) +
                formatting.mbold(" - ") +
                formatting.mitalic(item[1])
                for item in _paper
            ]
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🔧 Tool List"),
                    *arg,
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.listen()
        async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
            if not event.is_human:
                return
            print(event.channel_id.)
            if event.content == "!ping":
                await event.message.respond(f"Pong! {bot.heartbeat_latency * 1_000:.0f}ms")
            await create_task(event.message)
            print(event)

        @bot.listen()
        async def on_message(event: hikari.DMMessageCreateEvent) -> None:
            if not event.is_human:
                return
            if is_command(text=message.text, command="/tool"):
                print(event.channel_id)
            if event.content == "!ping":
                await event.message.respond(f"Pong! {bot.heartbeat_latency * 1_000:.0f}ms")
            await create_task(event.message)
            print(event)

        bot.run()
