from typing import List, Union, Type
from typing import Literal
from typing import Optional

from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import ConfigDict, BaseModel, Field, field_validator, model_validator
from pydantic import SecretStr
from tenacity import retry, stop_after_attempt, wait_exponential

from llmkira.openai._excption import raise_error, NetworkError, UnexpectedFormatError
from .cell import (
    Tool,
    ToolChoice,
    Message,
    AssistantMessage,
    CommonTool,
    ToolCall,
    ToolMessage,
    UserMessage,
    SystemMessage,
)

VISION = ("gpt-4-vision", "gpt-4-turbo", "claude-3", "gpt-4o")


class OpenAICredential(BaseModel):
    api_key: SecretStr
    base_url: str = "https://api.openai.com/v1"
    default_headers: dict = {"x-foo": "true"}
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    model: Optional[str] = None
    _session: AsyncSession = None

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    async def get_session(self, timeout: int = 180, update_headers: dict = None):
        if update_headers is None:
            update_headers = {}
        if not self.session:
            self.session = AsyncSession(
                timeout=timeout,
                headers={
                    "Accept": "*/*",
                    "Authorization": f"Bearer {self.api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                impersonate="edge101",
            )
        self.session.headers.update(update_headers)
        return self.session


class OpenAIResult(BaseModel):
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
        delta: Optional[dict] = None
        model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

        @property
        def need_action(self):
            return bool(
                "function_call" == self.finish_reason
                or "tool_calls" == self.finish_reason
            )

    id: str = Field(default="default")
    model: str
    # system_fingerprint: str = Field(default=None, alias="system_prompt_fingerprint")
    choices: List[Choices]
    usage: Usage
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @property
    def default_message(self) -> "AssistantMessage":
        return self.choices[0].message


class OpenAI(BaseModel):
    class ResponseFormat(BaseModel):
        type: Literal["json_object", "text"] = "text"

    model: str
    messages: List[
        Union[Message, AssistantMessage, ToolMessage, UserMessage, SystemMessage]
    ] = Field(..., description="Messages")

    @field_validator("messages")
    def check_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        return v

    temperature: Optional[float] = 1
    n: Optional[int] = 1
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = Field(None)
    """Up to 4 sequences where the API will stop generating further tokens."""

    @field_validator("stop")
    def check_stop(cls, v):
        if isinstance(v, list):
            assert (
                len(v) <= 4
            ), "Up to 4 sequences where the API will stop generating further tokens."
        return v

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
    response_format: Optional[ResponseFormat] = None
    """{ "type": "json_object" } Must be one of text or json_object."""
    tools: Optional[List[Union[Tool, CommonTool, Type[BaseModel]]]] = None
    """Tools"""

    @field_validator("tools")
    def check_tools(cls, v):
        if v:
            v = [
                Tool(function=i)
                if isinstance(i, BaseModel) and not isinstance(i, Tool)
                else i
                for i in v
            ]
            assert all(
                isinstance(i, Tool) for i in v
            ), "tools must be a list of Tool objects"
        return v

    tool_choice: Optional[Union["ToolChoice", Literal["auto", "none"]]] = None
    """Choice"""
    model_config = ConfigDict(arbitrary_types_allowed=False, extra="allow")

    @staticmethod
    def make_url(base_url: str):
        return base_url.strip().rstrip("/") + "/chat/completions"

    @model_validator(mode="after")
    def check_vision(self):
        if not self.model.startswith(VISION):
            logger.info(
                f"Try to remove the image content part from the messages, because the model is not supported {self.model}"
            )
            for message in self.messages:
                if isinstance(message, UserMessage) and isinstance(
                    message.content, list
                ):
                    message.content = [
                        content
                        for content in message.content
                        if content.type != "image_url"
                    ]
        return self

    @retry(
        stop=stop_after_attempt(3),
        reraise=True,
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def request(self, session: OpenAICredential) -> OpenAIResult:
        """
        :param session: Credential
        :return: OpenaiResult
        :raises: NetworkError, UnexpectedError, UnexpectedFormatError
        """
        logger.debug(f"Requesting to {self.model}")
        client = await session.get_session()
        client: AsyncSession
        model = session.model if session.model else self.model
        # Build request
        kwargs = self.model_dump(exclude_none=True)
        kwargs["model"] = model
        try:
            response = await client.post(
                url=self.make_url(session.base_url),
                headers={
                    **session.default_headers,
                    **{"Authorization": f"Bearer {session.api_key.get_secret_value()}"},
                },
                json=kwargs,
            )
        except Exception as exc:
            logger.exception(f"Request Error: {exc}")
            raise NetworkError("Some error occurred while making request.")
        try:
            jsoned = response.json()
        except Exception as exc:
            logger.exception(f"Server send a invalid response. \n{exc}")
            raise NetworkError("Server send a invalid response cant be parsed.")
        if jsoned.get("error"):
            raise_error(status_code=response.status_code, error_data=jsoned["error"])
        if response.status_code != 200:
            _message = jsoned.get("message", "No message details")
            raise UnexpectedFormatError(
                f"Unexpected response code {response.status_code} --message {_message}"
            )
        try:
            return OpenAIResult.model_validate(jsoned)
        except Exception as exc:
            logger.exception(exc)
            raise UnexpectedFormatError("Unexpected response format")

    @retry(
        stop=stop_after_attempt(3),
        reraise=True,
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def extract(
        self, response_model: Union[Type[BaseModel]], session: OpenAICredential
    ):
        """
        Extract the result from the response
        :param response_model: BaseModel
        :param session: OpenAICredential
        :return: BaseModel
        :raises NetworkError, UnexpectedFormatError, RuntimeError: The response model is not matched with the result
        """
        self.n = 1
        self.response_format = None
        tool = Tool(function=response_model)
        self.tools = [tool]
        self.tool_choice = ToolChoice(function=tool.function)
        result = await self.request(session)
        try:
            tool_call = ToolCall.model_validate(result.choices[0].message.tool_calls[0])
            logger.debug(f"Extracted: {tool_call}")
            return response_model.model_validate(tool_call.function.json_arguments)
        except Exception as exc:
            logger.error(f"extract:{exc}")
            raise RuntimeError("The response model is not matched with the result")
