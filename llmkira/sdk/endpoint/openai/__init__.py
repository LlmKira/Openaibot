# -*- coding: utf-8 -*-
# @Time    : 2023/8/15 下午10:34
# @Author  : sudoskys
# @File    : base.py
# @Software: PyCharm
__version__ = "0.0.1"

from typing import Union, List, Optional, Literal

import httpx
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, root_validator, validator, Field, BaseSettings

from .action import Tokenizer, TokenizerObj
from ..tee import Driver
from ...error import ValidationError
from ...network import request
from ...schema import Message, Function

load_dotenv()

MODEL = Literal[
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4-0613",
    "gpt-4",
    "gpt-4-32k",
    "gpt-4-32k-0613",
    # "gpt-3.5-turbo-instruct",
    # "gpt-4-0314",
    # "gpt-3.5-turbo-0301",
    # "gpt-4-32k-0314"
    # Do not use 0314. See: https://platform.openai.com/docs/guides/gpt/function-calling
]


class OpenaiResult(BaseModel):
    class Usage(BaseModel):
        prompt_tokens: int
        completion_tokens: int
        total_tokens: int

    class Choices(BaseModel):
        index: int
        message: Message = None
        finish_reason: str
        """The reason the model stopped generating tokens. This will be stop if the model hit a natural stop point or 
        a provided stop sequence, length if the maximum number of tokens specified in the request was reached, 
        content_filter if content was omitted due to a flag from our content filters, tool_calls if the model called 
        a tool, or function_call (deprecated) if the model called a function."""

        delta: dict = None

        @property
        def sign_function(self):
            return bool(
                "function_call" in self.finish_reason
                or
                "tool_calls" in self.finish_reason
            )

    id: Optional[str] = Field(default=None, alias="request_id")
    object: str
    created: int
    model: str
    system_fingerprint: str = Field(default=None, alias="system_prompt_fingerprint")
    choices: List[Choices]
    usage: Usage

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @property
    def result_type(self):
        return self.object

    @property
    def default_message(self):
        return self.choices[0].message


class Openai(BaseModel):
    class Proxy(BaseSettings):
        proxy_address: str = Field(None, env="OPENAI_API_PROXY")  # "all://127.0.0.1:7890"

        class Config:
            env_file = '.env'
            env_file_encoding = 'utf-8'
            case_sensitive = True
            arbitrary_types_allowed = True

    messages: List[Message]
    config: Driver
    """模型信息和配置"""
    temperature: Optional[float] = 1
    """温度"""
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    """暂时不打算用的流式"""
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[dict] = None
    user: Optional[str] = None

    response_format: Optional[dict] = Field(default=None, alias="response_format")
    seed: Optional[int] = Field(default=None, alias="seed")

    # 函数
    # functions: Optional[List[Function]] = Field(default=None, alias="functions")
    # function_call: Optional[str] = None
    tools: Optional[List[Function]] = Field(default=None, alias="tools")
    tool_choice: Optional[Union[dict, Literal["auto", "none"]]] = None

    # 用于调试
    echo: Optional[bool] = False

    @property
    def model(self):
        return self.config.model

    @property
    def get_request_data(self):
        _arg = self.dict(exclude_none=True, exclude={"config", "echo"})
        _arg["model"] = self.model
        return _arg

    def get_proxy_settings(self):
        proxy = self.Proxy()
        return proxy

    @staticmethod
    def get_model_list():
        return MODEL.__args__

    @staticmethod
    def get_token_limit(model: str):
        v = 2048
        if "gpt-3.5" in model:
            v = 4096
        elif "gpt-4" in model:
            v = 8192
        if "-16k" in model:
            v = v * 4
        elif "-32k" in model:
            v = v * 8
        return v

    @validator("presence_penalty")
    def check_presence_penalty(cls, v):
        if not (2 > v > -2):
            raise ValidationError("presence_penalty must be between -2 and 2")
        return v

    @validator("stop")
    def check_stop(cls, v):
        if isinstance(v, list) and len(v) > 4:
            raise ValidationError("stop list length must be less than 4")
        return v

    @validator("temperature")
    def check_temperature(cls, v):
        if not (2 > v > 0):
            raise ValidationError("temperature must be between 0 and 2")
        return v

    @root_validator
    def check_root(cls, values):
        return values

    @staticmethod
    def parse_single_reply(response: dict) -> Message:
        """
        解析响应
        :param response:
        :return:
        """
        # check
        if not response.get("choices"):
            raise ValidationError("Message is empty")

        _message = Message.parse_obj(response.get("choices")[0].get("message"))
        return _message

    @staticmethod
    def parse_usage(response: dict):
        if not response.get("usage"):
            raise ValidationError("usage is empty")
        return response.get("usage").get("total_tokens")

    async def create(self,
                     **kwargs
                     ) -> OpenaiResult:
        """
        请求
        :return:
        """
        """
        curl https://api.openai.com/v1/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -d '{"model": "text-davinci-003", "prompt": "Say this is a test", "temperature": 0, "max_tokens": 7}'
        """
        # check
        num_tokens_from_messages = TokenizerObj.num_tokens_from_messages(
            messages=self.messages,
            model=self.model,
        )
        if num_tokens_from_messages > self.get_token_limit(self.model):
            raise ValidationError("messages_box num_tokens > max_tokens")
        # Clear tokenizer encode cache
        TokenizerObj.clear_cache()
        # 返回请求
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"Bearer {self.config.api_key}",
            "api-key": f"{self.config.api_key}",
        }
        if self.config.org_id:
            headers["Openai-Organization"] = self.config.org_id
        try:
            _response = await request(
                method="POST",
                url=self.config.endpoint,
                data=self.get_request_data,
                headers=headers,
                proxy=self.get_proxy_settings().proxy_address,
                json_body=True
            )
            return_result = OpenaiResult.parse_obj(_response)
        except httpx.ConnectError as e:
            logger.error(f"Openai connect error: {e}")
            raise e
        if self.echo:
            logger.info(f"Openai response: {return_result}")
        return return_result
