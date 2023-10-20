# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:19
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json

from loguru import logger
from telebot import formatting, util
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.formatting import escape_markdown

from llmkira.middleware.env_virtual import EnvManager
from llmkira.middleware.router import RouterManager, Router
from llmkira.middleware.user import SubManager
from llmkira.schema import RawMessage
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.sdk.memory.redis import RedisChatMessageHistory
from llmkira.sender.util_func import parse_command, is_command, is_empty_command, auth_reloader
from llmkira.setting.telegram import BotSetting
from llmkira.task import Task, TaskHeader
from llmkira.transducer import TransferManager
from ..schema import Runner

StepCache = StateMemoryStorage()
__sender__ = "telegram"
TelegramTask = Task(queue=__sender__)
__default_function_enable__ = True


class TelegramBotRunner(Runner):

    def __init__(self):
        self.bot = None
        self.proxy = None

    async def is_user_admin(self, message: types.Message):
        _got = await self.bot.get_chat_member(message.chat.id, message.from_user.id)
        return _got.status in ['administrator', 'sender']

    async def upload(self, file):
        assert hasattr(file, "file_id"), "file_id not found"
        name = file.file_id
        _file_info = await self.bot.get_file(file.file_id)
        downloaded_file = await self.bot.download_file(_file_info.file_path)
        if isinstance(file, types.PhotoSize):
            name = f"{_file_info.file_unique_id}.jpg"
        if isinstance(file, types.Document):
            name = file.file_name
        return await RawMessage.upload_file(name=name, data=downloaded_file)

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

        async def create_task(message: types.Message, funtion_enable: bool = False):
            """
            创建任务
            :param message: telegram message
            :param funtion_enable: 是否启用功能
            :return:
            """
            _file = []
            if message.text:
                message.text = message.text.lstrip("/chat").lstrip("/task")
            if not message.text:
                return None
            if message.photo:
                _file.append(await self.upload(message.photo[-1]))
            if message.document:
                if message.document.file_size < 1024 * 1024 * 10:
                    _file.append(await self.upload(message.document))
            if message.reply_to_message:
                if message.reply_to_message.photo:
                    _file.append(await self.upload(message.reply_to_message.photo[-1]))
                if message.reply_to_message.document:
                    if message.reply_to_message.document.file_size < 1024 * 1024 * 10:
                        _file.append(await self.upload(message.reply_to_message.document))
            message.text = message.text if message.text else ""
            logger.info(
                f"telegram:create task from {message.chat.id} {message.text[:300]} funtion_enable:{funtion_enable}"
            )
            # 任务构建
            try:
                # 转析器
                _transfer = TransferManager().sender_parser(agent_name=__sender__)
                deliver_back_message, _file = _transfer().parse(message=message, file=_file)
                # Reply
                success, logs = await TelegramTask.send_task(
                    task=TaskHeader.from_telegram(
                        message,
                        file=_file,
                        deliver_back_message=deliver_back_message,
                        task_meta=TaskHeader.Meta(function_enable=funtion_enable, sign_as=(0, "root", __sender__)),
                        trace_back_message=[message.reply_to_message]
                    )
                )
                if not success:
                    await bot.reply_to(message, text=logs)
            except Exception as e:
                logger.exception(e)

        @bot.message_handler(commands='clear_endpoint', chat_types=['private'])
        async def listen_clear_endpoint_command(message: types.Message):
            # _cmd, _arg = parse_command(command=message.text)
            _tips = "🪄 Done"
            await SubManager(user_id=f"{__sender__}:{message.from_user.id}").clear_endpoint()
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold(_tips),
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='set_endpoint', chat_types=['private'])
        async def listen_set_endpoint_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            if not _arg:
                return
            _arg = str(_arg)
            _except = _arg.split("#", maxsplit=1)
            if len(_except) == 2:
                openai_key, openai_endpoint = _except
            else:
                openai_key, openai_endpoint = (_arg, None)
            try:
                await SubManager(user_id=f"{__sender__}:{message.from_user.id}").set_endpoint(
                    api_key=openai_key,
                    endpoint=openai_endpoint
                )
            except Exception as e:
                return await bot.reply_to(
                    message,
                    text=formatting.format_text(
                        formatting.mbold(f"🪄 Failed: {e}"),
                        formatting.mitalic("Format: /set_endpoint <openai_key>#<openai_endpoint>"),
                        separator="\n"
                    ),
                    parse_mode="MarkdownV2"
                )
            else:
                return await bot.reply_to(
                    message,
                    text=formatting.format_text(
                        formatting.mbold("🪄 Done"),
                        formatting.mbold(f"openai_key: {openai_key}"),
                        formatting.mbold(f"openai_endpoint: {openai_endpoint}"),
                        separator="\n"
                    ),
                    parse_mode="MarkdownV2"
                )

        @bot.message_handler(commands='bind', chat_types=['private'])
        async def listen_bind_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            if not _arg:
                return
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=message.from_user.id, dsn=_arg)
                _manager.add_router(router=router)
                router_list = _manager.get_router_by_user(user_id=message.from_user.id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await bot.reply_to(
                    message,
                    text=formatting.format_text(
                        formatting.mbold(str(e)),
                        separator="\n"
                    ),
                    parse_mode="MarkdownV2"
                )
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"),
                    *[f"`{escape_markdown(item.dsn(user_dsn=True))}`" for item in router_list],
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='env', chat_types=['private'])
        async def listen_env_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            if not _arg:
                return None
            _manager = EnvManager.from_meta(platform=__sender__, user_id=message.from_user.id)
            try:
                _meta_data = _manager.parse_env(env_string=_arg)
                updated_env = await _manager.update_env(env=_meta_data)
            except Exception as e:
                logger.exception(f"[213562]env update failed {e}")
                text = formatting.format_text(
                    formatting.mbold("🧊 Failed"),
                    separator="\n"
                )
            else:
                text = formatting.format_text(
                    formatting.mbold("🦴 Env Changed"),
                    formatting.mcode(json.dumps(updated_env, indent=2)),
                    separator="\n"
                )
            await bot.reply_to(
                message,
                text=text,
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='unbind', chat_types=['private'])
        async def listen_unbind_command(message: types.Message):
            _cmd, _arg = parse_command(command=message.text)
            if not _arg:
                return None
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=message.from_user.id, dsn=_arg)
                _manager.remove_router(router=router)
                router_list = _manager.get_router_by_user(user_id=message.from_user.id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await bot.reply_to(
                    message,
                    text=formatting.format_text(
                        formatting.mbold(str(e)),
                        separator="\n"
                    ),
                    parse_mode="MarkdownV2"
                )
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"),
                    *[f"`{escape_markdown(item.dsn(user_dsn=True))}`" for item in router_list],
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='clear', chat_types=['private', 'supergroup', 'group'])
        async def listen_help_command(message: types.Message):
            RedisChatMessageHistory(session_id=f"{__sender__}:{message.from_user.id}", ttl=60 * 60 * 1).clear()
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"),
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='help', chat_types=['private', 'supergroup', 'group'])
        async def listen_help_command(message: types.Message):
            from llmkira.sender.telegram.event import help_message
            _message = await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    escape_markdown(help_message()),
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(commands='tool', chat_types=['private', 'supergroup', 'group'])
        async def listen_tool_command(message: types.Message):
            _tool = ToolRegister().functions
            _paper = [[c.name, c.description] for name, c in _tool.items()]
            arg = [
                formatting.mbold(item[0]) +
                "\n" +
                escape_markdown(item[1]) +
                "\n"
                for item in _paper
            ]
            return await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🔧 Tool List"),
                    *arg,
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        @bot.message_handler(content_types=['text', 'photo', 'document'], chat_types=['private'])
        async def handle_private_msg(message: types.Message):
            """
            自动响应私聊消息
            """
            message.text = message.text if message.text else message.caption
            if not message.text:
                return None
            if is_command(text=message.text, command="/auth"):
                if not is_empty_command(text=message.text):
                    _cmd, _arg = parse_command(command=message.text)
                    try:
                        await auth_reloader(uuid=_arg, user_id=f"{message.from_user.id}", platform=__sender__)
                    except Exception as e:
                        auth_result = "❌ Auth failed,You dont have permission or the task do not exist"
                        logger.error(f"[270563]auth_reloader failed {e}")
                    else:
                        auth_result = "🪄 Auth Pass"
                    return await bot.reply_to(
                        message,
                        text=auth_result
                    )
            if is_command(text=message.text, command="/task"):
                return await create_task(message, funtion_enable=True)
            return await create_task(message, funtion_enable=__default_function_enable__)

        @bot.message_handler(content_types=['text', 'photo', 'document'], chat_types=['supergroup', 'group'])
        async def handle_group_msg(message: types.Message):
            """
            自动响应群组消息
            """
            message.text = message.text if message.text else message.caption
            if not message.text:
                return None
            if is_command(text=message.text, command="/auth"):
                if not is_empty_command(text=message.text):
                    _cmd, _arg = parse_command(command=message.text)
                    try:
                        await auth_reloader(uuid=_arg, user_id=f"{message.from_user.id}", platform=__sender__)
                    except Exception as e:
                        auth_result = "❌ Auth failed,You dont have permission or the task do not exist"
                        logger.error(f"[270563]auth_reloader failed {e}")
                    else:
                        auth_result = "🪄 Auth Pass"
                    return await bot.reply_to(
                        message,
                        text=auth_result
                    )
            if is_command(text=message.text, command="/chat", at_bot_username=BotSetting.bot_username):
                if is_empty_command(text=message.text):
                    return await bot.reply_to(message, text="?")
                return await create_task(message, funtion_enable=__default_function_enable__)
            if is_command(text=message.text, command="/task", at_bot_username=BotSetting.bot_username):
                if is_empty_command(text=message.text):
                    return await bot.reply_to(message, text="?")
                return await create_task(message, funtion_enable=True)
            if f"@{BotSetting.bot_username} " in message.text or message.text.endswith(f" @{BotSetting.bot_username}"):
                return await create_task(message, funtion_enable=__default_function_enable__)
            # 检查回复
            if message.reply_to_message:
                # 回复了 Bot
                if message.reply_to_message.from_user.id == BotSetting.bot_id:
                    return await create_task(message, funtion_enable=__default_function_enable__)

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))
        logger.success("Sender Runtime:TelegramBot start")
        await bot.infinity_polling(
            allowed_updates=util.update_types,
            skip_pending=True,
            timeout=20,
            request_timeout=20
        )
