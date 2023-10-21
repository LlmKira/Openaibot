# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午2:09
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
import time
from ssl import SSLContext

import aiohttp
from loguru import logger
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from telebot import formatting
from telebot.formatting import escape_markdown

from llmkira.middleware.env_virtual import EnvManager
from llmkira.middleware.router import RouterManager, Router
from llmkira.middleware.user import SubManager
from llmkira.sdk.func_calling.register import ToolRegister
from llmkira.sdk.memory.redis import RedisChatMessageHistory
from llmkira.sender.util_func import is_command, auth_reloader, parse_command
from llmkira.setting.slack import BotSetting
from llmkira.task import Task, TaskHeader
from llmkira.transducer import TransferManager
from .event import SlashCommand, SlackChannelInfo, help_message
from ..schema import Runner
from ...schema import SlackMessageEvent, RawMessage

__sender__ = "slack"
SlackTask = Task(queue=__sender__)
__default_function_enable__ = True
__join_cache__ = {}


async def download_url(url):
    async with aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {BotSetting.bot_token}"
            } if url.startswith("https://files.slack.com") else None
    ) as session:
        async with session.get(url, allow_redirects=True) as response:
            # verify content type is html
            if response.content_type == "text/html":
                logger.error(f"Warning, may bot missing `file:read` scope! because content_type is text/html")
            if response.status == 200:
                return await response.read()


class SlackBotRunner(Runner):
    def __init__(self):
        self.proxy = None
        self.client = None
        self.bot = None

    async def upload(self, file: SlackMessageEvent.SlackFile):
        if file.size > 1024 * 1024 * 20:
            return Exception(f"Chat File size too large:{file.size}")
        name = file.name
        url = file.url_private
        # Download from url
        try:
            data = await download_url(url=url)
        except Exception as e:
            logger.exception(f"[7652151]slack:download file failed :(\n {e} ,be sure you have the scope `files.read`")
            return Exception(f"Download file failed {e},be sure bot have the scope `files.read`")
        return await RawMessage.upload_file(name=name, data=data)

    async def run(self):

        if not BotSetting.available:
            logger.warning("Sender Runtime:SlackBot not configured, skip")
            return
        ssl_cert = SSLContext()
        # pip3 install proxy.py
        # proxy --port 9000 --log-level d
        if BotSetting.proxy_address:
            self.proxy = BotSetting.proxy_address
            logger.info("SlackBot proxy_tunnels being used in `AsyncWebClient`!")
        self.client = AsyncWebClient(
            token=BotSetting.bot_token,
            ssl=ssl_cert,
            proxy=BotSetting.proxy_address
        )
        self.bot = AsyncApp(
            token=BotSetting.bot_token,
            signing_secret=BotSetting.secret,
            client=self.client,
        )
        bot = self.bot

        async def create_task(event_: SlackMessageEvent, funtion_enable: bool = False):
            """
            创建任务
            :param event_: SlackMessageEvent
            :param funtion_enable: 是否启用功能
            :return:
            """
            message = event_
            _file = []
            if message.text:
                message.text = message.text.lstrip("/chat").lstrip("/task")
                message.text = message.text.replace(f"<@{BotSetting.bot_id}>", f"@{BotSetting.bot_username}")
            if not message.text:
                return None
            for file in message.files:
                try:
                    _file.append(await self.upload(file=file))
                except Exception as e:
                    await bot.client.chat_postMessage(
                        channel=message.channel,
                        text=formatting.format_text(
                            formatting.mbold("🪄 Failed"),
                            e,
                            separator="\n"
                        )
                    )
            message.text = message.text if message.text else ""
            logger.info(
                f"slack:create task from {message.channel} {message.text[:300]} funtion_enable:{funtion_enable}"
            )
            # 任务构建
            try:
                # 转析器
                _transfer = TransferManager().sender_parser(agent_name=__sender__)
                deliver_back_message, _file = _transfer().parse(message=message, file=_file)
                # Reply
                success, logs = await SlackTask.send_task(
                    task=TaskHeader.from_slack(
                        message=event_,
                        file=_file,
                        deliver_back_message=deliver_back_message,
                        task_meta=TaskHeader.Meta(function_enable=funtion_enable, sign_as=(0, "root", __sender__))
                    )
                )
                if not success:
                    await bot.client.chat_postMessage(
                        channel=message.channel,
                        text=formatting.format_text(
                            formatting.mbold("🪄 Failed"),
                            logs,
                            separator="\n"
                        )
                    )
            except Exception as e:
                logger.exception(e)

        @bot.command(command='/clear_endpoint')
        async def listen_clear_endpoint_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            # _cmd, _arg = parse_command(command=message.text)
            _tips = "🪄 Done"
            await SubManager(user_id=f"{__sender__}:{command.user_id}").clear_endpoint()
            return await respond(
                text=_tips
            )

        @bot.command(command='/set_endpoint')
        async def listen_set_endpoint_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            _except = _arg.split("#", maxsplit=1)
            if len(_except) == 2:
                openai_key, openai_endpoint = _except
            else:
                openai_key, openai_endpoint = (_arg, None)
            try:
                await SubManager(user_id=f"{__sender__}:{command.user_id}").set_endpoint(
                    api_key=openai_key,
                    endpoint=openai_endpoint
                )
            except Exception as e:
                return await respond(
                    text=formatting.format_text(
                        formatting.mbold(f"🪄 Failed: {e}", escape=False),
                        formatting.mitalic("Format: /set_endpoint <openai_key>#<openai_endpoint>"),
                        separator="\n"
                    )
                )
            else:
                return await respond(
                    text=formatting.format_text(
                        formatting.mbold("🪄 Done", escape=False),
                        formatting.mbold(f"openai_key: {openai_key}", escape=False),
                        formatting.mbold(f"openai_endpoint: {openai_endpoint}", escape=False),
                        separator="\n"
                    )
                )

        @bot.command(command='/bind')
        async def listen_bind_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=command.user_id, dsn=_arg)
                _manager.add_router(router=router)
                router_list = _manager.get_router_by_user(user_id=command.user_id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await respond(
                    text=formatting.format_text(
                        formatting.mbold(str(e), escape=False),
                        separator="\n"
                    )
                )
            return await respond(
                text=formatting.format_text(
                    formatting.mbold("🪄 Done", escape=False),
                    *[f"`{escape_markdown(item.dsn(user_dsn=True))}`" for item in router_list],
                    separator="\n"
                )
            )

        @bot.command(command='/env')
        async def listen_env_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            _manager = EnvManager.from_meta(platform=__sender__, user_id=command.user_id)
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
            await respond(
                text=text
            )

        @bot.command(command='/unbind')
        async def listen_unbind_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            _manager = RouterManager()
            try:
                router = Router.build_from_receiver(receiver=__sender__, user_id=command.user_id, dsn=_arg)
                _manager.remove_router(router=router)
                router_list = _manager.get_router_by_user(user_id=command.user_id, to_=__sender__)
            except Exception as e:
                logger.exception(e)
                return await respond(
                    text=formatting.format_text(
                        formatting.mbold(str(e)),
                        separator="\n"
                    )
                )
            return await respond(
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"),
                    *[f"`{escape_markdown(item.dsn(user_dsn=True))}`" for item in router_list],
                    separator="\n"
                )
            )

        @bot.command(command='/clear')
        async def listen_clear_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            RedisChatMessageHistory(session_id=f"{__sender__}:{command.user_id}", ttl=60 * 60 * 1).clear()
            return await respond(
                text=formatting.format_text(
                    formatting.mbold("🪄 Done"),
                    separator="\n"
                )
            )

        @bot.command(command='/help')
        async def listen_help_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            await respond(
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    help_message(),
                    separator="\n"
                )
            )

        @bot.command(command='/tool')
        async def listen_tool_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            _tool = ToolRegister().functions
            _paper = [[c.name, c.description] for name, c in _tool.items()]
            arg = [
                formatting.mbold(item[0], escape=False) +
                "\n" +
                item[1] +
                "\n"
                for item in _paper
            ]
            return await respond(
                text=formatting.format_text(
                    formatting.mbold("🔧 Tool List"),
                    *arg,
                    separator="\n"
                )
            )

        async def auth_chain(uuid, user_id):
            try:
                await auth_reloader(uuid=uuid, user_id=f"{user_id}", platform=__sender__)
            except Exception as e:
                auth_result = "❌ Auth failed,You dont have permission or the task do not exist"
                logger.info(f"[3031]auth_reloader failed {e}")
            else:
                auth_result = "🪄 Auth Pass"
            return auth_result

        @bot.command(command='/auth')
        async def listen_auth_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.parse_obj(command)
            await ack()
            if not command.text:
                return await respond(
                    text="🥕 Please input uuid"
                )
            _arg = command.text.strip("`")
            auth_result = await auth_chain(uuid=_arg, user_id=command.user_id)
            return await respond(
                text=auth_result
            )

        async def validate_join(event_: SlackMessageEvent):
            """
            When Start, **validate every channel first event**
            """
            if __join_cache__.get(event_.channel):
                return True
            try:
                _res = await self.bot.client.conversations_info(
                    channel=event_.channel
                )
                _channel: SlackChannelInfo = SlackChannelInfo.parse_obj(_res.get("channel", {}))
                if not _channel.is_member:
                    raise Exception("Not in channel")
            except Exception as e:
                logger.error(f"[353688]slack:validate_join failed {e}")
                try:
                    await self.bot.client.chat_postMessage(
                        channel=event_.user,
                        text="🥕 Please... invite me to the channel first :)"
                        if not event_.channel_type == "im" else "🥺 I cant reach u, call from u own chat... ",
                    )
                except Exception as e:
                    logger.error(f"[364258]slack:validate_join failed {e}")
                return False
            else:
                __join_cache__[event_.channel] = True
                return True

        async def deal_group(event_: SlackMessageEvent):
            """
            自动响应群组消息
            """
            if not event_.text:
                return None
            if not await validate_join(event_=event_):
                return None
            _text = event_.text
            if is_command(text=_text, command="!chat"):
                return await create_task(event_, funtion_enable=__default_function_enable__)
            if is_command(text=_text, command="!task"):
                return await create_task(event_, funtion_enable=True)
            if is_command(text=_text, command="!ask"):
                return await create_task(event_, funtion_enable=False)
            if is_command(text=_text, command="!auth"):
                _cmd, _arg = parse_command(command=_text)
                if not _arg:
                    return None
                auth_result = await auth_chain(uuid=_text, user_id=event_.user)
                return await bot.client.chat_postMessage(
                    channel=event_.channel,
                    text=auth_result,
                    thread_ts=event_.thread_ts,
                )
            if f"<@{BotSetting.bot_id}>" in _text or _text.endswith(f"<@{BotSetting.bot_id}>"):
                return await create_task(event_, funtion_enable=__default_function_enable__)

        @bot.event("message")
        async def listen_im(event, logger):
            """
            自动响应私聊消息
            """

            logger.info(event)
            event_: SlackMessageEvent = SlackMessageEvent.parse_obj(event)
            # 校验消息是否过期
            if int(float(event_.event_ts)) < int(time.time()) - 60 * 60 * 5:
                logger.warning(f"slack: message expired {event_.event_ts}")
                return
            if not event_.text:
                return None
            if event_.channel_type == "im":
                return await deal_group(event_)
            if event_.channel_type == "group":
                return await deal_group(event_)
            if event_.channel_type == "channel":
                return await deal_group(event_)

        _self_get = await self.client.auth_test()
        logger.success(f"SlackBot init, bot_id:{_self_get}")
        BotSetting.bot_id = _self_get["user_id"]
        BotSetting.bot_username = _self_get["user"]
        logger.success("Sender Runtime:SlackBot start")
        listen_world = AsyncSocketModeHandler(bot, BotSetting.app_token)
        await listen_world.start_async()
