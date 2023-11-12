# -*- coding: utf-8 -*-
# @Time    : 2023/8/15 下午10:34
# @Author  : sudoskys
# @File    : base.py
# @Software: PyCharm
from pydantic import field_validator, ConfigDict, model_validator

__version__ = "0.0.1"

from typing import Union, List, Optional, Literal, Type

import httpx
import pydantic
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

from ..schema import LlmResult, LlmRequest
from ..tee import Driver
from ..tokenizer import get_tokenizer
from ...adapter import SCHEMA_GROUP, SingleModel
from ...error import ValidationError
from ...network import request
from ...schema import Message, Function, ToolChoice, AssistantMessage, Tool, BaseFunction, ToolMessage

load_dotenv()


class OpenaiResult(LlmResult):
    class Usage(BaseModel):
        prompt_tokens: int
        completion_tokens: int
        total_tokens: int

    class Choices(BaseModel):
        index: int
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
                or
                "tool_calls" == self.finish_reason
            )

    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str = Field(default=None, alias="system_prompt_fingerprint")
    choices: List[Choices]
    usage: Usage
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @property
    def result_type(self):
        return self.object

    @property
    def default_message(self):
        return self.choices[0].message


class Openai(LlmRequest):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    _config: Driver = PrivateAttr(default=None)
    """模型信息和配置"""
    messages: List[Union[Message, Type[Message]]]
    temperature: Optional[float] = 1
    n: Optional[int] = 1
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    """基础设置"""
    stream: Optional[bool] = False
    """暂时不打算用的流式"""
    logit_bias: Optional[dict] = None
    """暂时不打算用的logit_bias"""
    user: Optional[str] = None
    """追踪 User"""
    response_format: Optional[dict] = None
    """回复指定的格式，See: https://platform.openai.com/docs/api-reference/chat/create"""
    # 函数
    functions: Optional[List[Function]] = None
    """deprecated"""
    function_call: Optional[Union[BaseFunction, Literal["auto", "none"]]] = None
    """deprecated"""
    # 工具
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[ToolChoice, Literal["auto", "none"]]] = None
    """工具调用"""

    # 注意，我们
    """
    如果是 vison ，需要转换消息。
    注意验证 tool choice 的字段。
    """

    @model_validator(mode="before")
    @classmethod
    def fix_tool(cls, values):
        if not values.get("tools"):
            values["tools"] = None
        else:
            assert isinstance(values.get("tools"), list)

        if not values.get("functions"):
            values["functions"] = None
        else:
            assert isinstance(values.get("functions"), list)
        if values.get("tools") and values.get("functions"):
            logger.warning("sdk param validator:'functions' and 'tools' cannot both be provided. ignoring 'functions'")
            values["functions"] = None
            values["function_call"] = None
        """Deprecated by openai"""
        return values

    @property
    def schema_map(self) -> dict:
        return {
            "model": True,
            "messages": True,
            "temperature": True,
            "top_p": True,
            "n": True,
            "stop": True,
            "max_tokens": True,
            "seed": True,
            "presence_penalty": True,
            "frequency_penalty": True,
            "stream": True,
            "logit_bias": True,
            "user": True,
            "response_format": True,
            "functions": True,
            "function_call": True,
            "tools": True,
            "tool_choice": True,
        }

    def create_params(self):
        # 获取已经传递的工具模型
        _done = []
        _need = []
        for message in self.messages:
            if isinstance(message, ToolMessage):
                _done.append(message.tool_call_id)
        for message in self.messages:
            if isinstance(message, AssistantMessage):
                if message.tool_calls:
                    for tool in message.tool_calls:
                        _need.append(tool.id)
        # 修补
        _need_fix = list(set(_need) - set(_done))
        _new_messages = []
        for message in self.messages:
            _new_messages.append(message)
            if isinstance(message, AssistantMessage):
                if message.tool_calls:
                    for tool in message.tool_calls:
                        if tool.id in _need_fix:
                            _new_messages.append(
                                ToolMessage(
                                    tool_call_id=tool.id,
                                    content="[On Queue]"
                                )
                            )
        self.messages = _new_messages
        #
        _arg = self.model_dump(
            exclude_none=True,
            include=self.schema_map
        )
        assert "messages" in _arg, "messages is required"
        _arg["model"] = self.model
        _arg = {
            k: v
            for k, v in _arg.items()
            if v is not None
        }
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

    async def create(self,
                     **kwargs
                     ) -> OpenaiResult:
        """
        请求
        :return:
        """
        """
        Docs:https://platform.openai.com/docs/api-reference/chat/create
        """
        # Check Token Limit
        num_tokens_from_messages = get_tokenizer(model_name=self.model).num_tokens_from_messages(
            messages=self.messages,
            model=self.model,
        )
        if num_tokens_from_messages > SCHEMA_GROUP.get_token_limit(model_name=self.model):
            raise ValidationError("messages_box num_tokens > max_tokens")
        # 返回请求
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"Bearer {self._config.api_key}",
            "api-key": f"{self._config.api_key}",
        }
        if self._config.org_id:
            headers["Openai-Organization"] = self._config.org_id
        try:
            logger.debug(f"[Openai request] {self.create_params()}")
            _response = await request(
                method="POST",
                url=self._config.endpoint,
                data=self.create_params(),
                headers=headers,
                proxy=self.proxy_address(),
                json_body=True
            )
            assert _response, ValidationError("response is empty")
            logger.debug(f"[Openai response] {_response}")
            return_result = OpenaiResult.model_validate(_response).ack()
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
            llm_model="chatglm3",
            token_limit=4096,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="function_call",
            exception=None
        ),
        SingleModel(
            llm_model="chatglm3-16k",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="function_call",
            exception=None
        ),
    ]
)

SCHEMA_GROUP.add_model(
    models=[
        SingleModel(
            llm_model="gpt-3.5-turbo-1106",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo",
            token_limit=4096,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-16k",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-0613",
            token_limit=4096,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-3.5-turbo-16k-0613",
            token_limit=16384,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-4",
            token_limit=8192,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-4-32k",
            token_limit=32768,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-4-0613",
            token_limit=8192,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-4-vision-preview",
            token_limit=128000,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        ),
        SingleModel(
            llm_model="gpt-4-1106-preview",
            token_limit=128000,
            request=Openai,
            response=OpenaiResult,
            schema_type="openai",
            func_executor="tool_call",
            exception=None
        )
    ]
)
