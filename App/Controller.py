# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio
import time
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telebot import util
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from App import Event
from utils.Data import DefaultData

global me_id

time_interval = 60
# 使用 deque 存储请求时间戳
request_timestamps = deque()


async def set_cron(funcs, second: int):
    """
    启动一个异步定时器
    :param funcs: 回调函数
    :param second: 秒数
    :return:
    """
    tick_scheduler = AsyncIOScheduler()
    tick_scheduler.add_job(funcs, 'interval', seconds=second)
    tick_scheduler.start()


class BotRunner(object):
    def __init__(self, config):
        self.bot = config.bot
        self.proxy = config.proxy

    def botCreate(self):
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self):
        # print(self.bot)
        logger.info("APP:Bot Start")
        bot, _config = self.botCreate()
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            print("USE PROXY！")

        # 私聊起动机
        @bot.message_handler(commands=["start", 'about'], chat_types=['private'])
        async def handle_command(message):
            if "/start" in message.text:
                await Event.Start(bot, message, _config)
            elif "/about" in message.text:
                await Event.About(bot, message, _config)

        # 群聊
        @bot.message_handler(chat_types=['supergroup', 'group'])
        async def group_msg_no_admin(message):
            global me_id
            if message.text.startswith("/chat") or message.text.startswith("/write") or message.text.startswith(
                    "/remind"):
                await Event.Text(bot, message, _config, reset=True)
                request_timestamps.append(time.time())
            else:
                if message.reply_to_message:
                    if message.reply_to_message.from_user.id == me_id:
                        await Event.Text(bot, message, _config, reset=False)
                        request_timestamps.append(time.time())
            return

        # 私聊
        @bot.message_handler(content_types=['text'], chat_types=['private'])
        async def handle_private_msg(message):
            if message.from_user.id in _config.master:
                await Event.Master(bot, message, _config)
            if message.text.startswith("/chat") or not message.text.startswith("/") or message.text.startswith(
                    "/remind"):
                await Event.Friends(bot, message, _config)
            request_timestamps.append(time.time())

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        def get_request_frequency():
            # 检查队列头部是否过期
            while request_timestamps and request_timestamps[0] < time.time() - time_interval:
                request_timestamps.popleft()
            # 计算请求频率
            request_frequency = len(request_timestamps)
            DefaultData().setAnalysis(frequency=request_frequency)
            return request_frequency

        async def main():
            global me_id
            _me = await bot.get_me()
            me_id = _me.id
            logger.info(f"Init Bot id:{me_id}")
            await asyncio.gather(
                bot.polling(non_stop=True, allowed_updates=util.update_types),
                set_cron(get_request_frequency, second=4)
            )

        asyncio.run(main())
