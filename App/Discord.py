# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github: sudoskys

import asyncio

from discord.ext import commands
from loguru import logger


class BotRunner:
    def __init__(self, _config):
        self.config = _config
        self.bot = None

    def botCreate(self):
        if not self.config.botToken:
            return None
        bot = commands.Bot(command_prefix=self.config.prefix)

        # Add command handlers here
        @bot.command(name='ping')
        async def ping(ctx):
            await ctx.send('Pong!')

        return bot

    def run(self):
        self.bot = self.botCreate()
        if not self.bot:
            logger.info("Discord Bot Close")
            return None

        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user.name} has connected to Discord!')

        @self.bot.event
        async def on_message(message):
            # Check if the message was sent by a bot
            if message.author.bot:
                return None

            # Ignore all messages that are not from the bot
            if message.author != self.bot.user:
                return None
            # Handle private messages
            if not message.guild:
                # Do something with the private message
                pass
            else:
                # Handle group messages
                # Do something with the group message
                pass

        async def main():
            self.bot.run(self.config.token)

        asyncio.run(main())
