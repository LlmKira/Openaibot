# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
from typing import Literal, Optional

from pydantic import BaseModel, root_validator, Field

from sdk.error import ValidationError


class Message(BaseModel):
    class FunctionCall(BaseModel):
        name: str
        arguments: str

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: Optional[str] = None
    # speaker
    name: Optional[str] = Field(None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    # AI generated function call
    function_call: Optional[FunctionCall] = None

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        if not values.get("content") and not values.get("function_call"):
            raise ValidationError("sdk param validator:content or function_call must be specified")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}

    @classmethod
    def create_task_message_list(cls, task_desc, refer, role: str = None):
        """
        生成task
        """
        if not role:
            role = "[Scene: chatting in real time]\nPlease complete the order according to the task description refer to given information"
        return [
            cls(
                role="system",
                content=role,
            ),
            cls(
                role="assistant",
                content=refer,
                name="information"
            ),
            cls(
                role="user",
                content=task_desc,
                name="task"
            ),
            cls(
                role="assistant",
                content="ok , i will complete the tasks you give",
            )
        ]


class Function(BaseModel):
    """
    函数定义体。
    供外部模组定义并注册函数
    """

    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}

    name: str = Field(None, description="函数名称", regex=r"^[a-zA-Z0-9_]+$")
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")
    required: list[str] = []

    def add_property(self, property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.required.append(property_name)

    def parse_schema_to_properties(self, schema: BaseModel):
        """
        解析pydantic的schema
        传入一个pydantic的schema，解析成properties
        参数可以被数据模型所定义
        """
        self.parameters.properties = schema.schema()["properties"]
