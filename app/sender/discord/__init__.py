# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 下午10:22
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import base64
import binascii
import random
from typing import List

import crescent
import hikari
from hikari import Intents
from hikari.impl import ProxySettings
from loguru import logger
from telebot import formatting
from telegramify_markdown import markdownify

from app.setting.discord import BotSetting
from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.file import File
from llmkira.memory import global_message_runtime
from llmkira.sdk.tools import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import EventMessage, Sign
from .event import help_message
from ..schema import Runner

__sender__ = "discord_hikari"
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
from ...components.credential import Credential, ProviderError

DiscordTask = Task(queue=__sender__)


class StartUpEvent(object):
    def __init__(self) -> None:
        ...

    async def on_start(self, event: hikari.StartedEvent) -> None:
        """
        This function is called when your bot starts. This is a good place to open a
        connection to a database, aiohttp client, or similar.
        """
        pass

    async def on_stop(self, event: hikari.StoppedEvent) -> None:
        """
        This function is called when your bot stops. This is a good place to put
        cleanup functions for the model class.
        """
        pass


class DiscordBotRunner(Runner):
    def __init__(self):
        self.bot = None
        self.proxy = None

    async def upload(self, attachment: hikari.Attachment, uid: str):
        # Limit 7MB
        if attachment.size > 1024 * 1024 * 7:
            raise Exception("File size too large")
        file_name = f"{attachment.filename}"
        file_data = await attachment.read()
        try:
            return await File.upload_file(
                creator=uid, file_name=file_name, file_data=file_data
            )
        except CacheDatabaseError as e:  # noqa
            logger.error(f"Cache upload failed {e} for user {uid}")
            return None

    async def transcribe(
        self,
        last_message: hikari.Message,
        messages: List[hikari.Message] = None,
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
                    chat_id=str(
                        message.guild_id if message.guild_id else message.channel_id
                    ),
                    user_id=str(message.author.id),
                    text=f"{message.content}",
                    created_at=str(message.created_at.timestamp()),  # timestamp
                )
            )
        file_prompt = ""
        if files:
            for file in files:
                file_prompt += f"\n<appendix name={file.file_name} key={file.file_key}>"
                # inform to llm
        event_messages.append(
            EventMessage(
                chat_id=str(
                    last_message.guild_id
                    if last_message.guild_id
                    else last_message.channel_id
                ),
                user_id=str(last_message.author.id),
                text=f"{last_message.content} {file_prompt}",
                created_at=str(last_message.created_at.timestamp()),  # timestamp
                files=files,
            )
        )
        # 按照时间戳排序
        event_messages = sorted(event_messages, key=lambda x: x.created_at)
        return event_messages

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:Discord not configured, skip")
            return None
        my_intents = (
            Intents.GUILDS
            | Intents.GUILD_MESSAGES
            | Intents.DM_MESSAGES
            | Intents.MESSAGE_CONTENT
        )
        logger.info(f"Sender Runtime:DiscordBot will start with intents:{my_intents}")
        self.bot = hikari.GatewayBot(
            intents=my_intents,
            token=BotSetting.token,
            proxy_settings=ProxySettings(url=BotSetting.proxy_address)
            if BotSetting.proxy_address
            else None,
        )
        self.proxy = BotSetting.proxy_address
        # prepare
        bot = self.bot
        model = StartUpEvent()
        client = crescent.Client(app=bot, model=model)
        # Base64 解码
        try:
            _based = BotSetting.token.split(".", maxsplit=1)[0] + "=="
            _bot_id = base64.b64decode(_based).decode("utf-8")
        except UnicodeDecodeError as e:
            logger.exception(f"Sender Runtime:DiscordBot token maybe invalid {e}")
        except binascii.Error as e:
            logger.exception(f"Sender Runtime:DiscordBot token maybe invalid {e}")
        except Exception as e:
            logger.exception(f"Sender Runtime:DiscordBot token maybe invalid {e}")
        else:
            BotSetting.bot_id = _bot_id

        # Task Creator
        async def create_task(
            message: hikari.Message, disable_tool_action: bool = False
        ):
            # event.message.embeds
            _file = []
            for attachment in message.attachments:
                try:
                    _file.append(
                        await self.upload(
                            attachment=attachment,
                            uid=uid_make(__sender__, message.author.id),
                        )
                    )
                except Exception as e:
                    logger.exception(e)
                    await message.respond(
                        content=f"Some file upload failed, {type(e)}",
                        mentions_reply=True,
                    )
            if message.content:
                if message.content.startswith(("/chat", "/task")):
                    message.content = message.content[5:]
                if message.content.startswith("/ask"):
                    message.content = message.content[4:]
            message.content = message.content if message.content else ""
            _user_name = bot.get_me().username
            if _user_name:
                message.content = message.content.replace(
                    f"<@{BotSetting.bot_id}>", f" @{_user_name} "
                )
            logger.info(
                f"discord_hikari:create task from {message.channel_id} "
                f"{message.content[:300]} disable_tool_action:{disable_tool_action}"
            )
            # 任务构建
            try:
                event_message = await self.transcribe(last_message=message, files=_file)
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
                success, logs = await DiscordTask.send_task(
                    task=TaskHeader.from_sender(
                        event_message,
                        task_sign=sign,
                        chat_id=str(
                            message.guild_id if message.guild_id else message.channel_id
                        ),
                        user_id=str(message.author.id),
                        message_id=str(message.id),
                        platform=__sender__,
                    )
                )
                if not success:
                    pass
            except Exception as e:
                logger.exception(e)

        @client.include
        @crescent.command(
            dm_enabled=True, name="login_via_url", description="login via url"
        )
        async def listen_login_url_command(
            ctx: crescent.Context,
            provider_url: str,
            token: str,
        ):
            try:
                credential = Credential.from_provider(
                    token=token, provider_url=provider_url
                )
                await save_credential(
                    uid=uid_make(__sender__, ctx.user.id),
                    credential=credential,
                )
            except ProviderError as e:
                return await ctx.respond(
                    content=f"❌ Login failed\n`{e}`", ephemeral=True
                )
            except Exception as e:
                return await ctx.respond(
                    content=f"❌ Login failed\n`{e}`", ephemeral=True
                )
            else:
                return await ctx.respond(
                    content="\nLogin success as provider! Welcome master!",
                    ephemeral=True,
                )

        @client.include
        @crescent.command(
            dm_enabled=True,
            name="learn",
            description="Set instruction text",
        )
        async def listen_learn_command(ctx: crescent.Context, instruction: str):
            reply = await learn_instruction(
                uid=uid_make(__sender__, ctx.user.id), instruction=instruction
            )
            return await ctx.respond(content=markdownify(reply), ephemeral=True)

        @client.include
        @crescent.command(
            dm_enabled=True,
            name="login",
            description="set openai endpoint for yourself",
        )
        async def listen_endpoint_command(
            ctx: crescent.Context,
            api_endpoint: str,
            api_key: str,
            api_model: str,
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
                    uid=uid_make(__sender__, ctx.user.id),
                    credential=credential,
                )
            except ProviderError as e:
                return await ctx.respond(
                    content=formatting.format_text(f"❌ Set endpoint failed {e}\n", e),
                    ephemeral=True,
                )
            except Exception as e:
                return await ctx.respond(
                    content=formatting.format_text(
                        f"❌ Set endpoint failed\n`{type(e)}`", e
                    ),
                    ephemeral=True,
                )
            else:
                return await ctx.respond(
                    content=formatting.format_text(
                        "\nLogin success as provider! Welcome master!",
                    ),
                    ephemeral=True,
                )

        @client.include
        @crescent.command(
            dm_enabled=True, name="logout", description="clear your credential"
        )
        async def listen_logout_command(ctx: crescent.Context):
            reply = await logout(
                uid=uid_make(__sender__, ctx.user.id),
            )
            return await ctx.respond(
                ephemeral=True,
                content=reply,
            )

        @client.include
        @crescent.command(
            dm_enabled=True, name="clear", description="clear your message  history"
        )
        async def listen_clear_command(ctx: crescent.Context):
            await global_message_runtime.update_session(
                session_id=uid_make(__sender__, ctx.user.id),
            ).clear()
            _comment = [
                "I swear I've forgotten about you.",
                "Okay?",
                "Let's hope so.",
                "I'm not sure what you mean.",
                "what about u?",
            ]
            return await ctx.respond(
                ephemeral=True,
                content=formatting.format_text(
                    "I have cleared your message history\n",
                    random.choice(_comment),
                ),
            )

        @client.include
        @crescent.command(dm_enabled=True, name="help", description="show help message")
        async def listen_help_command(ctx: crescent.Context):
            return await ctx.respond(
                ephemeral=True,
                content=formatting.format_text(
                    "**🥕 Help**",
                    help_message(),
                ),
            )

        @client.include
        @crescent.command(dm_enabled=True, name="auth", description="auth [credential]")
        async def listen_auth_command(ctx: crescent.Context, credential: str):
            try:
                result = await auth_reloader(
                    snapshot_credential=credential,
                    user_id=f"{ctx.user.id}",
                    platform=__sender__,
                )
            except Exception as exc:
                message = (
                    "❌ Auth failed,You dont have permission or the task do not exist"
                )
                logger.error(f"[270563]auth_reloader failed {exc}")
            else:
                if result:
                    message = "🪄 Auth Pass"
                else:
                    message = "You dont have this snapshot"
            return await ctx.respond(content=message, ephemeral=True)

        @client.include
        @crescent.command(
            dm_enabled=True, name="tool", description="Show function tool list"
        )
        async def listen_tool_command(ctx: crescent.Context):
            _tool = ToolRegister().get_plugins_meta
            _paper = [
                f"# {tool_item.name}\n{tool_item.get_function_string}\n```{tool_item.usage}```"
                for tool_item in _tool
            ]
            reply_message_text = markdownify("\n".join(_paper))
            await ctx.respond(
                ephemeral=True,
                content=reply_message_text,
            )

        @client.include
        @crescent.command(dm_enabled=True, name="env", description="env VAR1=XXX")
        async def listen_env_command(ctx: crescent.Context, env_string: str):
            _manager = EnvManager(user_id=uid_make(__sender__, ctx.user.id))
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
            await ctx.respond(
                ephemeral=True,
                content=text,
            )

        # Two input point
        @client.include
        @crescent.event
        async def on_guild_create(event_: hikari.GuildMessageCreateEvent):
            if event_.message.author.is_bot:
                return
            if not event_.content:
                logger.info(
                    "discord_hikari:ignore a empty message,do you turn on the MESSAGE_CONTENT setting?"
                )
                return

            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=event_.content,
                uid=uid_make(__sender__, event_.message.author.id),
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        event_.message, disable_tool_action=trigger.function_enable
                    )
                if trigger.action == "deny":
                    return await event_.message.respond(content=trigger.message)

            # 命令
            # Bot may cant read message
            if is_command(text=event_.content, command=f"{BotSetting.prefix}chat"):
                if is_empty_command(text=event_.content):
                    return await event_.message.respond(content="?")
                return await create_task(
                    event_.message, disable_tool_action=__default_disable_tool_action__
                )

            if is_command(text=event_.content, command=f"{BotSetting.prefix}task"):
                if is_empty_command(text=event_.content):
                    return await event_.message.respond(content="?")
                return await create_task(event_.message, disable_tool_action=False)

            if is_command(text=event_.content, command=f"{BotSetting.prefix}ask"):
                if is_empty_command(text=event_.content):
                    return await event_.message.respond(content="?")
                return await create_task(event_.message, disable_tool_action=True)

            if f"<@{BotSetting.bot_id}>" in event_.content:
                # At 事件
                return await create_task(
                    event_.message, disable_tool_action=__default_disable_tool_action__
                )

            if event_.message.referenced_message:
                # 回复了 Bot
                if event_.message.referenced_message.author.id == bot.get_me().id:
                    return await create_task(
                        event_.message,
                        disable_tool_action=__default_disable_tool_action__,
                    )

        @client.include
        @crescent.event
        async def on_dm_create(event_: hikari.DMMessageCreateEvent):
            if event_.message.author.is_bot:
                return
            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__, message=event_.content
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        event_.message, disable_tool_action=trigger.function_enable
                    )
                if trigger.action == "deny":
                    return await event_.message.respond(content=trigger.message)
            # 命令
            if is_command(text=event_.content, command=f"{BotSetting.prefix}task"):
                return await create_task(event_.message, disable_tool_action=False)
            if is_command(text=event_.content, command=f"{BotSetting.prefix}ask"):
                return await create_task(event_.message, disable_tool_action=True)
            return await create_task(
                event_.message, disable_tool_action=__default_disable_tool_action__
            )

        logger.success("Sender Runtime:DiscordBot start")
        bot.run()
