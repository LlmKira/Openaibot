# -*- coding: utf-8 -*-
# @Time    : 2/10/23 12:01 PM
# @FileName: Discord.py
# @Software: PyCharm
# @Github    ：sudoskys

########
# ONGOING
# https://github.com/nextcord/nextcord/tree/v2.3.2/examples
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
import nextcord
from nextcord.ext import commands

time_interval = 60
# 使用 deque 存储请求时间戳
request_timestamps = deque()

lock = None


def get_message(message: nextcord.Message):
    # 自动获取名字
    first_name = message.from_user.first_name if message.from_user.first_name else ""
    last_name = message.from_user.last_name if message.from_user.last_name else ""
    _name = f"{first_name}{last_name}"
    if len(_name) > 12 and len(f"{last_name}") < 6:
        _name = f"{last_name}"
    group_name = message.chat.title if message.chat.title else message.chat.last_name
    group_name = group_name if group_name else "Group"
    return create_message(
        state=104,
        user_id=message.from_user.id,
        user_name=_name,
        group_id=message.chat.id,
        text=message.text,
        group_name=group_name
    )


class BotClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        intents = nextcord.Intents.default()
        client = BotClient(command_prefix="/", intents=intents)
        return client, self.config.botToken

    def run(self, pLock=None):
        global lock
        # print(self.bot)
        client, token = self.botCreate()
        if not client:
            logger.info("Controller:Discord Bot Close")
            return
        lock = pLock

        client.run(token)
