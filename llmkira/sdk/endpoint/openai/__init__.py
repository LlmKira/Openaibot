# -*- coding: utf-8 -*-
# @Time    : 2023/8/15 下午10:34
# @Author  : sudoskys
# @File    : base.py
# @Software: PyCharm
from pydantic import field_validator, ConfigDict

__version__ = "0.0.1"

from typing import Union, List, Optional, Literal

import httpx
import pydantic
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

from ..schema import LlmResult, LlmRequest
from ..tee import Driver
from ...adapter import SCHEMA_GROUP, SingleModel
from ...error import ValidationError
from ...network import request
from ...schema import (
    Message,
    ToolChoice,
    AssistantMessage,
    Tool,
    ToolMessage,
)

load_dotenv()


class OpenaiResult(LlmResult):
    class Usage(BaseModel):
        prompt_tokens: int
        completion_tokens: int
        total_tokens: int

    class Choices(BaseModel):
        message: AssistantMessage
        finish_reason: str
        """
        The reason the model stopped generating tokens. This will be stop if the model hit a natural stop point or
        a provided stop sequence, length if the maximum number of tokens specified in the request was reached,
        content_filter if content was omitted due to a flag from our content filters, tool_calls if the model called
        a tool, or function_call (deprecated) if the model called a function.
        """
        delta: dict = None

        @property
        def sign_function(self):
            return bool(
                "function_call" == self.finish_reason
                or "tool_calls" == self.finish_reason
            )

    model: str
    system_fingerprint: str = Field(default=None, alias="system_prompt_fingerprint")
    choices: List[Choices]
    usage: Usage
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @property
    def default_message(self):
        return self.choices[0].message


class Openai(LlmRequest):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    _config: Driver = PrivateAttr(default=None)
    """模型信息和配置"""
    messages: List["Message"]
    n: Optional[int] = 1
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    """Max Tokens"""
    presence_penalty: Optional[float] = None
    """Presence Penalty"""
    frequency_penalty: Optional[float] = None
    """Frequency Penalty"""
    seed: Optional[int] = None
    """Seed"""
    stream: Optional[bool] = False
    """Stream"""
    logit_bias: Optional[dict] = None
    """Logit Bias"""
    response_format: Optional[dict] = None
    """回复指定的格式，See: https://platform.openai.com/docs/api-reference/chat/create"""
    # 工具
    tools: Optional[List["Tool"]] = None
    tool_choice: Optional[Union["ToolChoice", Literal["auto", "none"]]] = None
    """工具调用"""

    @property
    def config(self):
        return self._config

    @staticmethod
    def sort_insert_message(message_list: List[Message]):
        """
        排序插入
        :param message_list:
        :return:
        """
        origin_message_list = message_list.copy()
        ordered_message_list = []
        child_resp = {}
        for message in message_list:
            if isinstance(message, ToolMessage):
                if message.tool_call_id in child_resp:
                    child_resp[message.tool_call_id].append(message)
                else:
                    child_resp[message.tool_call_id] = [message]
                message_list.remove(message)
        # 在不存在 child 的情况下，修补
        for message in message_list:
            # 存放一个
            ordered_message_list.append(message)
            if isinstance(message, AssistantMessage) and message.tool_calls:
                # 需要修补的消息
                for tool in message.tool_calls:
                    if tool.id in child_resp:
                        # 匹配到了 对应的 child
                        ordered_message_list.extend(child_resp[tool.id])
                    else:
                        # 没有匹配到对应的 child
                        ordered_message_list.append(
                            ToolMessage(tool_call_id=tool.id, content="[On Queue]")
                        )
        # 修补完毕
        if len(origin_message_list) != len(ordered_message_list):
            logger.warning(
                f"message_list is not match, origin:{origin_message_list}, orderd:{ordered_message_list}"
            )
        return ordered_message_list

    def create_params(self):
        # 修补消息
        self.messages = self.sort_insert_message(message_list=self.messages)
        # 获取已经传递的工具模型
        _arg = self.model_dump(exclude_none=True, include=self.schema_map)
        assert "messages" in _arg, "messages is required"
        _arg["model"] = self.model
        _arg = {k: v for k, v in _arg.items() if v is not None}
        return _arg

    @field_validator("presence_penalty")
    def check_presence_penalty(cls, v):
        if not (2 > v > -2):
            raise ValidationError("presence_penalty must be between -2 and 2")
        return v

    @field_validator("stop")
    def check_stop(cls, v):
        if isinstance(v, list) and len(v) > 4:
            raise ValidationError("stop list length must be less than 4")
        return v

    @field_validator("temperature")
    def check_temperature(cls, v):
        if not (2 > v > 0):
            raise ValidationError("temperature must be between 0 and 2")
        return v

    async def create(self, **kwargs) -> OpenaiResult:
        """
        请求
        :return:
        """
        """
        Docs:https://platform.openai.com/docs/api-reference/chat/create
        """
        # Do not check token limit, 没有意义
        # 返回请求
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"Bearer {self.config.api_key}",
            "api-key": f"{self.config.api_key}",
        }
        if self.config.org_id:
            headers["Openai-Organization"] = self.config.org_id
        try:
            logger.debug(f"[Openai request] {self.create_params()}")
            _response = await request(
                method="POST",
                url=self.config.endpoint,
                data=self.create_params(),
                headers=headers,
                proxy=self.proxy_address(),
                json_body=True,
            )
            assert _response, ValidationError("response is empty")
            logger.debug(f"[Openai response] {_response}")
            return_result = OpenaiResult.model_validate(_response)
        except httpx.ConnectError as e:
            logger.error(f"[Openai connect error] {e}")
            raise e
        except pydantic.ValidationError as e:
            logger.error(f"[Api format error] {e}")
            raise e
        if self.echo:
            logger.info(f"[Openai Raw response] {return_result}")
        return return_result


SCHEMA_GROUP.add_model(
    models=[
        SingleModel(
            llm_model="gpt-3.5-turbo-1106",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo",
            token_limit=4096,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-16k",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-0613",
            token_limit=4096,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-16k-0613",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-4",
            token_limit=8192,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-4-32k",
            token_limit=32768,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-4-0613",
            token_limit=8192,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-4-vision-preview",
            token_limit=128000,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="unsupported",
            exception=None,
        ),
        SingleModel(
            llm_model="gpt-4-1106-preview",
            token_limit=128000,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None,
        ),
    ]
)
