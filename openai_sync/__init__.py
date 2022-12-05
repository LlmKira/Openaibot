# -*- coding: utf-8 -*-
# @Time    : 12/5/22 9:54 PM
# @FileName: __init__.py
# @Software: PyCharm
# @Github    ：sudoskys
import os
import json
from .network import request


def _load_api():
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".api_url.json")
    )
    if os.path.exists(path):
        with open(path, encoding="utf8") as f:
            return json.loads(f.read())
    else:
        raise FileNotFoundError("NotFind:api_url.json")


API = _load_api()


class Completion(object):
    def __init__(self, api_key: str, proxy_url: str = ""):
        self.__api_key = api_key
        self.__proxy = proxy_url

    def get_api_key(self):
        return self.__api_key

    async def create(self, model: str = "text-davinci-003", prompt: str = "Say this is a test", temperature: int = 0,
                     max_tokens: int = 7):
        """
        得到一个对话
        :param model: 模型
        :param prompt: 提示
        :param temperature: unknown
        :param max_tokens: 返回数量
        :return:
        """
        """
        curl https://api.openai.com/v1/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -d '{"model": "text-davinci-003", "prompt": "Say this is a test", "temperature": 0, "max_tokens": 7}'
        """
        api = API["v1"]["completions"]
        params = {"model": model, "prompt": prompt, "temperature": temperature, "max_tokens": max_tokens}
        return await request("POST", api["url"], data=params, auth=self.__api_key, json_body=True, proxy=self.__proxy)
