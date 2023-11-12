# -*- coding: utf-8 -*-
# @Time    : 2023/11/13 上午2:00
# @Author  : sudoskys
# @File    : pydantic_function.py
# @Software: PyCharm
from pprint import pprint

from llmkira.sdk.schema import Function
from pydantic import BaseModel, ConfigDict, field_validator, Field


class Alarm(BaseModel):
    """
    Set a timed reminder (only for minutes)
    """
    delay: int = Field(5, description="The delay time, in minutes")
    content: str = Field(..., description="reminder content")
    model_config = ConfigDict(extra="allow")

    @field_validator("delay")
    def delay_validator(cls, v):
        if v < 0:
            raise ValueError("delay must be greater than 0")
        return v


result = Function.parse_from_pydantic(schema_model=Alarm, plugin_name="set_alarm_reminder")

pprint(result)
