import asyncio
import json
import pathlib
import tzlocal
import tempfile
import time
from collections import deque
from typing import Optional, Union, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from App import Event
from utils import Setting, Sticker
from utils.Blip import BlipServer, FileReader
from utils.Chat import Utils, PhotoRecordUtils, ConfigUtils
from utils.Data import DefaultData, User_Message, create_message, PublicReturn, Service_Data
from utils.Frequency import Vitality

from nakuru import (
    CQHTTP,
    GroupMessage,
    FriendMessage,
    FriendRequest
)
from nakuru.entities.components import Plain

_service = Service_Data.get_key()

class BotRunner(object):
    def __init__(self, config):
        self.bot = config
        self.proxy = config.proxy
    def botCreate(self):
        if not all([self.bot.host, self.bot.port, self.bot.http_port]):
            logger.error('QQ Bot parameters insufficient, not starting!')
            return
        bot = CQHTTP(host=self.bot.host,
                     port=self.bot.port,
                     http_port=self.bot.http_port,
                     token=self.bot.token)
        if not bot:
            logger.error('Failed to start QQ bot!')
            return
        return bot, self.bot
    async def universalHandler(self, app: CQHTTP, source: Union[FriendMessage, GroupMessage]):
        target = 'Group' if isinstance(source, GroupMessage) else 'Friend'
        fromID = source.group_id if hasattr(source, 'group_id') else source.user_id
        sendFunc = getattr(app, f'send{target}Message') # call app.send[Group/Friend]Message by sendFunc
        
        if source.raw_message.startswith('/start'):
            sendFunc(fromID, await Event.Start())
            return
        elif source.raw_message.startswith('/help'):
            sendFunc(fromID, await Event.Help())
            return
        elif source.raw_message.startswith('/about'):
            sendFunc(fromID, await Event.About())
            return
        
        # -----build message info-----
        messageObject = create_message(
            user_id=source.user_id,
            user_name=source.sender.nickname,
            group_id=source.group_id if target == 'Group' else source.user_id,
            text=source.raw_message,
            state=101
        )
        # TODO
    def run(self):
        bot, _config = self.botCreate()
        @bot.receiver("GroupMessage")
        async def _(app: CQHTTP, source: GroupMessage):
            await self.universalHandler(app, source)
        @bot.receiver("FriendMessage")
        async def _(app: CQHTTP, source: FriendMessage):
            await self.universalHandler(app, source)
        @bot.receiver("FriendRequest")
        async def _(app: CQHTTP, source: FriendRequest):
            if(self.bot.autoAcceptNewFriend):
                await app.setFriendRequest(source.flag, True)