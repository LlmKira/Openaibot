# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio
import pathlib
import telebot

from App import Event
from utils.Base import Tool
from telebot import types, util
from utils.Logging import logCreate
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage


class BotRunner(object):
    def __init__(self, config):
        self.bot = config.bot
        self.proxy = config.proxy

    def botCreate(self):
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self):
        # print(self.bot)
        logCreate().info("Bot Start")
        bot, _config = self.botCreate()
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            print("正在使用隧道！")

        @bot.message_handler(commands=["start", 'about'], chat_types=['private'])
        async def handle_command(message):
            if "/start" in message.text:
                await Event.Start(bot, message, _config)
            elif "/about" in message.text:
                await Event.About(bot, message, _config)

        @bot.message_handler(commands=["chat"], chat_types=['supergroup', 'group'])
        async def group_msg_no_admin(message):
            await Event.Text(bot, message, _config)

        # 私聊事件捕获
        @bot.message_handler(content_types=['text'], chat_types=['private'])
        async def handle_private_msg(message):
            await Event.Master(bot, message, _config)

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        async def main():
            await asyncio.gather(bot.polling(non_stop=True, allowed_updates=util.update_types))

        asyncio.run(main())
