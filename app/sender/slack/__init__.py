# -*- coding: utf-8 -*-
# @Time    : 2023/10/21 下午2:09
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import time
from ssl import SSLContext
from typing import List

import aiohttp
from loguru import logger
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_sdk.web.async_client import AsyncWebClient
from telebot import formatting
from telegramify_markdown import markdownify

from app.sender.util_func import (
    is_command,
    auth_reloader,
    parse_command,
    uid_make,
    login,
    dict2markdown,
    learn_instruction,
    logout,
)
from app.setting.slack import BotSetting
from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.file import File
from llmkira.memory import global_message_runtime
from llmkira.openapi.trigger import get_trigger_loop
from llmkira.sdk.tools import ToolRegister
from llmkira.task import Task, TaskHeader
from llmkira.task.schema import Sign, EventMessage
from .event import SlashCommand, SlackChannelInfo, help_message
from .schema import SlackMessageEvent, SlackFile
from ..schema import Runner

__sender__ = "slack"

SlackTask = Task(queue=__sender__)
__default_disable_tool_action__ = False
__join_cache__ = {}


async def download_url(url):
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {BotSetting.bot_token}"}
        if url.startswith("https://files.slack.com")
        else None
    ) as session:
        async with session.get(url, allow_redirects=True) as response:
            # verify content type is html
            if response.content_type == "text/html":
                logger.error(
                    "Warning, may bot missing `file:read` scope! because content_type is text/html"
                )
            if response.status == 200:
                return await response.read()


class SlackBotRunner(Runner):
    def __init__(self):
        self.proxy = None
        self.client = None
        self.bot = None

    async def upload(self, file: SlackFile, uid: str):
        if file.size > 1024 * 1024 * 20:
            return Exception(f"Chat File size too large:{file.size}")
        name = file.name
        url = file.url_private
        # Download from url
        try:
            data = await download_url(url=url)
        except Exception as e:
            logger.exception(
                f"[7652151]slack:download file failed :(\n {e} ,be sure you have the scope `files.read`"
            )
            return Exception(
                f"Download file failed {e},be sure bot have the scope `files.read`"
            )
        try:
            return await File.upload_file(creator=uid, file_name=name, file_data=data)
        except CacheDatabaseError as e:  # noqa
            logger.error(f"Cache upload failed {e} for user {uid}")
            return None

    async def transcribe(
        self,
        last_message: SlackMessageEvent,
        messages: List[SlackMessageEvent] = None,
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
                    chat_id=str(message.channel),
                    user_id=str(message.user),
                    text=f"{message.text}",
                    created_at=str(message.event_ts),  # timestamp
                )
            )
        file_prompt = ""
        if files:
            for file in files:
                file_prompt += f"\n<appendix name={file.file_name} key={file.file_key}>"
                # inform to llm
        event_messages.append(
            EventMessage(
                chat_id=str(last_message.channel),
                user_id=str(last_message.user),
                text=f"{last_message.text} {file_prompt}",
                created_at=str(last_message.event_ts),  # timestamp
                files=files,
            )
        )
        # 按照时间戳排序
        event_messages = sorted(event_messages, key=lambda x: x.created_at)
        return event_messages

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
            token=BotSetting.bot_token, ssl=ssl_cert, proxy=BotSetting.proxy_address
        )
        self.bot = AsyncApp(
            token=BotSetting.bot_token,
            signing_secret=BotSetting.secret,
            client=self.client,
        )
        bot = self.bot

        async def create_task(
            event_: SlackMessageEvent, disable_tool_action: bool = True
        ):
            """
            创建任务
            :param event_: SlackMessageEvent
            :param disable_tool_action: 是否启用功能
            :return:
            """
            message = event_
            _file = []
            if message.text:
                if message.text.startswith(("/chat", "/task")):
                    message.text = message.text[5:]
                if message.text.startswith("/ask"):
                    message.text = message.text[4:]
                message.text = message.text.replace(
                    f"<@{BotSetting.bot_id}>", f"@{BotSetting.bot_username}"
                )
            if not message.text:
                return None
            for file in message.files:
                try:
                    _file.append(
                        await self.upload(
                            file=file,
                            uid=uid_make(__sender__, message.user),
                        )
                    )
                except Exception as e:
                    await bot.client.chat_postMessage(
                        channel=message.channel,
                        text=formatting.format_text(
                            formatting.mbold("🪄 Failed"), e, separator="\n"
                        ),
                    )
            message.text = message.text if message.text else ""
            logger.info(
                f"slack:create task from {message.channel} {message.text[:300]} {disable_tool_action}"
            )
            # 任务构建
            try:
                # 转析器
                event_message = await self.transcribe(last_message=message, files=_file)
                sign = Sign.from_root(
                    disable_tool_action=disable_tool_action,
                    response_snapshot=True,
                    platform=__sender__,
                )
                _, event_message, sign = await self.hook(
                    platform=__sender__, messages=event_message, sign=sign
                )
                # Reply
                success, logs = await SlackTask.send_task(
                    task=TaskHeader.from_sender(
                        event_messages=event_message,
                        task_sign=sign,
                        message_id=message.thread_ts,
                        chat_id=message.channel,
                        user_id=message.user,
                        platform=__sender__,
                    )
                )
                if not success:
                    await bot.client.chat_postMessage(
                        channel=message.channel,
                        text=formatting.format_text(
                            formatting.mbold("🪄 Failed"), logs, separator="\n"
                        ),
                    )
            except Exception as e:
                logger.exception(e)

        @bot.command(command="/learn")
        async def listen_learn_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            reply = await learn_instruction(
                uid=uid_make(__sender__, command.user_id), instruction=_arg
            )
            return await respond(text=reply)

        @bot.command(command="/login")
        async def listen_login_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            reply = await login(
                uid=uid_make(__sender__, command.user_id), arg_string=_arg
            )
            return await respond(text=reply)

        @bot.command(command="/logout")
        async def listen_logout_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            if not command.text:
                return
            _arg = command.text
            reply = await logout(uid=uid_make(__sender__, command.user_id))
            return await respond(text=reply)

        @bot.command(command="/env")
        async def listen_env_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            _manager = EnvManager(user_id=uid_make(__sender__, command.user_id))
            if not command.text:
                env_map = await _manager.read_env()
                text = markdownify(dict2markdown(env_map))
                return await respond(text=text)
            _arg = command.text
            try:
                env_map = await _manager.set_env(
                    env_value=_arg, update=True, return_all=True
                )
            except Exception as e:
                logger.exception(f"[213562]env update failed {e}")
                text = formatting.mbold("🧊 Failed")
            else:
                text = markdownify(dict2markdown(env_map))
            await respond(text=text)

        @bot.command(command="/clear")
        async def listen_clear_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            await global_message_runtime.update_session(
                session_id=uid_make(__sender__, command.user_id)
            ).clear()
            return await respond(
                text=formatting.format_text(formatting.mbold("🪄 Done"), separator="\n")
            )

        @bot.command(command="/help")
        async def listen_help_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            await respond(
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"), help_message(), separator="\n"
                )
            )

        @bot.command(command="/tool")
        async def listen_tool_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            _tool = ToolRegister().get_plugins_meta
            _paper = [
                f"# {tool_item.name}\n{tool_item.get_function_string}\n```{tool_item.usage}```"
                for tool_item in _tool
            ]
            reply_message_text = markdownify("\n".join(_paper))
            return await respond(text=reply_message_text)

        async def auth_chain(uuid, user_id):
            try:
                result = await auth_reloader(
                    snapshot_credential=uuid,
                    user_id=f"{user_id}",
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
            return auth_result

        @bot.command(command="/auth")
        async def listen_auth_command(ack: AsyncAck, respond: AsyncRespond, command):
            command: SlashCommand = SlashCommand.model_validate(command)
            await ack()
            if not command.text:
                return await respond(text="🥕 Please input uuid")
            _arg = command.text.strip("`")
            auth_result = await auth_chain(uuid=_arg, user_id=command.user_id)
            return await respond(text=auth_result)

        async def validate_join(event_: SlackMessageEvent):
            """
            When Start, **validate every channel first event**
            """
            if __join_cache__.get(event_.channel):
                return True
            try:
                _res = await self.bot.client.conversations_info(channel=event_.channel)
                _channel: SlackChannelInfo = SlackChannelInfo.model_validate(
                    _res.get("channel", {})
                )
                if not _channel.is_member:
                    raise Exception("Not in channel")
            except Exception as e:
                logger.error(f"[353688]slack:validate_join failed {e}")
                try:
                    await self.bot.client.chat_postMessage(
                        channel=event_.user,
                        text="🥕 Please... invite me to the channel first :)"
                        if not event_.channel_type == "im"
                        else "🥺 I cant reach u, call from u own chat... ",
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

            # 扳机
            trigger = await get_trigger_loop(
                platform_name=__sender__,
                message=_text,
                uid=uid_make(__sender__, event_.user),
            )
            if trigger:
                if trigger.action == "allow":
                    return await create_task(
                        event_, disable_tool_action=trigger.function_enable
                    )
                if trigger.action == "deny":
                    return await bot.client.chat_postMessage(
                        channel=event_.channel,
                        text=trigger.message,
                        thread_ts=event_.thread_ts,
                    )

            # 默认指令
            if is_command(text=_text, command="!chat"):
                return await create_task(
                    event_, disable_tool_action=__default_disable_tool_action__
                )
            if is_command(text=_text, command="!task"):
                return await create_task(event_, disable_tool_action=False)
            if is_command(text=_text, command="!ask"):
                return await create_task(event_, disable_tool_action=True)
            if is_command(text=_text, command="!auth") or is_command(
                text=_text, command="`!auth"
            ):
                _cmd, _arg = parse_command(command=_text.strip("`"))
                if not _arg:
                    return None
                _arg = str(_arg).strip("`")
                auth_result = await auth_chain(uuid=_arg, user_id=event_.user)
                return await bot.client.chat_postMessage(
                    channel=event_.channel,
                    text=auth_result,
                    thread_ts=event_.thread_ts,
                )
            if f"<@{BotSetting.bot_id}>" in _text or _text.endswith(
                f"<@{BotSetting.bot_id}>"
            ):
                return await create_task(
                    event_, disable_tool_action=__default_disable_tool_action__
                )

        @bot.event("message")
        async def listen_im(_event, _logger):
            """
            自动响应私聊消息
            """
            event_: SlackMessageEvent = SlackMessageEvent.model_validate(_event)
            # 校验消息是否过期
            if int(float(event_.event_ts)) < int(time.time()) - 60 * 60 * 5:
                _logger.warning(f"slack: message expired {event_.event_ts}")
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
