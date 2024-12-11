# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:19
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import Optional, Union, List

import telegramify_markdown
from loguru import logger
from telebot import formatting, util
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telegramify_markdown import markdownify

from app.sender.util_func import (
    parse_command,
    is_command,
    is_empty_command,
    auth_reloader,
    uid_make,
    login,
    TimerObjectContainer,
    dict2markdown,
    learn_instruction,
    logout,
)
from app.setting.telegram import BotSetting
from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.file import File, CacheDatabaseError
from llmkira.memory import global_message_runtime
from llmkira.openapi.trigger import get_trigger_loop
from llmkira.sdk.tools.register import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Sign, EventMessage
from ..schema import Runner

__sender__ = "telegram"
__default_disable_tool_action__ = False

StepCache = StateMemoryStorage()
FileWindow = TimerObjectContainer()
TelegramTask = Task(queue=__sender__)


class TelegramBotRunner(Runner):
    def __init__(self):
        self.bot = None
        self.proxy = None

    async def is_user_admin(self, message: types.Message):
        _got = await self.bot.get_chat_member(message.chat.id, message.from_user.id)
        return _got.status in ["administrator", "sender"]

    async def transcribe(
        self,
        last_message: types.Message,
        messages: List[types.Message] = None,
        files: List[File] = None,
    ) -> List[EventMessage]:
        """
        转录消息
        :param last_message: 最后一条消息
        :param messages: 消息列表
        :param files: 文件列表
        :return: 事件消息列表
        """
        files = files if files else []
        messages = messages if messages else []
        event_messages = []
        files = [file for file in files if file]  # No None
        for index, message in enumerate(messages):
            message_text = (
                (
                    getattr(message, "text", None)
                    or getattr(message, "caption", None)
                    or "empty"
                )
                if message is not None
                else "empty"
            )
            event_messages.append(
                EventMessage(
                    chat_id=str(message.chat.id),
                    user_id=str(message.from_user.id),
                    text=message_text,
                    created_at=str(message.date),  # timestamp
                )
            )
        file_prompt = ""
        if files:
            for file in files:
                file_prompt += f"\n<appendix name={file.file_name} key={file.file_key}>"
                # inform to llm
        event_messages.append(
            EventMessage(
                chat_id=str(last_message.chat.id),
                user_id=str(last_message.from_user.id),
                text=last_message.text + file_prompt,
                created_at=str(last_message.date),  # timestamp
                files=files,
            )
        )
        # 按照时间戳排序
        event_messages = sorted(event_messages, key=lambda x: x.created_at)
        return event_messages

    async def upload(
        self, file: Union[types.PhotoSize, types.Document], uid: str
    ) -> Optional[File]:
        assert hasattr(file, "file_id"), "file_id not found"
        name = file.file_id
        _file_info = await self.bot.get_file(file.file_id)
        downloaded_file = await self.bot.download_file(_file_info.file_path)
        if isinstance(file, types.PhotoSize):
            name = f"{_file_info.file_unique_id}.jpg"
        if isinstance(file, types.Document):
            name = file.file_name
        try:
            return await File.upload_file(
                creator=uid, file_name=name, file_data=downloaded_file
            )
        except CacheDatabaseError as e:  # noqa
            logger.error(f"Cache upload failed {e} for user {uid}")
            return None

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:TelegramBot not configured, skip")
            return None
        self.bot = AsyncTeleBot(BotSetting.token, state_storage=StepCache)
        self.proxy = BotSetting.proxy_address
        bot = self.bot
        if self.proxy:
            from telebot import asyncio_helper

            asyncio_helper.proxy = self.proxy
            logger.info("TelegramBot proxy_tunnels being used!")

        async def create_task(message: types.Message, disable_tool_action: bool = True):
            """
            创建任务
            :param message: telegram message
            :param disable_tool_action: 是否启用功能
            :return:
            """
            uploaded_file = []
            message.text = message.text if message.text else message.caption
            if message.text:
                if message.text.startswith(("/chat", "/task")):
                    message.text = message.text[5:]
                if message.text.startswith("/ask"):
                    message.text = message.text[4:]
            if not message.text:
                return None
            __used_file_id = []
            photos: List[types.PhotoSize] = FileWindow.get_objects(
                user_id=message.from_user.id
            )
            FileWindow.clear_objects(user_id=message.from_user.id)
            for photo in photos:
                __used_file_id.append(photo.file_id)
                uploaded_file.append(
                    await self.upload(
                        file=photo,
                        uid=uid_make(__sender__, message.from_user.id),
                    )
                )
            if message.photo:
                uploaded_file.append(
                    await self.upload(
                        file=message.photo[-1],
                        uid=uid_make(__sender__, message.from_user.id),
                    )
                )
            if message.document:
                if message.document.file_size < 1024 * 1024 * 10:
                    uploaded_file.append(
                        await self.upload(
                            file=message.document,
                            uid=uid_make(__sender__, message.from_user.id),
                        )
                    )
            if message.reply_to_message:
                if message.reply_to_message.photo:
                    if message.reply_to_message.photo[-1].file_id not in __used_file_id:
                        uploaded_file.append(
                            await self.upload(
                                message.reply_to_message.photo[-1],
                                uid=uid_make(__sender__, message.from_user.id),
                            )
                        )
                if message.reply_to_message.document:
                    if message.reply_to_message.document.file_size < 1024 * 1024 * 10:
                        uploaded_file.append(
                            await self.upload(
                                file=message.reply_to_message.document,
                                uid=uid_make(__sender__, message.from_user.id),
                            )
                        )
            logger.info(
                f"telegram:create task from {message.chat.id} {message.text[:300]} "
                f"disable_tool_action:{disable_tool_action}"
            )
            # 任务构建
            try:
                history_message_list = []
                if message.reply_to_message:
                    history_message_list.append(message.reply_to_message)
                event_message = await self.transcribe(
                    last_message=message,
                    messages=history_message_list,
                    files=uploaded_file,
                )
                sign = Sign.from_root(
                    disable_tool_action=disable_tool_action,
                    response_snapshot=True,
                    platform=__sender__,
                )
                _, event_message, sign = await self.hook(
                    platform=__sender__, messages=event_message, sign=sign
                )
                # Reply
                success, logs = await TelegramTask.send_task(
                    task=TaskHeader.from_sender(
                        task_sign=sign,
                        event_messages=event_message,
                        chat_id=str(message.chat.id),
                        user_id=str(message.from_user.id),
                        message_id=str(message.message_id),
                        platform=__sender__,
                    )
                )
                if not success:
                    await bot.reply_to(message, text=logs)
            except Exception as e:
                logger.exception(e)

        @bot.message_handler(
            commands="learn", chat_types=["private", "supergroup", "group"]
        )
        async def listen_learn_command(message: types.Message):
            logger.debug("Debug:learn command")
            _cmd, _arg = parse_command(command=message.text)
            reply = await learn_instruction(
                uid=uid_make(__sender__, message.from_user.id), instruction=_arg
            )
            await bot.reply_to(message, text=reply)

        @bot.message_handler(commands="login", chat_types=["private"])
        async def listen_login_command(message: types.Message):
            logger.debug("Debug:login command")
            _cmd, _arg = parse_command(command=message.text)
            reply = await login(
                uid=uid_make(__sender__, message.from_user.id), arg_string=_arg
            )
            await bot.reply_to(
                message,
                text=reply,
                parse_mode="MarkdownV2",
            )

        @bot.message_handler(commands="logout", chat_types=["private"])
        async def listen_logout_command(message: types.Message):
            logger.debug("Debug:logout command")
            _cmd, _arg = parse_command(command=message.text)
            reply = await logout(uid=uid_make(__sender__, message.from_user.id))
            await bot.reply_to(
                message,
                text=reply,
                parse_mode="MarkdownV2",
            )

        @bot.message_handler(commands="env", chat_types=["private"])
        async def listen_env_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            _manager = EnvManager(user_id=uid_make(__sender__, message.from_user.id))
            if not _arg:
                env_map = await _manager.read_env()
                return await bot.reply_to(
                    message,
                    text=markdownify(dict2markdown(env_map)),
                    parse_mode="MarkdownV2",
                )
            try:
                env_map = await _manager.set_env(
                    env_value=_arg, update=True, return_all=True
                )
            except Exception as e:
                logger.exception(f"[213562]env update failed {e}")
                text = formatting.format_text(
                    formatting.mbold("🧊 Failed"), separator="\n"
                )
            else:
                text = markdownify(dict2markdown(env_map))
            await bot.reply_to(message, text=text, parse_mode="MarkdownV2")

        @bot.message_handler(
            commands="clear", chat_types=["private", "supergroup", "group"]
        )
        async def listen_clear_command(message: types.Message):
            await global_message_runtime.update_session(
                session_id=uid_make(__sender__, message.from_user.id)
            ).clear()
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"), separator="\n"
                ),
                parse_mode="MarkdownV2",
            )

        @bot.message_handler(
            commands="help", chat_types=["private", "supergroup", "group"]
        )
        async def listen_help_command(message: types.Message):
            from app.sender.telegram.event import help_message

            _message = await bot.reply_to(
                message,
                text=formatting.format_text(
                    telegramify_markdown.markdownify(help_message()),
                    separator="\n",
                ),
                parse_mode="MarkdownV2",
            )

        @bot.message_handler(
            commands="tool", chat_types=["private", "supergroup", "group"]
        )
        async def listen_tool_command(message: types.Message):
            _tool = ToolRegister().get_plugins_meta
            _paper = [
                f"# {tool_item.name}\n{tool_item.get_function_string}\n```{tool_item.usage}```"
                for tool_item in _tool
            ]
            reply_message_text = "\n".join(_paper)
            if len(reply_message_text) > 4096:
                reply_message_text = reply_message_text[:4096]
            return await bot.reply_to(
                message, text=markdownify(reply_message_text), parse_mode="MarkdownV2"
            )

        @bot.message_handler(
            commands="auth", chat_types=["private", "supergroup", "group"]
        )
        async def listen_auth_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            if not _arg:
                return None
            try:
                result = await auth_reloader(
                    snapshot_credential=_arg,
                    user_id=f"{message.from_user.id}",
                    platform=__sender__,
                )
            except Exception as e:
                auth_result = (
                    "❌ Auth failed,You dont have permission or the task do not exist"
                )
                logger.info(f"Auth failed {e}")
            else:
                if result:
                    auth_result = "🪄 Snapshot released"
                else:
                    auth_result = "You dont have this snapshot"
            return await bot.reply_to(message, text=markdownify(auth_result))

        @bot.message_handler(
            content_types=["text", "photo", "document"], chat_types=["private"]
        )
        async def handle_private_msg(message: types.Message):
            """
            自动响应私聊消息
            """
            message.text = message.text if message.text else message.caption

            # Support for GPT Vision
            if not message.text:
                if message.photo:
                    logger.debug("Add a spc image")
                    FileWindow.add_object(
                        user_id=message.from_user.id, obj=message.photo[-1]
                    )
                return None
            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=message.text,
                uid=uid_make(__sender__, message.from_user.id),
            )
            if trigger:
                if trigger == "allow":
                    return await create_task(
                        message, disable_tool_action=__default_disable_tool_action__
                    )
                if trigger == "deny":
                    return None
                return await create_task(
                    message, disable_tool_action=__default_disable_tool_action__
                )

            if is_command(text=message.text, command="/task"):
                return await create_task(message, disable_tool_action=True)
            if is_command(text=message.text, command="/ask"):
                return await create_task(message, disable_tool_action=False)
            return await create_task(
                message, disable_tool_action=__default_disable_tool_action__
            )

        @bot.message_handler(
            content_types=["text", "photo", "document", "voice"],
            chat_types=["supergroup", "group"],
        )
        async def handle_group_msg(message: types.Message):
            """
            自动响应群组消息
            """
            message.text = message.text if message.text else message.caption
            if not message.text:
                return None

            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=message.text,
                uid=uid_make(__sender__, message.from_user.id),
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        message, disable_tool_action=trigger.disable_tool_action
                    )
                if trigger.action == "deny":
                    return await bot.reply_to(message, text=trigger.message)

            # 响应
            if is_command(
                text=message.text,
                command="/chat",
                at_bot_username=BotSetting.bot_username,
            ):
                if is_empty_command(text=message.text):
                    return await bot.reply_to(message, text="Say something?")
                return await create_task(
                    message, disable_tool_action=__default_disable_tool_action__
                )
            if is_command(
                text=message.text,
                command="/task",
                at_bot_username=BotSetting.bot_username,
            ):
                if is_empty_command(text=message.text):
                    return await bot.reply_to(message, text="Say something?")
                return await create_task(message, disable_tool_action=False)
            if is_command(
                text=message.text,
                command="/ask",
                at_bot_username=BotSetting.bot_username,
            ):
                if is_empty_command(text=message.text):
                    return await bot.reply_to(message, text="Say something?")
                return await create_task(message, disable_tool_action=True)
            if f"@{BotSetting.bot_username} " in message.text or message.text.endswith(
                f" @{BotSetting.bot_username}"
            ):
                return await create_task(
                    message, disable_tool_action=__default_disable_tool_action__
                )
            # 检查回复
            if message.reply_to_message:
                # 回复了 Bot
                if str(message.reply_to_message.from_user.id) == str(BotSetting.bot_id):
                    return await create_task(
                        message, disable_tool_action=__default_disable_tool_action__
                    )

        from telebot import asyncio_filters

        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))
        logger.success("Sender Runtime:TelegramBot start")
        await bot.infinity_polling(
            allowed_updates=util.update_types,
            skip_pending=True,
            timeout=60,
            request_timeout=60,
        )
