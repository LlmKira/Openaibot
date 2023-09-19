# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午6:11
# @Author  : sudoskys
# @File    : alarm.py
# @Software: PyCharm
import datetime
import re

from loguru import logger
from pydantic import validator, BaseModel

from receiver.aps import SCHEDULER
from schema import TaskHeader, RawMessage
from sdk.endpoint.openai import Function
from sdk.func_call import BaseTool, listener
from task import Task

__plugin_name__ = "set_alarm_reminder"

alarm = Function(name=__plugin_name__, description="Set a timed reminder")
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

    class Config:
        extra = "allow"

    @validator("delay")
    def delay_validator(cls, v):
        if v < 0:
            raise ValueError("delay must be greater than 0")
        return v


@listener(function=alarm)
class AlarmTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = False
    function: Function = alarm
    keywords: list = ["闹钟", "提醒", "定时", "到点", '分钟']
    pattern = re.compile(r"(\d+)(分钟|小时|天|周|月|年)后提醒我(.*)")

    def pre_check(self):
        return True

    def func_message(self, message_text):
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

    async def failed(self, platform, task, receiver, reason):
        try:
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    sender=task.sender,
                    receiver=receiver,
                    task_meta=TaskHeader.Meta(callback_forward=True,
                                              callback=TaskHeader.Meta.Callback(
                                                  role="function",
                                                  name=__plugin_name__
                                              ),
                                              ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text=f"🍖 {__plugin_name__}操作失败了！原因：{reason}"
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _set = Alarm.parse_obj(arg)

            async def _send(receiver, _set):
                await Task(queue=receiver.platform).send_task(
                    task=TaskHeader(
                        sender=task.sender,  # 继承发送者
                        receiver=receiver,  # 因为可能有转发，所以可以单配
                        task_meta=TaskHeader.Meta(callback_forward=True,
                                                  callback=TaskHeader.Meta.Callback(
                                                      role="function",
                                                      name=__plugin_name__
                                                  ),
                                                  ),
                        message=[
                            RawMessage(
                                user_id=receiver.user_id,
                                chat_id=receiver.chat_id,
                                text=_set.content
                            )
                        ]
                    )
                )

            logger.debug("set alarm {} minutes later".format(_set.delay))
            SCHEDULER.add_job(
                func=_send,
                trigger="date",
                run_date=datetime.datetime.now() + datetime.timedelta(minutes=_set.delay),
                args=[receiver, _set]
            )
            try:
                SCHEDULER.start()
            except Exception as e:
                pass
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason=str(e))
