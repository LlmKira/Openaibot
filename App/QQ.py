# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github: purofle
import asyncio
import time
from collections import deque
from typing import Union, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from graia.amnesia.message import MessageChain
from graia.ariadne.connection.config import config, HttpClientConfig, WebsocketClientConfig
from graia.ariadne.message import Source, Quote
from graia.ariadne.message.element import Voice, Plain
from graia.ariadne.message.parser.twilight import UnionMatch
from graia.ariadne.model import Group, Member, Friend, MemberPerm
from graia.ariadne import Ariadne
from graia.ariadne.model import Profile
from graiax import silkcoder
from loguru import logger

from App import Event
from utils import Setting
from utils.Chat import Utils
from utils.Data import create_message, User_Message, PublicReturn, DefaultData
from utils.Frequency import Vitality


time_interval = 60 * 5
# 使用 deque 存储请求时间戳
request_timestamps = deque()
ProfileManager = Setting.ProfileManager()


def get_user_message(
        message: MessageChain,
        member: Union[Member, Friend],
        group: Optional[Group] = None) -> User_Message:
    return create_message(
        state=101,
        user_id=member.id,  # qq 号
        user_name=member.name if isinstance(member, Member) else member.nickname,
        group_id=group.id if group else member.id,
        text=str(message),
        group_name=group.name if group else "Group"
    )


class BotRunner:
    def __init__(self, _config):
        self.config = _config

    def botCreate(self):
        if not self.config.verify_key:
            return None
        return Ariadne(config(self.config.account, self.config.verify_key, HttpClientConfig(host=self.config.http_host),
                              WebsocketClientConfig(host=self.config.ws_host)))

    def run(self, pLock=None):
        bot = self.botCreate()
        if not bot:
            logger.info("APP:QQ Bot Close")
            return None
        logger.success("APP:QQ Bot Start")

        @bot.broadcast.receiver("FriendMessage", dispatchers=[UnionMatch("/about", "/start", "/help")])
        async def starter(app: Ariadne, message: MessageChain, friend: Friend, source: Source):
            logger.info(message.content)
            message = str(message)
            if message == "/about":
                await app.send_message(friend, await Event.About(self.config), quote=source)
            elif message == "/start":
                await app.send_message(friend, await Event.Start(self.config), quote=source)
            elif message == "/help":
                await app.send_message(friend, await Event.Help(self.config), quote=source)

        async def get_message_chain(_hand: User_Message):
            request_timestamps.append(time.time())

            if not _hand.text.startswith("/"):
                _hand.text = f"/chat {_hand.text}"
            # _friends_message = await Event.Text(_hand, self.config)
            _friends_message = await Event.Friends(Message=_hand,
                                                   bot_profile=ProfileManager.access_qq(init=False),
                                                   config=self.config
                                                   )

            if not _friends_message.status:
                return None

            _caption = f"{_friends_message.reply}\n{self.config.INTRO}"
            if _friends_message.voice:
                # 转换格式
                voice = await silkcoder.async_encode(_friends_message.voice, audio_format="ogg")
                message_chain = MessageChain([Voice(data_bytes=voice)])
            elif _friends_message.reply:
                message_chain = MessageChain([Plain(_caption)])
            else:
                message_chain = MessageChain([Plain(_friends_message.msg)])
            return message_chain

        # "msg" @ RegexMatch(r"\/\b(chat|voice|write|forgetme|remind)\b.*")
        @bot.broadcast.receiver("AccountLaunch")
        async def initAccount():
            _me: Profile = await bot.get_bot_profile()
            _name = _me.nickname
            _bot_profile = {"id": bot.account, "name": _name}
            ProfileManager.access_qq(bot_name=_name, bot_id=bot.account, init=True)

        @bot.broadcast.receiver("FriendMessage")
        async def chat(app: Ariadne, msg: MessageChain, friend: Friend, source: Source):
            _hand = get_user_message(msg, member=friend, group=None)
            _read_id = friend.id
            if _read_id in self.config.master:
                _reply = await Event.MasterCommand(user_id=_read_id, Message=_hand, config=self.config, pLock=pLock)
                if _reply:
                    await app.send_message(friend, "".join(_reply), quote=source)

            message_chain = await get_message_chain(_hand)
            if message_chain:
                active_msg = await app.send_message(friend, message_chain, quote=source)
                # Utils.trackMsg(f"{_hand.from_chat.id}{active_msg.id}", user_id=_hand.from_user.id)

        @bot.broadcast.receiver("GroupMessage")
        async def group_chat(app: Ariadne,
                             msg: MessageChain,
                             quote: Optional[Quote],
                             member: Member,
                             group: Group,
                             source: Source):
            _hand = get_user_message(msg, member=member, group=group)
            _hand: User_Message
            _at_me = f'@{bot.account} '
            get_request_frequency()
            started = False
            if _hand.text.startswith(("/chat", "/voice", "/write", "/style", "/forgetme", "/remind")):
                started = True
            elif _hand.text.startswith("/"):
                _is_admin = member.permission
                if _is_admin in [MemberPerm.Owner, MemberPerm.Administrator]:
                    _reply = await Event.GroupAdminCommand(Message=_hand, config=self.config, pLock=pLock)
                    if _reply:
                        message_chain = MessageChain([Plain("".join(_reply))])
                        await app.send_message(group, message_chain, quote=source)
            elif _hand.text.startswith(_at_me):
                started = True
                p1 = _hand.text.index('@')
                p2 = _hand.text.index(' ') + 1
                t = _hand.text[p1:p2]
                _hand.text = _hand.text.replace(t, '/chat ')

            if quote:
                if str(Utils.checkMsg(
                        f"QQ{quote.group_id}101{quote.id}")) == f"{_hand.from_user.id}":
                    if not _hand.text.startswith("/"):
                        _hand.text = f"/chat {_hand.text}"
                    started = True
                    if _hand.text.startswith('@'):  # 去除QQ回复时的自动at
                        p1 = _hand.text.index('@')
                        p2 = _hand.text.index(' ') + 1
                        t = _hand.text[p1:p2]
                        _hand.text = _hand.text.replace(t, '')

            # 分发指令
            if _hand.text.startswith("/help"):
                await bot.send_message(group, await Event.Help(self.config))
            # logger.warning(started)
            # 热力扳机
            if not started:
                try:
                    _trigger_message = await Event.Trigger(_hand, self.config)
                    if _trigger_message.status:
                        _GroupTrigger = Vitality(group_id=_hand.from_chat.id)
                        _GroupTrigger.trigger(Message=_hand, config=self.config)
                        _check = _GroupTrigger.check(Message=_hand)
                        if _check:
                            _hand.text = f"/catch {_hand.text}"
                            started = True
                except Exception as e:
                    logger.warning(
                        f"{e}\nThis is a trigger Error,may [trigger] typo [tigger],try to check your config?")

            if started:
                request_timestamps.append(time.time())
                _friends_message = await Event.Group(Message=_hand,
                                                     bot_profile=ProfileManager.access_qq(init=False),
                                                     config=self.config
                                                     )
                _friends_message: PublicReturn

                _caption = f"{_friends_message.reply}\n{self.config.INTRO}"
                if _friends_message.voice:
                    # 转换格式
                    voice = await silkcoder.async_encode(_friends_message.voice, audio_format="ogg")
                    message_chain = MessageChain([Voice(data_bytes=voice)])
                elif _friends_message.reply:
                    message_chain = MessageChain([Plain(_caption)])
                else:
                    message_chain = MessageChain([Plain(_friends_message.msg)])
                if message_chain:
                    active_msg = await app.send_message(group, message_chain, quote=source)
                    Utils.trackMsg(f"QQ{_hand.from_chat.id}{active_msg.id}", user_id=_hand.from_user.id)

        def get_request_frequency():
            # 检查队列头部是否过期
            while request_timestamps and request_timestamps[0] < time.time() - time_interval:
                request_timestamps.popleft()
            # 计算请求频率
            request_frequency = len(request_timestamps)
            DefaultData().setAnalysis(qq=request_frequency)
            return request_frequency

        Ariadne.launch_blocking()
