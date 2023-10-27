# -*- coding: utf-8 -*-
# @Time    : 2023/10/27 下午8:24
# @Author  : sudoskys
# @File    : private.py
# @Software: PyCharm
import time

from pydantic import BaseModel, Field

from config import settings
from llmkira.sdk.endpoint.openai import Openai
from . import resign_provider
from .schema import BaseProvider, ProviderException

WHITE_LIST = settings.get("private_white_list", default=[])


class UserToday(BaseModel):
    count: int = 0
    time: int = Field(default=time.strftime("%Y%m%d", time.localtime()))


@resign_provider()
class PrivateProvider(BaseProvider):
    name = "private"

    def __database_key(self, uid: str):
        return f"driver:{self.name}:{uid}"

    def config_docs(self):
        return "This instance is only available to authorized users :)"

    async def authenticate(self, uid, token, status) -> bool:
        if uid in WHITE_LIST:
            return True
        if not Openai.Driver.from_public_env().available:
            raise ProviderException(
                "\nYou are using a public and free instance.\nThe current instance key is not configured.",
                provider=self.name
            )
        raise ProviderException(
            "This is a private instance."
            "\nPlease contact the administrator to apply for a private instance."
            f"\n You id is {uid}",
            provider=self.name
        )

    async def request_driver(self, uid, token) -> Openai.Driver:
        return Openai.Driver.from_public_env()
