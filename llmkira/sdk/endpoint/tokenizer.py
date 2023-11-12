# -*- coding: utf-8 -*-
# @Time    : 2023/11/9 下午3:50
# @Author  : sudoskys
# @File    : tokenizer.py
# @Software: PyCharm
import json
from typing import Union, List, Type

import tiktoken
from loguru import logger
from pydantic import BaseModel


def _pydantic_type(_message):
    if isinstance(_message, BaseModel):
        return _message.model_dump()
    return _message


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schema import Message


class BaseTokenizer(object):
    def num_tokens_from_messages(self, messages: List[Union[dict, BaseModel, Type[BaseModel]]], model: str) -> int:
        """Return the number of tokens used by a list of messages_box."""
        raise NotImplementedError


class OpenaiTokenizer(BaseTokenizer):
    def num_tokens_from_messages(self,
                                 messages: List[Union[dict, BaseModel, Type[BaseModel]]],
                                 model: str
                                 ) -> int:
        """Return the number of tokens used by a list of messages_box."""
        if hasattr(messages, "request_final"):
            messages: "Message"
            messages = messages.request_final(schema_model=model)
        messages: List[dict] = [_pydantic_type(message) for message in messages]
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = 1  # if there's a name, the role is omitted
            logger.warning(
                f"""num_tokens_from_messages() is not implemented for model {model}."""
                """:) If you use a no-openai model, """
                """you can [one-api](https://github.com/songquanpeng/one-api) project handle token usage."""
                """or issue https://github.com/LlmKira/Openaibot/issues to request support."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                if isinstance(value, list):
                    value = json.dumps(value, ensure_ascii=False)
                if value is None:
                    continue
                _tokens = len(encoding.encode(value))
                num_tokens += _tokens
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


def get_tokenizer(model_name: str) -> BaseTokenizer:
    if model_name.startswith("gpt"):
        return OpenaiTokenizer()
    elif model_name.startswith("."):
        raise NotImplementedError(f"sdk.endpoint.get_tokenizer() is not implemented for model {model_name}.")
    else:
        logger.warning(
            f"sdk.endpoint.get_tokenizer() is not implemented for model {model_name}.\n "
            f"Using default tokenizer.[cl100k]"
        )
        return OpenaiTokenizer()
