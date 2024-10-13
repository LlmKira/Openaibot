import os

import requests
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel


class ProviderError(Exception):
    pass


class Credential(BaseModel):
    api_key: str
    api_endpoint: str
    api_model: str
    api_tool_model: str = "gpt-4o-mini"

    @classmethod
    def from_provider(cls, token, provider_url):
        """
        使用 token POST 请求 provider_url 获取用户信息
        :param token: 用户 token
        :param provider_url: provider url
        :return: 用户信息
        :raises HTTPError: 请求失败
        :raises JSONDecodeError: 返回数据解析失败
        :raises ProviderError: provider 返回错误信息
        """
        response = requests.post(provider_url, data={"token": token})
        response.raise_for_status()
        user_data = response.json()
        if user_data.get("error"):
            raise ProviderError(user_data["error"])
        return cls(
            api_key=user_data["api_key"],
            api_endpoint=user_data["api_endpoint"],
            api_model=user_data["api_model"],
            api_tool_model=user_data.get("api_tool_model", "gpt-4o-mini"),
        )


load_dotenv()

if os.getenv("GLOBAL_OAI_KEY") and os.getenv("GLOBAL_OAI_ENDPOINT"):
    logger.warning("\n\n**Using GLOBAL credential**\n\n")
    global_credential = Credential(
        api_key=os.getenv("GLOBAL_OAI_KEY"),
        api_endpoint=os.getenv("GLOBAL_OAI_ENDPOINT"),
        api_model=os.getenv("GLOBAL_OAI_MODEL", "gpt-4o-mini"),
        api_tool_model=os.getenv("GLOBAL_OAI_TOOL_MODEL", "gpt-4o-mini"),
    )
else:
    global_credential = None
