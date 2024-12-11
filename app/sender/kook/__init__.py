# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:33
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import random
from typing import List

import aiohttp
import khl
from khl import Bot, Message, Cert, MessageTypes, PrivateMessage, PublicMessage
from loguru import logger
from telebot import formatting
from telegramify_markdown import markdownify

from app.setting.kook import BotSetting
from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.file import File
from llmkira.memory import global_message_runtime
from llmkira.sdk.tools import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Sign, EventMessage
from .event import help_message, _upload_error_message_template, MappingDefault
from ..schema import Runner

__sender__ = "kook"
__default_disable_tool_action__ = False

from ..util_func import (
    auth_reloader,
    is_command,
    is_empty_command,
    uid_make,
    save_credential,
    dict2markdown,
    learn_instruction,
    logout,
)
from llmkira.openapi.trigger import get_trigger_loop
from ...components.credential import ProviderError, Credential

KookTask = Task(queue=__sender__)


class CacheTemp(object):
    def __init__(self):
        self.__file_cache_queue_ = {}

    def new(self, user_id):
        if not self.__file_cache_queue_.get(user_id) or not isinstance(
            self.__file_cache_queue_[user_id], list
        ):
            self.__file_cache_queue_[user_id] = []
        return self

    def append(self, user_id, item):
        self.new(user_id=user_id).__file_cache_queue_[user_id].append(item)
        return self

    def clear(self, user_id):
        self.new(user_id=user_id).__file_cache_queue_[user_id].clear()
        return self

    def get(self, user_id):
        return self.__file_cache_queue_.get(user_id, [])


_file_cache_queue_ = CacheTemp()


async def download_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()


class KookBotRunner(Runner):
    def __init__(self):
        self.bot = None
        self.proxy = None

    async def upload(self, file_info: dict, uid: str):
        if not file_info.get("url"):
            return Exception("File url not found")
        if file_info.get("type") == "file":
            if file_info.get("size") > 1024 * 1024 * 5:
                raise Exception("File size too large")
        name = file_info.get("name", "unknown")
        url = file_info.get("url", None)
        # Download from url
        try:
            data = await download_url(url=url)
        except Exception as e:
            logger.exception(f"[602253]kook:download file failed {e}")
            return Exception(f"Download file failed {e}")
        try:
            return await File.upload_file(creator=uid, file_name=name, file_data=data)
        except CacheDatabaseError as e:  # noqa
            logger.error(f"Cache upload failed {e} for user {uid}")
            return None

    async def transcribe(
        self,
        last_message: khl.Message,
        messages: List[khl.Message] = None,
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
        for index, message in enumerate(messages):
            event_messages.append(
                EventMessage(
                    chat_id=(
                        message.ctx.guild.id
                        if message.ctx.guild
                        else message.ctx.channel.id
                    ),
                    user_id=str(message.author_id),
                    text=f"{message.content}",
                    created_at=str(message.msg_timestamp),  # timestamp
                )
            )
        file_prompt = ""
        if files:
            for file in files:
                file_prompt += f"\n<appendix name={file.file_name} key={file.file_key}>"
                # inform to llm
        event_messages.append(
            EventMessage(
                chat_id=(
                    last_message.ctx.guild.id
                    if last_message.ctx.guild
                    else last_message.ctx.channel.id
                ),
                user_id=str(last_message.author_id),
                text=f"{last_message.content} {file_prompt}",
                created_at=str(last_message.msg_timestamp),  # timestamp
                files=files,
            )
        )
        # 按照时间戳排序
        event_messages = sorted(event_messages, key=lambda x: x.created_at)
        return event_messages

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:Kook not configured, skip")
            return None
        self.bot = Bot(cert=Cert(token=BotSetting.token))
        # prepare
        bot = self.bot

        # Task Creator
        async def create_task(_event: Message, disable_tool_action: bool = False):
            # event.message.embeds
            _file: list = []
            try:
                if _event.type == MessageTypes.FILE:
                    _file_cache_queue_.append(
                        user_id=_event.author_id,
                        item=await self.upload(
                            _event.extra.get("attachments"),
                            uid=uid_make(__sender__, _event.author_id),
                        ),
                    )
                    return None
                if _event.type == MessageTypes.IMG:
                    _file_cache_queue_.append(
                        user_id=_event.author_id,
                        item=await self.upload(
                            _event.extra.get("attachments"),
                            uid=uid_make(__sender__, _event.author_id),
                        ),
                    )
                    return None
            except Exception as e:
                logger.exception(e)
                _template: str = random.choice(_upload_error_message_template)
                await _event.reply(
                    content=_template.format_map(
                        map=MappingDefault(filename="File", error=str(e))
                    ),
                    type=MessageTypes.KMD,
                )
                return None

            # Cache Run Point
            if _event.type in [MessageTypes.KMD, MessageTypes.TEXT]:
                _file: list = [
                    item
                    for item in _file_cache_queue_.get(user_id=_event.author_id)
                    if item
                ]
                _file_cache_queue_.clear(user_id=_event.author_id)
            message: Message = _event
            if message.content:
                if message.content.startswith(("/chat", "/task")):
                    message.content = message.content[5:]
                if message.content.startswith("/ask"):
                    message.content = message.content[4:]
            message.content = message.content if message.content else ""
            logger.info(
                f"kook:create task from {message.ctx.channel.id} "
                f"{message.content[:300]} disable_tool_action:{disable_tool_action}"
            )
            # 任务构建
            try:
                event_message = await self.transcribe(
                    last_message=message,
                    files=_file,
                )
                sign = Sign.from_root(
                    disable_tool_action=disable_tool_action,
                    response_snapshot=True,
                    platform=__sender__,
                )
                # 转析器
                _, event_message, sign = await self.hook(
                    platform=__sender__, messages=event_message, sign=sign
                )
                # Reply
                kook_task = TaskHeader.from_sender(
                    event_message,
                    task_sign=sign,
                    message_id=None,
                    chat_id=message.ctx.channel.id,
                    user_id=message.author_id,
                    platform=__sender__,
                )
                success, logs = await KookTask.send_task(task=kook_task)
                if not success:
                    pass
            except Exception as e:
                logger.exception(e)

        @bot.command(name="login_via_url")
        async def listen_login_url_command(
            msg: Message,
            provider_url: str,
            token: str,
        ):
            try:
                credential = Credential.from_provider(
                    token=token, provider_url=provider_url
                )
                await save_credential(
                    uid=uid_make(__sender__, msg.author_id),
                    credential=credential,
                )
            except ProviderError as e:
                return await msg.reply(
                    content=f"Login failed, website return {e}",
                    is_temp=True,
                    type=MessageTypes.KMD,
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Set endpoint failed\n`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD,
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        "\nLogin success as provider! Welcome master!",
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD,
                )

        @bot.command(name="learn")
        async def listen_learn_command(
            msg: Message,
            instruction: str,
        ):
            reply = await learn_instruction(
                uid=uid_make(__sender__, msg.author_id),
                instruction=instruction,
            )
            return await msg.reply(
                content=markdownify(reply),
                is_temp=True,
                type=MessageTypes.KMD,
            )

        @bot.command(name="login")
        async def listen_login_command(
            msg: Message,
            api_endpoint: str,
            api_key: str,
            api_model: str = "gpt-4o-mini",
            api_tool_model: str = "gpt-4o-mini",
        ):
            try:
                credential = Credential(
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    api_model=api_model,
                    api_tool_model=api_tool_model,
                )
                await save_credential(
                    uid=uid_make(__sender__, msg.author_id),
                    credential=credential,
                )
            except ProviderError as e:
                return await msg.reply(
                    content=f"Login failed, website return {e}",
                    is_temp=True,
                    type=MessageTypes.KMD,
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Set endpoint failed\n`{type(e)}`",
                    is_temp=True,
                    type=MessageTypes.KMD,
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        "\nLogin success as provider! Welcome master!",
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD,
                )

        @bot.command(name="logout")
        async def listen_logout_command(msg: Message):
            reply = await logout(uid=uid_make(__sender__, msg.author_id))
            return await msg.reply(
                content=markdownify(reply),
                is_temp=True,
                type=MessageTypes.KMD,
            )

        @bot.command(name="clear")
        async def listen_clear_command(msg: Message):
            await global_message_runtime.update_session(
                session_id=uid_make(__sender__, msg.author_id),
            ).clear()
            _comment = [
                "I swear I've forgotten about you.",
                "Okay?",
                "Let's hope so.",
                "I'm not sure what you mean.",
                "what about u?",
            ]
            return await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=formatting.format_text(
                    "I have cleared your message history\n",
                    random.choice(_comment),
                ),
            )

        @bot.command(name="help")
        async def listen_help_command(msg: Message):
            return await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=formatting.format_text(
                    "**🥕 Help**",
                    help_message(),
                ),
            )

        @bot.command(name="tool")
        async def listen_tool_command(msg: Message):
            _tool = ToolRegister().get_plugins_meta
            _paper = [
                f"# {tool_item.name}\n{tool_item.get_function_string}\n```{tool_item.usage}```"
                for tool_item in _tool
            ]
            reply_message_text = markdownify("\n".join(_paper))
            await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=reply_message_text,
            )

        @bot.command(name="auth")
        async def listen_auth_command(msg: Message, credential: str):
            try:
                result = await auth_reloader(
                    snapshot_credential=credential,
                    user_id=f"{msg.author_id}",
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
            return await msg.reply(
                content=auth_result, is_temp=True, type=MessageTypes.KMD
            )

        @bot.command(name="env")
        async def listen_env_command(msg: Message, env_string: str):
            _manager = EnvManager(user_id=uid_make(__sender__, msg.author_id))
            try:
                env_map = await _manager.set_env(
                    env_value=env_string, update=True, return_all=True
                )
            except Exception as e:
                logger.exception(f"[1202359]env update failed {e}")
                text = formatting.format_text(
                    "**🧊 Env parse failed...O_o**\n", separator="\n"
                )
            else:
                text = markdownify(dict2markdown(env_map))
            await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=text,
            )

        async def on_guild_create(msg: PublicMessage):
            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=msg.content,
                uid=uid_make(__sender__, msg.author_id),
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        msg, disable_tool_action=trigger.function_enable
                    )
                if trigger.action == "deny":
                    return await msg.reply(content=trigger.message)
            # 命令
            if is_command(text=msg.content, command="/chat"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(
                    msg, disable_tool_action=__default_disable_tool_action__
                )
            if is_command(text=msg.content, command="/chat"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(msg, disable_tool_action=False)
            if is_command(text=msg.content, command="/ask"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(msg, disable_tool_action=True)
            # 追溯回复

        async def on_dm_create(msg: PrivateMessage):
            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=msg.content,
                uid=uid_make(__sender__, msg.author_id),
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        msg, disable_tool_action=trigger.function_enable
                    )
                if trigger.action == "deny":
                    return await msg.reply(content=trigger.message)

            if is_command(text=msg.content, command="/task"):
                return await create_task(msg, disable_tool_action=False)
            if is_command(text=msg.content, command="/ask"):
                return await create_task(msg, disable_tool_action=True)
            return await create_task(
                msg, disable_tool_action=__default_disable_tool_action__
            )

        @bot.command(regex=r"[\s\S]*")
        async def handle_message(event_: Message):
            if event_.author.bot:
                return None
            # NOT A BOT
            if isinstance(event_, PublicMessage):
                await on_guild_create(event_)
            if isinstance(event_, PrivateMessage):
                await on_dm_create(event_)

        logger.success("Sender Runtime:KookBot start")
        bot.run()
