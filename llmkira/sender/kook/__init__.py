# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:33
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
import random

import aiohttp
from khl import Bot, Message, Cert, MessageTypes, PrivateMessage, PublicMessage
from loguru import logger
from telebot import formatting

from llmkira.extra.user import UserControl
from llmkira.middleware.env_virtual import EnvManager
from llmkira.middleware.router import RouterManager, Router
from llmkira.schema import RawMessage
from llmkira.sdk.func_calling import ToolRegister
from llmkira.sdk.memory.redis import RedisChatMessageHistory
from llmkira.setting.kook import BotSetting
from llmkira.task import Task, TaskHeader
from .event import help_message, _upload_error_message_template, MappingDefault
from ..schema import Runner

__sender__ = "kook"
__default_function_enable__ = True

from ..util_func import auth_reloader, is_command, is_empty_command
from ...sdk.openapi.trigger import get_trigger_loop

KookTask = Task(queue=__sender__)


class CacheTemp(object):
    def __init__(self):
        self.__file_cache_queue_ = {}

    def new(self, user_id):
        if not self.__file_cache_queue_.get(user_id) or not isinstance(self.__file_cache_queue_[user_id], list):
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

    async def upload(self, file_info: dict):
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
        return await RawMessage.upload_file(name=name, data=data)

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:Kook not configured, skip")
            return None
        self.bot = Bot(cert=Cert(token=BotSetting.token))
        # prepare
        bot = self.bot

        # Task Creator
        async def create_task(event: Message, funtion_enable: bool = False):
            # event.message.embeds
            _file: list = []
            try:
                if event.type == MessageTypes.FILE:
                    _file_cache_queue_.append(
                        user_id=event.author_id,
                        item=await self.upload(event.extra.get("attachments"))
                    )
                    return None
                if event.type == MessageTypes.IMG:
                    _file_cache_queue_.append(
                        user_id=event.author_id,
                        item=await self.upload(event.extra.get("attachments"))
                    )
                    return None
            except Exception as e:
                logger.exception(e)
                _template: str = random.choice(_upload_error_message_template)
                await event.reply(
                    content=_template.format_map(map=MappingDefault(filename="File", error=str(e))),
                    type=MessageTypes.KMD,
                )
                return None

            # Cache Run Point
            if event.type in [MessageTypes.KMD, MessageTypes.TEXT]:
                _file: list = [item for item in _file_cache_queue_.get(user_id=event.author_id) if item]
                _file_cache_queue_.clear(user_id=event.author_id)
            message: Message = event
            if message.content:
                if message.content.startswith(("/chat", "/task")):
                    message.content = message.content[5:]
                if message.content.startswith("/ask"):
                    message.content = message.content[4:]
            message.content = message.content if message.content else ""
            logger.info(
                f"kook:create task from {message.ctx.channel.id} {message.content[:300]} funtion_enable:{funtion_enable}"
            )
            # 任务构建
            try:
                # 转析器
                message, _file = await self.loop_turn_only_message(
                    platform_name=__sender__,
                    message=message,
                    file_list=_file
                )
                # Reply
                kook_task = TaskHeader.from_kook(
                    message,
                    file=_file,
                    deliver_back_message=[],
                    task_meta=TaskHeader.Meta.from_root(
                            function_enable=funtion_enable,
                            release_chain=True,
                            platform=__sender__
                        ),
                    trace_back_message=[]
                )
                success, logs = await KookTask.send_task(
                    task=kook_task
                )
                if not success:
                    pass
            except Exception as e:
                logger.exception(e)

        @bot.command(name='clear_endpoint')
        async def listen_clear_endpoint_command(msg: Message):
            try:
                status = "🪄 Clear endpoint success"
                await UserControl.clear_endpoint(uid=UserControl.uid_make(__sender__, msg.author_id))
            except Exception as e:
                status = "❌ Clear endpoint failed"
                logger.error(f"[102335]clear_endpoint failed {e}")
            if isinstance(msg, PublicMessage):
                return await msg.reply(
                    content=status,
                    is_temp=True
                )
            if isinstance(msg, PrivateMessage):
                return await msg.reply(
                    content=status
                )

        @bot.command(name='set_endpoint')
        async def listen_endpoint_command(
                msg: Message,
                openai_endpoint: str,
                openai_key: str,
                model: str
        ):
            try:
                new_driver = await UserControl.set_endpoint(
                    uid=UserControl.uid_make(__sender__, msg.author_id),
                    api_key=openai_key,
                    endpoint=openai_endpoint,
                    model=model
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Set endpoint failed\n`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        f"🪄 Set endpoint success\n",
                        new_driver.detail
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD
                )

        @bot.command(name='token_clear')
        async def listen_token_clear_command(msg: Message):
            try:
                status = "🪄 Clear token success"
                await UserControl.set_token(
                    uid=UserControl.uid_make(__sender__, msg.author_id),
                    token=None
                )
            except Exception as e:
                status = "❌ Clear token failed"
                logger.error(f"[217835]token clear failed {e}")
            if isinstance(msg, PublicMessage):
                return await msg.reply(
                    content=status,
                    is_temp=True
                )
            if isinstance(msg, PrivateMessage):
                return await msg.reply(
                    content=status
                )

        @bot.command(name='token')
        async def listen_token_command(
                msg: Message,
                token: str
        ):
            try:
                token = await UserControl.set_token(
                    uid=UserControl.uid_make(__sender__, msg.author_id),
                    token=token
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Set token failed\n`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        f"🪄 Set token success\n",
                        token
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD
                )

        @bot.command(name='func_ban')
        async def listen_func_ban_command(
                msg: Message,
                func_name: str
        ):
            try:
                func_list = await UserControl.block_plugin(
                    uid=UserControl.uid_make(__sender__, msg.author_id),
                    plugin_name=func_name
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Ban failed\n`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        f"🪄 Ban success\n",
                        f"**🔗 Current Ban**\n"
                        f"{[f'`{item}`' for item in func_list]}"
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD
                )

        @bot.command(name='func_unban')
        async def listen_func_unban_command(
                msg: Message,
                func_name: str
        ):
            try:
                func_list = await UserControl.unblock_plugin(
                    uid=UserControl.uid_make(__sender__, msg.author_id),
                    plugin_name=func_name
                )
            except Exception as e:
                return await msg.reply(
                    content=f"❌ Unban failed\n`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD
                )
            else:
                return await msg.reply(
                    content=formatting.format_text(
                        f"🪄 Ban success\n",
                        f"**🔗 Current Ban**\n"
                        f"{[f'`{item}`' for item in func_list]}"
                    ),
                    is_temp=True,
                    type=MessageTypes.KMD
                )

        @bot.command(name='bind')
        async def listen_bind_command(msg: Message, dsn: str):
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=msg.author_id, dsn=dsn)
                _manager.add_router(router=router)
                router_list = _manager.get_router_by_user(user_id=msg.author_id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await msg.reply(
                    content=f"`{e}`",
                    is_temp=True,
                    type=MessageTypes.KMD
                )
            return await msg.reply(
                content=formatting.format_text(
                    formatting.mbold("🪄 Bind Success"),
                    "\n",
                    formatting.mbold("🔗 Current Bind"),
                    *[f" `{(item.dsn(user_dsn=True))}` " for item in router_list],
                    separator="\n"
                ),
                is_temp=True,
                type=MessageTypes.KMD
            )

        @bot.command(name='unbind')
        async def listen_unbind_command(msg: Message, dsn: str):
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=msg.author_id, dsn=dsn)
                _manager.remove_router(router=router)
                router_list = _manager.get_router_by_user(user_id=msg.author_id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await msg.reply(
                    content=f"`{e}`",
                    type=MessageTypes.KMD,
                    is_temp=True
                )
            return await msg.reply(
                content=formatting.format_text(
                    formatting.mbold("🪄 Unbind Success"),
                    "\n",
                    formatting.mbold("🔗 Current Bind"),
                    *[f" `{(item.dsn(user_dsn=True))}` " for item in router_list],
                    separator="\n"
                ),
                type=MessageTypes.KMD,
                is_temp=True
            )

        @bot.command(name='clear')
        async def listen_clear_command(msg: Message):
            RedisChatMessageHistory(session_id=f"{__sender__}:{msg.author_id}", ttl=60 * 60 * 1).clear()
            _comment = ["I swear I've forgotten about you.", "Okay?", "Let's hope so.", "I'm not sure what you mean.",
                        "what about u?"]
            return await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=formatting.format_text(
                    f"I have cleared your message history\n",
                    random.choice(_comment),
                )
            )

        @bot.command(name='help')
        async def listen_help_command(msg: Message):
            return await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=formatting.format_text(
                    f"**🥕 Help**",
                    help_message(),
                )
            )

        @bot.command(name='tool')
        async def listen_tool_command(msg: Message):
            _tool = ToolRegister().functions
            _paper = [[c.name, c.description] for name, c in _tool.items()]
            arg = [
                f"**{item[0]}**\n"
                f"{item[1]}\n"
                for item in _paper
            ]
            tool_message = formatting.format_text(
                formatting.mbold("🔧 Tool List"),
                *arg,
                separator="\n"
            )
            await msg.reply(
                is_temp=True,
                type=MessageTypes.KMD,
                content=tool_message,
            )

        @bot.command(name='auth')
        async def listen_auth_command(msg: Message, uuid: str):
            try:
                await auth_reloader(uuid=uuid, user_id=f"{msg.author_id}", platform=__sender__)
            except Exception as e:
                message = "❌ Auth failed,You dont have permission or the task do not exist"
                logger.error(f"[2753383]auth_reloader failed:{e}")
            else:
                message = "🪄 Auth Pass"
            return await msg.reply(
                content=message,
                is_temp=True,
                type=MessageTypes.KMD
            )

        @bot.command(name='env')
        async def listen_env_command(msg: Message, env_string: str):
            _manager = EnvManager.from_meta(platform=__sender__, user_id=msg.author_id)
            try:
                _meta_data = _manager.parse_env(env_string=env_string)
                updated_env = await _manager.update_env(env=_meta_data)
            except Exception as e:
                logger.exception(f"[1202359]env update failed {e}")
                text = formatting.format_text(
                    f"**🧊 Env parse failed...O_o**\n",
                    separator="\n"
                )
            else:
                text = formatting.format_text(
                    f"**🧊 Updated**\n"
                    f"```json\n{json.dumps(updated_env, indent=2)}```",
                    separator="\n"
                )
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
                uid=UserControl.uid_make(__sender__, msg.author_id)
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(msg, funtion_enable=trigger.function_enable)
                if trigger.action == "deny":
                    return await msg.reply(content=trigger.message)
            # 命令
            if is_command(text=msg.content, command=f"/chat"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(msg, funtion_enable=__default_function_enable__)
            if is_command(text=msg.content, command=f"/chat"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(msg, funtion_enable=True)
            if is_command(text=msg.content, command=f"/ask"):
                if is_empty_command(text=msg.content):
                    return await msg.reply(content="?")
                return await create_task(msg, funtion_enable=False)
            # 追溯回复

        async def on_dm_create(msg: PrivateMessage):
            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=msg.content,
                uid=UserControl.uid_make(__sender__, msg.author_id)
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(msg, funtion_enable=trigger.function_enable)
                if trigger.action == "deny":
                    return await msg.reply(content=trigger.message)
            if is_command(text=msg.content, command="/task"):
                return await create_task(msg, funtion_enable=True)
            if is_command(text=msg.content, command="/ask"):
                return await create_task(msg, funtion_enable=False)
            return await create_task(msg, funtion_enable=__default_function_enable__)

        @bot.command(regex=r'[\s\S]*')
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
