# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Controller.py.py
# @Software: PyCharm
# @Github: sudoskys

import asyncio
import pathlib
import tempfile
import time
from collections import deque
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telebot import util, types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from App import Event
from utils import Setting, Blip
from utils.Chat import Utils, PhotoRecordUtils
from utils.Data import DefaultData, User_Message, create_message, PublicReturn, Service_Data
from utils.Frequency import Vitality

from PIL import Image

# from utils.Base import Tool

_service = Service_Data.get_key()
BLIP_CONF = _service["media"]["blip"]

if BLIP_CONF.get("status"):
    BlipModel = BLIP_CONF.get("model")
    if BlipModel not in ['large', 'base']:
        BlipModel = 'large'
    BlipConfig = Blip.Config()
    BlipConfig.model = BlipModel
    BlipInterrogator = Blip.Interrogator(BlipConfig)
else:
    BlipInterrogator = None

TIME_INTERVAL = 60
# 使用 deque 存储请求时间戳
request_timestamps = deque()
ProfileManager = Setting.ProfileManager()


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


async def recognize_photo(bot: AsyncTeleBot, photo: types.PhotoSize) -> Optional[str]:
    _file_info = await bot.get_file(photo.file_id)
    _history = PhotoRecordUtils.getKey(_file_info.file_unique_id)
    if _history:
        return _history
    if _file_info.file_size > 10485760:
        return "Too Large Photo"
    downloaded_file = await bot.download_file(_file_info.file_path)
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        f.write(downloaded_file)
        f.flush()
        image_pil = Image.open(f.name).convert('RGB')
    if downloaded_file:
        BlipInterrogatorText = BlipInterrogator.generate_caption(
            pil_image=image_pil)
        if BlipInterrogatorText:
            PhotoRecordUtils.setKey(_file_info.file_unique_id, BlipInterrogatorText)
        return BlipInterrogatorText
    return None


async def get_message(bot: AsyncTeleBot, message: types.Message):
    # 自动获取名字
    msg_text = ""
    if message:
        msg_text = message.text
    if message.photo and BlipInterrogator:
        # TODO
        logger.warning('photo')
        msg_text = message.caption
        # RECOGNIZE File
        photo_text = recognize_photo(bot=bot, photo=message.photo[-1])
        if photo_text:
            BlipInterrogatorText = f"![PHOTO|{photo_text}]\n{message.caption}"
            msg_text = f"{BlipInterrogatorText}"
    if message.sticker:
        # TODO
        msg_text = message.sticker.emoji
        logger.warning(message.json)
    logger.warning(msg_text)
    prompt = [msg_text]
    _name = message.from_user.full_name
    group_name = message.chat.title if message.chat.title else message.chat.first_name
    group_name = group_name if group_name else "Group"
    return create_message(
        state=100,
        user_id=message.from_user.id,
        user_name=_name,
        group_id=message.chat.id,
        text=msg_text,
        prompt=prompt,
        group_name=group_name,
    )


class BotRunner(object):
    def __init__(self, config):
        self.bot = config
        self.proxy = config.proxy

    def botCreate(self):
        if not self.bot.botToken:
            return None, None
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self, pLock=None):
        # print(self.bot)
        bot, _config = self.botCreate()
        if not bot:
            logger.info("APP:Telegram Bot Close")
            return
        logger.success("APP:Telegram Bot Start")
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            logger.info("Telegram Bot Using proxy!")

        # 管理员权限
        async def is_admin(message: types.Message):
            _got = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return _got.status in ['administrator', 'creator']

        # 私聊起动机
        @bot.message_handler(commands=["start", 'about', "help"], chat_types=['private'])
        async def handle_command(message):
            _hand = await get_message(bot, message)
            _hand: User_Message
            if "/start" in _hand.text:
                await bot.reply_to(message, await Event.Start(_config))
            elif "/about" in _hand.text:
                await bot.reply_to(message, await Event.About(_config))
            elif "/help" in _hand.text:
                await bot.reply_to(message, await Event.Help(_config))

        # 群聊
        @bot.message_handler(content_types=['text', 'sticker', 'photo'], chat_types=['supergroup', 'group'])
        async def group_msg(message):
            _hand = await get_message(bot, message)
            _hand: User_Message
            started = False

            # 回复逻辑判定
            if message.reply_to_message:
                _name = message.reply_to_message.from_user.full_name
                _name = DefaultData.name_split(sentence=_name, limit=16)
                _text = str(message.reply_to_message.text)
                _text = _text.replace(_config.INTRO, "")
                if f"{message.reply_to_message.from_user.id}" == f"{Setting.ProfileManager().access_telegram(init=False).bot_id}":
                    # Chat
                    if not _hand.text.startswith("/"):
                        _hand.text = f"/chat {_hand.text}"
                    started = True
                    if str(Utils.checkMsg(
                            f"{_hand.from_chat.id}{message.reply_to_message.id}")) == f"{_hand.from_user.id}":
                        pass
                    else:
                        _hand.prompt.append(f"{_name}:{_text}")
                else:
                    _hand.prompt.append(f"{_name}:{_text}")

            # 命令解析
            if _hand.text.startswith(("/chat", "/voice", "/write", "/forgetme", "/style", "/remind")):
                started = True
            elif _hand.text.startswith("/"):
                _is_admin = await is_admin(message)
                if _is_admin:
                    _reply = await Event.GroupAdminCommand(Message=_hand, config=_config, pLock=pLock)
                    if _reply:
                        await bot.reply_to(message, "".join(_reply))

            # 分发指令
            if _hand.text.startswith("/help"):
                await bot.reply_to(message, await Event.Help(_config))

            # 热力扳机
            if not started:
                try:
                    _trigger_message = await Event.Trigger(_hand, _config)
                    if _trigger_message.status:
                        _GroupTrigger = Vitality(group_id=_hand.from_chat.id)
                        _GroupTrigger.trigger(Message=_hand, config=_config)
                        _check = _GroupTrigger.check(Message=_hand)
                        if _check:
                            _hand.text = f"/catch {_hand.text}"
                            started = True
                except Exception as e:
                    logger.warning(
                        f"{e} \n This is a trigger Error,may [trigger] typo [tigger],try to check your config")

            # 触发
            if started:
                request_timestamps.append(time.time())
                _friends_message = await Event.Group(Message=_hand,
                                                     config=_config,
                                                     bot_profile=ProfileManager.access_telegram(init=False)
                                                     )
                _friends_message: PublicReturn
                if _friends_message.status:
                    if _friends_message.voice:
                        _caption = f"{_friends_message.reply}\n{_config.INTRO}"
                        msg = await bot.send_voice(chat_id=message.chat.id,
                                                   reply_to_message_id=message.id,
                                                   voice=_friends_message.voice,
                                                   caption=_caption
                                                   )
                    elif _friends_message.reply:
                        _caption = f"{_friends_message.reply}\n{_config.INTRO}"
                        msg = await bot.reply_to(message, _caption)
                    else:
                        msg = await bot.reply_to(message, _friends_message.msg)
                    Utils.trackMsg(f"{_hand.from_chat.id}{msg.id}", user_id=_hand.from_user.id)

        # 私聊
        @bot.message_handler(content_types=['text', 'sticker', 'photo'], chat_types=['private'])
        async def handle_private_msg(message):
            _hand = await get_message(bot, message)

            # 检查管理员指令
            _real_id = message.from_user.id
            _hand: User_Message
            request_timestamps.append(time.time())

            # 私聊嘛
            if not _hand.text.startswith("/"):
                _hand.text = f"/chat {_hand.text}"

            # 交谈
            if _hand.text.startswith(
                    ("/chat", "/voice", "/write", "/forgetme", "/style", "/remind")):
                _friends_message = await Event.Friends(Message=_hand,
                                                       config=_config,
                                                       bot_profile=ProfileManager.access_telegram(init=False)
                                                       )
                _friends_message: PublicReturn
                if _friends_message.status:
                    if _friends_message.voice:
                        _caption = f"{_friends_message.reply}\n{_config.INTRO}"
                        await bot.send_voice(chat_id=message.chat.id,
                                             reply_to_message_id=message.id,
                                             voice=_friends_message.voice,
                                             caption=_caption
                                             )
                    elif _friends_message.reply:
                        _caption = f"{_friends_message.reply}\n{_config.INTRO}"
                        await bot.reply_to(message, _caption)
                    else:
                        await bot.reply_to(message, _friends_message.msg)
            if _real_id in _config.master:
                _reply = await Event.MasterCommand(user_id=_real_id, Message=_hand, config=_config, pLock=pLock)
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
            while request_timestamps and request_timestamps[0] < time.time() - TIME_INTERVAL:
                request_timestamps.popleft()
            # 计算请求频率
            request_frequency = len(request_timestamps)
            DefaultData().setAnalysis(telegram=request_frequency)
            return request_frequency

        async def main():
            _me = await bot.get_me()
            _bot_id = _me.id
            _first_name = _me.first_name if _me.first_name else ""
            _last_name = _me.last_name if _me.last_name else ""
            _bot_name = ProfileManager.name_generate(first_name=_first_name, last_name=_last_name)
            ProfileManager.access_telegram(bot_name=_bot_name, bot_id=_bot_id, init=True)
            await asyncio.gather(
                bot.polling(non_stop=True, skip_pending=True, allowed_updates=util.update_types),
                set_cron(get_request_frequency, second=5)
            )

        asyncio.run(main())
