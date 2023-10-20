# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 下午10:22
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
import random

import crescent
import hikari
from hikari.impl import ProxySettings
from loguru import logger
from telebot import formatting
from typing_extensions import Annotated

from llmkira.middleware.env_virtual import EnvManager
from llmkira.middleware.router import RouterManager, Router
from llmkira.middleware.user import SubManager
from llmkira.schema import RawMessage
from llmkira.sdk.func_calling import ToolRegister
from llmkira.sdk.memory.redis import RedisChatMessageHistory
from llmkira.setting.discord import BotSetting
from llmkira.task import Task, TaskHeader
from llmkira.transducer import TransferManager
from .event import help_message, _upload_error_message_template, MappingDefault
from ..schema import Runner

__sender__ = "discord_hikari"
__default_function_enable__ = True

from ..util_func import auth_reloader, is_command, is_empty_command

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

    async def upload(self, attachment: hikari.Attachment):
        # Limit 7MB
        if attachment.size > 1024 * 1024 * 7:
            raise Exception("File size too large")
        file_name = f"{attachment.filename}"
        file_data = await attachment.read()
        return await RawMessage.upload_file(name=file_name, data=file_data)

    async def run(self):
        if not BotSetting.available:
            logger.warning("Sender Runtime:Discord not configured, skip")
            return None
        self.bot = hikari.GatewayBot(
            intents=hikari.Intents.ALL,
            token=BotSetting.token,
            proxy_settings=ProxySettings(
                url=BotSetting.proxy_address
            ) if BotSetting.proxy_address else None
        )
        self.proxy = BotSetting.proxy_address
        # prepare
        bot = self.bot
        model = StartUpEvent()
        client = crescent.Client(app=bot, model=model)

        # Task Creator
        async def create_task(message: hikari.Message, funtion_enable: bool = False):
            # event.message.embeds
            _file = []
            for attachment in message.attachments:
                try:
                    _file.append(await self.upload(attachment=attachment))
                except Exception as e:
                    logger.exception(e)
                    _template: str = random.choice(_upload_error_message_template)
                    await message.respond(
                        content=_template.format_map(map=MappingDefault(filename=attachment.filename, error=str(e))),
                        mentions_reply=True
                    )
            if message.content:
                message.content = message.content.lstrip("/chat").lstrip("/task")
            message.content = message.content if message.content else ""
            logger.info(
                f"discord_hikari:create task from {message.channel_id} {message.content[:300]} funtion_enable:{funtion_enable}"
            )
            # 任务构建
            try:
                # 转析器
                _transfer = TransferManager().sender_parser(agent_name=__sender__)
                deliver_back_message, _file = _transfer().parse(message=message, file=_file)
                # Reply
                success, logs = await DiscordTask.send_task(
                    task=TaskHeader.from_discord_hikari(
                        message,
                        file=_file,
                        deliver_back_message=deliver_back_message,
                        task_meta=TaskHeader.Meta(function_enable=funtion_enable, sign_as=(0, "root", __sender__)),
                        trace_back_message=[]
                    )
                )
                if not success:
                    pass
            except Exception as e:
                logger.exception(e)

        async def endpoint_autocomplete(
                ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
        ) -> list[tuple[str, str]]:
            return [("https://api.openai.com/v1/chat/completions", "https://api.openai.com/v1/chat/completions")]

        @client.include
        @crescent.command(dm_enabled=True, name="clear_endpoint", description="clear openai endpoint")
        async def listen_clear_endpoint_command(ctx: crescent.Context):
            try:
                status = "🪄 Clear endpoint success"
                await SubManager(user_id=f"{__sender__}:{ctx.user.id}").clear_endpoint()
            except Exception as e:
                status = "❌ Clear endpoint failed"
                logger.error(f"[102335]clear_endpoint failed {e}")
            return await ctx.respond(
                content=status,
                ephemeral=True
            )

        @client.include
        @crescent.command(dm_enabled=True, name="set_endpoint", description="set openai endpoint")
        async def listen_endpoint_command(
                ctx: crescent.Context,
                endpoint: Annotated[str, crescent.Autocomplete(endpoint_autocomplete)],
                openai_key: str
        ):
            try:
                await SubManager(user_id=f"{__sender__}:{ctx.user.id}").set_endpoint(
                    api_key=openai_key,
                    endpoint=endpoint
                )
            except Exception as e:
                return await ctx.respond(
                    content=f"❌ Set endpoint failed\n`{e}`",
                    ephemeral=True
                )
            else:
                return await ctx.respond(
                    content=formatting.format_text(
                        f"🪄 Set endpoint success\n",
                        f"endpoint: {endpoint}\n",
                        f"openai_key: {openai_key}\n",
                    ),
                    ephemeral=True
                )

        @client.include
        @crescent.command(dm_enabled=True, name="bind", description="bind some platform")
        async def listen_bind_command(ctx: crescent.Context, token: str):
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=ctx.user.id, dsn=token)
                _manager.add_router(router=router)
                router_list = _manager.get_router_by_user(user_id=ctx.user.id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await ctx.respond(
                    content=f"`{e}`",
                    ephemeral=True
                )
            return await ctx.respond(
                content=formatting.format_text(
                    formatting.mbold("🪄 Bind Success"),
                    "\n",
                    formatting.mbold("🔗 Current Bind"),
                    *[f" `{(item.dsn(user_dsn=True))}` " for item in router_list],
                    separator="\n"
                ),
                ephemeral=True
            )

        @client.include
        @crescent.command(dm_enabled=True, name="unbind", description="unbind some platform")
        async def listen_unbind_command(ctx: crescent.Context, token: str):
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=ctx.user.id, dsn=token)
                _manager.remove_router(router=router)
                router_list = _manager.get_router_by_user(user_id=ctx.user.id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await ctx.respond(
                    content=f"`{e}`",
                    ephemeral=True
                )
            return await ctx.respond(
                content=formatting.format_text(
                    formatting.mbold("🪄 Unbind Success"),
                    "\n",
                    formatting.mbold("🔗 Current Bind"),
                    *[f" `{(item.dsn(user_dsn=True))}` " for item in router_list],
                    separator="\n"
                ),
                ephemeral=True
            )

        @client.include
        @crescent.command(dm_enabled=True, name="clear", description="clear your message  history")
        async def listen_clear_command(ctx: crescent.Context):
            RedisChatMessageHistory(session_id=f"{__sender__}:{ctx.user.id}", ttl=60 * 60 * 1).clear()
            _comment = ["I swear I've forgotten about you.", "Okay?", "Let's hope so.", "I'm not sure what you mean.",
                        "what about u?"]
            return await ctx.respond(
                ephemeral=True,
                content=formatting.format_text(
                    f"I have cleared your message history\n",
                    random.choice(_comment),
                )
            )

        @client.include
        @crescent.command(dm_enabled=True, name="help", description="show help message")
        async def listen_help_command(ctx: crescent.Context):
            return await ctx.respond(
                ephemeral=True,
                content=formatting.format_text(
                    f"**🥕 Help**",
                    help_message(),
                )
            )

        @client.include
        @crescent.command(dm_enabled=True, name="auth", description="auth [uuid]")
        async def listen_auth_command(ctx: crescent.Context, uuid: str):
            try:
                await auth_reloader(uuid=uuid, user_id=f"{ctx.user.id}", platform=__sender__)
            except Exception as e:
                message = "❌ Auth failed,You dont have permission or the task do not exist"
                logger.error(f"[270563]auth_reloader failed {e}")
            else:
                message = "🪄 Auth Pass"
            return await ctx.respond(
                content=message,
                ephemeral=True
            )

        @client.include
        @crescent.command(dm_enabled=True, name="tool", description="Show function tool list")
        async def listen_tool_command(ctx: crescent.Context):
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
            await ctx.respond(
                ephemeral=True,
                content=tool_message,
            )

        @client.include
        @crescent.command(dm_enabled=True, name="env", description="env VAR1=XXX")
        async def listen_env_command(ctx: crescent.Context, env_string: str):
            _manager = EnvManager.from_meta(platform=__sender__, user_id=ctx.user.id)
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
            await ctx.respond(
                ephemeral=True,
                content=text,
            )

        # Two input point
        @client.include
        @crescent.event
        async def on_guild_create(event_: hikari.MessageCreateEvent):
            if event_.message.author.is_bot:
                return
            if not event_.content:
                logger.info(f"discord_hikari:ignore a empty message")
                return
            # Bot may cant read message
            if is_command(text=event_.content, command=f"{BotSetting.prefix}chat"):
                if is_empty_command(text=event_.content):
                    return await event_.message.respond(content="?")
                return await create_task(event_.message, funtion_enable=__default_function_enable__)
            if is_command(text=event_.content, command=f"{BotSetting.prefix}task"):
                if is_empty_command(text=event_.content):
                    return await event_.message.respond(content="?")
                return await create_task(event_.message, funtion_enable=True)
            if event_.message.referenced_message:
                # 回复了 Bot
                if event_.message.referenced_message.author.id == bot.get_me().id:
                    return await create_task(event_.message, funtion_enable=__default_function_enable__)

        @client.include
        @crescent.event
        async def on_dm_create(event_: hikari.DMMessageCreateEvent):
            if event_.message.author.is_bot:
                return
            return await create_task(event_.message, funtion_enable=True)

        logger.success("Sender Runtime:DiscordBot start")
        bot.run()
