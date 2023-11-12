# -*- coding: utf-8 -*-
from pydantic import field_validator, ConfigDict

__package__name__ = "llmkira.extra.plugins.alarm"
__plugin_name__ = "set_alarm_reminder"
__openapi_version__ = "20231111"

from llmkira.sdk.func_calling import verify_openapi_version
from llmkira.sdk.schema import Function

verify_openapi_version(__package__name__, __openapi_version__)

import datetime
import re

from loguru import logger
from pydantic import BaseModel

from llmkira.receiver.aps import SCHEDULER
from llmkira.schema import RawMessage
from llmkira.sdk.func_calling import PluginMetadata, BaseTool
from llmkira.sdk.func_calling.schema import FuncPair
from llmkira.task import Task, TaskHeader

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from llmkira.sdk.schema import TaskBatch

alarm = Function(name=__plugin_name__, description="Set a timed reminder (only for minutes)")
alarm.add_property(
    property_name="delay",
    property_description="The delay time, in minutes",
    property_type="integer",
    required=True
)
alarm.add_property(
    property_name="content",
    property_description="reminder content",
    property_type="string",
    required=True
)


class Alarm(BaseModel):
    delay: int
    content: str
    model_config = ConfigDict(extra="allow")

    @field_validator("delay")
    def delay_validator(cls, v):
        if v < 0:
            raise ValueError("delay must be greater than 0")
        return v


async def send_notify(_platform, _meta, _sender: dict, _receiver: dict, _user, _chat, _content: str):
    await Task(queue=_platform).send_task(
        task=TaskHeader(
            sender=TaskHeader.Location.model_validate(_sender),  # 继承发送者
            receiver=TaskHeader.Location.model_validate(_receiver),  # 因为可能有转发，所以可以单配
            task_meta=TaskHeader.Meta.model_validate(_meta),
            message=[
                RawMessage(
                    user_id=_user,
                    chat_id=_chat,
                    text=_content
                )
            ]
        )
    )


class AlarmTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = False
    function: Function = alarm
    keywords: list = ["闹钟", "提醒", "定时", "到点", '分钟']
    pattern: Optional[re.Pattern] = re.compile(r"(\d+)(分钟|小时|天|周|月|年)后提醒我(.*)")
    require_auth: bool = True

    # env_required: list = ["SCHEDULER", "TIMEZONE"]

    def pre_check(self):
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

    async def failed(self,
                     task: "TaskHeader", receiver: "TaskHeader.Location",
                     exception,
                     env: dict,
                     arg: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                     **kwargs
                     ):
        _meta = task.task_meta.reply_notify(
            plugin_name=__plugin_name__,
            callback=[TaskHeader.Meta.Callback.create(
                name=__plugin_name__,
                function_response=f"Timer Run Failed: {exception}",
                tool_call_id=pending_task.get_batch_id()
            )],
            write_back=True,
            release_chain=True
        )
        await Task(queue=receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_meta=_meta,
                message=[
                    RawMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"{__plugin_name__} Run failed {exception}"
                    )
                ]
            )
        )

    async def callback(self,
                       task: "TaskHeader", receiver: "TaskHeader.Location",
                       env: dict,
                       arg: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                       **kwargs
                       ):
        return None

    async def run(self,
                  task: "TaskHeader", receiver: "TaskHeader.Location",
                  arg: dict, env: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                  ):
        """
        处理message，返回message
        """
        _set = Alarm.model_validate(arg)
        _meta = task.task_meta.reply_message(
            plugin_name=__plugin_name__,
            callback=[
                TaskHeader.Meta.Callback.create(
                    name=__plugin_name__,
                    function_response="Timer Run Success",
                    tool_call_id=pending_task.get_batch_id()
                )
            ]
        )

        logger.debug("Plugin:set alarm {} minutes later".format(_set.delay))
        SCHEDULER.add_job(
            func=send_notify,
            id=str(receiver.user_id),
            trigger="date",
            replace_existing=True,
            misfire_grace_time=1000,
            run_date=datetime.datetime.now() + datetime.timedelta(minutes=_set.delay),
            args=[
                task.receiver.platform,
                _meta.model_dump(),
                task.sender.model_dump(), receiver.model_dump(),
                receiver.user_id, receiver.chat_id,
                _set.content
            ]
        )
        await Task(queue=receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,  # 继承发送者
                receiver=receiver,  # 因为可能有转发，所以可以单配
                task_meta=_meta,
                message=[
                    RawMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"🍖 The alarm is now set,just wait for {_set.delay} min"
                    )
                ]
            )
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Set a timed reminder (only for minutes)",
    usage="set_alarm_reminder 10 minutes later remind me to do something",
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=alarm, tool=AlarmTool)
    },
    homepage="https://github.com/LlmKira"
)
