import os
from urllib.parse import urlparse

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
        )


def split_setting_string(input_string):
    if not isinstance(input_string, str):
        return None
    segments = input_string.split("$")

    # 检查链接的有效性
    def is_valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    # 开头为链接的情况
    if is_valid_url(segments[0]) and len(segments) >= 3:
        return segments[:3]
    # 第二个元素为链接，第一个元素为字符串的情况
    elif (
        len(segments) == 2
        and not is_valid_url(segments[0])
        and is_valid_url(segments[1])
    ):
        return segments
    # 其他情况
    else:
        return None


load_dotenv()

if os.getenv("GLOBAL_OAI_KEY") and os.getenv("GLOBAL_OAI_ENDPOINT"):
    logger.warning("\n\n**Using GLOBAL credential**\n\n")
    global_credential = Credential(
        api_key=os.getenv("GLOBAL_OAI_KEY"),
        api_endpoint=os.getenv("GLOBAL_OAI_ENDPOINT"),
        api_model=os.getenv("GLOBAL_OAI_MODEL", "gpt-3.5-turbo"),
    )
else:
    global_credential = None
