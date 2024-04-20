# -*- coding: utf-8 -*-
__package__name__ = "llmkira.extra.plugins.alarm"
__plugin_name__ = "set_alarm_reminder"
__openapi_version__ = "20240416"

import datetime
import re
from typing import Optional, Union, Type

from llmkira.openai.cell import Tool, ToolCall, class_tool
from llmkira.sdk.tools import verify_openapi_version
from llmkira.sdk.utils import sync
from llmkira.task.schema import Location, EventMessage, Sign, ToolResponse

verify_openapi_version(__package__name__, __openapi_version__)  # noqa
from llmkira.sdk.tools import PluginMetadata  # noqa
from llmkira.sdk.tools.schema import FuncPair, BaseTool  # noqa
from loguru import logger  # noqa
from pydantic import BaseModel, Field  # noqa
from pydantic import field_validator, ConfigDict  # noqa

from app.receiver.aps import SCHEDULER  # noqa

from llmkira.task import Task, TaskHeader  # noqa
import pytz  # noqa
from tzlocal import get_localzone


class SetAlarm(BaseModel):
    delay: int = Field(description="The delay time, in minutes")
    content: str = Field(description="reminder content")
    model_config = ConfigDict(extra="allow")

    @field_validator("delay")
    def delay_validator(cls, v):
        if v < 0:
            raise ValueError("delay must be greater than 0")
        return v


def send_notify(
    _platform, _meta, _sender: dict, _receiver: dict, _user, _chat, _content: str
):
    sync(
        Task.create_and_send(
            queue_name=_platform,
            task=TaskHeader(
                sender=Location.model_validate(_sender),  # 继承发送者
                receiver=Location.model_validate(
                    _receiver
                ),  # 因为可能有转发，所以可以单配
                task_sign=Sign.model_validate(_meta),
                message=[EventMessage(user_id=_user, chat_id=_chat, text=_content)],
            ),
        )
    )


class AlarmTool(BaseTool):
    """
    搜索工具
    """

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = SetAlarm
    keywords: list = ["闹钟", "提醒", "定时", "到点", "分钟", "小时"]
    pattern: Optional[re.Pattern] = re.compile(
        r"(\d+)(分钟|小时|天|周|月|年)后提醒我(.*)"
    )

    # env_required: list = ["SCHEDULER", "TIMEZONE"]

    def require_auth(self, env_map: dict) -> bool:
        return True

    def func_message(self, message_text, **kwargs):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        # 正则匹配
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        return None

    async def failed(
        self,
        task: "TaskHeader",
        receiver: "Location",
        exception,
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
        **kwargs,
    ):
        _meta = task.task_sign.notify(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Timer Run Failed: {exception}",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
            memory_able=True,
            response_snapshot=True,
        )
        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_sign=_meta,
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"{__plugin_name__} Run failed {exception}",
                    )
                ],
            ),
        )

    async def callback(
        self,
        task: "TaskHeader",
        receiver: "Location",
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
        **kwargs,
    ):
        return None

    async def run(
        self,
        task: "TaskHeader",
        receiver: "Location",
        arg: dict,
        env: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
    ):
        """
        处理message，返回message
        """
        argument = SetAlarm.model_validate(arg)
        _meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response="Timer Run Success",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )

        logger.debug("Plugin --set_alarm {} minutes".format(argument.delay))
        # 这里假设您的任务应该在UTC时间下执行，如果需要在其他时区执行，根据实际情况更改tz变量
        tz = pytz.timezone(get_localzone().key)
        run_time = datetime.datetime.now() + datetime.timedelta(minutes=argument.delay)
        logger.debug(run_time)
        # 将本地时间转换为设定的时区
        run_time = tz.localize(run_time)
        logger.debug(run_time)
        SCHEDULER.add_job(
            func=send_notify,
            id=receiver.uid,
            trigger="date",
            replace_existing=True,
            misfire_grace_time=1000,
            run_date=run_time,
            args=[
                task.receiver.platform,
                _meta.model_dump(),
                task.sender.model_dump(),
                receiver.model_dump(),
                receiver.user_id,
                receiver.chat_id,
                argument.content,
            ],
        )
        await Task(queue=receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,  # 继承发送者
                receiver=receiver,  # 因为可能有转发，所以可以单配
                task_sign=_meta,
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"🍖 The alarm is now set,just wait for {argument.delay} min",
                    )
                ],
            )
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Set a timed reminder (only for minutes)",
    usage="直接说，以分钟为单位，如：10分钟后提醒我吃饭",
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(SetAlarm), tool=AlarmTool)},
    homepage="https://github.com/LlmKira",
)
