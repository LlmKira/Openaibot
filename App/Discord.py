# -*- coding: utf-8 -*-
# @Time    : 1/9/23 10:59 PM
# @FileName: Discord.py
# @Software: PyCharm
# @Github    ：sudoskys

########
# ONGOING
# https://github.com/Rapptz/discord.py
########

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

lock = None


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


class MyClient(discord.Client):
    async def on_ready(self):
        logger.info(f'Discord:Logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!hello'):
            await message.reply('Hello!', mention_author=True)


class BotRunner(object):
    def __init__(self, config):
        self.config = config
        self.proxy = config.proxy

    def botCreate(self):
        if not self.config.botToken:
            return None

        intents = discord.Intents.default()
        intents.message_content = True
        client = MyClient(intents=intents)
        return client, self.config.botToken

    def run(self, pLock=None):
        global lock
        # print(self.bot)
        client, token = self.botCreate()
        if not client:
            logger.info("Controller:Discord Bot Close")
            return
        logger.success("Controller:Discord Bot Start")
        lock = pLock
        client.run(token)
