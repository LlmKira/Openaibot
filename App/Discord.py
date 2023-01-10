# -*- coding: utf-8 -*-
# @Time    : 1/9/23 10:59 PM
# @FileName: Discord.py
# @Software: PyCharm
# @Github    ：sudoskys

import asyncio
import pathlib
import time
from collections import deque

from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from App import Event
from utils import Setting
from utils.Chat import Utils
from utils.Frequency import Vitality
from utils.Data import DefaultData, User_Message, create_message, PublicReturn

import discord
from discord.ext import commands

time_interval = 60
# 使用 deque 存储请求时间戳
request_timestamps = deque()


def get_message(message):
    # 自动获取名字
    first_name = message.from_user.first_name if message.from_user.first_name else ""
    last_name = message.from_user.last_name if message.from_user.last_name else ""
    _name = f"{first_name}{last_name}"
    if len(_name) > 12 and len(f"{last_name}") < 6:
        _name = f"{last_name}"
    group_name = message.chat.title if message.chat.title else message.chat.last_name
    group_name = group_name if group_name else "Group"
    return create_message(
        state=102,
        user_id=message.from_user.id,
        user_name=_name,
        group_id=message.chat.id,
        text=message.text,
        group_name=group_name
    )


class BotRunner(object):
    def __init__(self, config):
        self.config = config
        self.proxy = config.proxy

    def botCreate(self):
        if not self.config.botToken:
            return None
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='>', intents=intents)
        return bot

    def run(self, pLock=None):
        # print(self.bot)
        bot, _ = self.botCreate()
        if not bot:
            logger.info("Controller:Discord Bot Close")
            return
        logger.success("Controller:Discord Bot Start")

        @bot.command(name="")
        async def ping(ctx):
            await ctx.send('pong')

        bot.run(self.config.botToken)
