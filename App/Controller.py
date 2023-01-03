# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio
import pathlib
import time
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telebot import util, types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from App import Event
from utils import Setting
from utils.Chat import Utils
from utils.Data import DefaultData, User_Message, create_message, PublicReturn

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
    tick_scheduler.add_job(funcs, trigger='interval', max_instances=10, seconds=second)
    tick_scheduler.start()


def get_message(message: types.Message):
    # 自动获取名字
    first_name = message.from_user.first_name if message.from_user.first_name else ""
    last_name = message.from_user.last_name if message.from_user.last_name else ""
    _name = f"{first_name}{last_name}"
    if len(_name) > 12 and len(f"{last_name}") < 6:
        _name = f"{last_name}"
    group_name = message.chat.title if message.chat.title else message.chat.last_name
    group_name = group_name if group_name else "Group"
    return create_message(user_id=message.from_user.id,
                          user_name=_name,
                          group_id=message.chat.id,
                          text=message.text,
                          group_name=group_name
                          )


class BotRunner(object):
    def __init__(self, config):
        self.bot = config.bot
        self.proxy = config.proxy

    def botCreate(self):
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self):
        # print(self.bot)
        logger.success("APP:Bot Start")
        bot, _config = self.botCreate()
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            logger.info("USE PROXY！")

        # 私聊起动机
        @bot.message_handler(commands=["start", 'about', "help"], chat_types=['private'])
        async def handle_command(message):
            if "/start" in message.text:
                await bot.reply_to(message, await Event.Start(_config))
            elif "/about" in message.text:
                await bot.reply_to(message, await Event.About(_config))
            elif "/help" in message.text:
                await bot.reply_to(message, await Event.Help(_config))

        # 群聊
        @bot.message_handler(content_types=['text'], chat_types=['supergroup', 'group'])
        async def group_msg(message):
            _hand = get_message(message)
            _hand: User_Message
            request_timestamps.append(time.time())
            started = False
            if message.text.startswith(("/chat", "/voice", "/write", "/forgetme", "/remind")):
                started = True
            if message.reply_to_message:
                if message.reply_to_message.from_user.id == Setting.bot_profile()["id"]:
                    if str(Utils.checkMsg(
                            f"{message.chat.id}{message.reply_to_message.id}")) == f"{message.from_user.id}":
                        started = True
            # 分发指令
            if message.text.startswith("/help"):
                await bot.reply_to(message, await Event.Help(_config))
            if started:
                _friends_message = await Event.Text(_hand, _config)
                _friends_message: PublicReturn
                if _friends_message.status:
                    if _friends_message.type == "Reply":
                        _type = _friends_message.data.get("type")
                        _caption = f"{_friends_message.data.get('text')}\n{_friends_message.data.get('msg')}\n{_config.INTRO}"
                        if _type == "voice":
                            msg = await bot.send_voice(chat_id=message.chat.id,
                                                       reply_to_message_id=message.id,
                                                       voice=_friends_message.data.get("voice"),
                                                       caption=_caption
                                                       )
                            Utils.trackMsg(f"{message.chat.id}{msg.id}", user_id=message.from_user.id)
                        elif _type == "text":
                            msg = await bot.reply_to(message, _caption)
                            Utils.trackMsg(f"{message.chat.id}{msg.id}", user_id=message.from_user.id)
                    else:
                        msg = await bot.reply_to(message, _friends_message.msg)
                        Utils.trackMsg(f"{message.chat.id}{msg.id}", user_id=message.from_user.id)

        # 私聊
        @bot.message_handler(content_types=['text'], chat_types=['private'])
        async def handle_private_msg(message):
            _hand = get_message(message)
            _hand: User_Message
            request_timestamps.append(time.time())
            if not _hand.text.startswith("/"):
                _hand.text = f"/chat {_hand.text}"
            # 交谈
            if _hand.text.startswith(
                    ("/chat", "/voice", "/write", "/forgetme", "/remind")):
                _friends_message = await Event.Friends(_hand, _config)
                _friends_message: PublicReturn
                if _friends_message.status:
                    if _friends_message.type == "Reply":
                        _type = _friends_message.data.get("type")
                        _caption = f"{_friends_message.data.get('text')}\n{_friends_message.data.get('msg')}\n{_config.INTRO}"
                        if _type == "voice":
                            await bot.send_voice(chat_id=message.chat.id,
                                                 reply_to_message_id=message.id,
                                                 voice=_friends_message.data.get("voice"),
                                                 caption=_caption
                                                 )
                        elif _type == "text":
                            await bot.reply_to(message, _caption)
                    else:
                        await bot.reply_to(message, _friends_message.msg)
            # 检查管理员指令
            if message.from_user.id in _config.master:
                _reply = await Event.MasterCommand(Message=_hand, config=_config)
                # 检查管理员指令
                if _hand.text == "/config":
                    path = str(pathlib.Path().cwd()) + "/" + "Config/config.json"
                    if pathlib.Path(path).exists():
                        doc = open(path, 'rb')
                        await bot.send_document(message.chat.id, doc)
                    else:
                        _reply.append("没有找到配置文件")
                if _reply:
                    await bot.reply_to(message, "".join(_reply))

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
            await Setting.bot_profile_init(bot)
            await asyncio.gather(
                bot.polling(non_stop=True, allowed_updates=util.update_types),
                set_cron(get_request_frequency, second=4)
            )

        asyncio.run(main())
