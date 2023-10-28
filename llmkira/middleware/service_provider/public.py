# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午11:46
# @Author  : sudoskys
# @File    : public.py
# @Software: PyCharm
import time

from loguru import logger
from pydantic import BaseModel, Field

from config import settings
from llmkira.cache.redis import cache
from llmkira.sdk.endpoint.openai import Openai
from . import resign_provider
from .schema import BaseProvider, ProviderException

QUOTA = 24
WHITE_LIST = []
if settings.get("public", default=None) is not None:
    QUOTA = settings.public.get("public_quota", default=24)
    WHITE_LIST = settings.public.get("public_white_list", default=[])
    logger.debug(f"🍦 Public Provider Config Loaded, QUOTA({QUOTA}) WHITE_LIST({WHITE_LIST})")


class UserToday(BaseModel):
    count: int = 0
    time: int = Field(default=time.strftime("%Y%m%d", time.localtime()))


@resign_provider()
class PublicProvider(BaseProvider):
    name = "public"

    def __database_key(self, uid: str):
        return f"driver:{self.name}:{uid}"

    def config_docs(self):
        return "ConfigDocs:Its a public provider"

    async def authenticate(self, uid, token, status) -> bool:
        _pass = await self.check_times(times=QUOTA, uid=uid)
        if not _pass:
            raise ProviderException(
                "You are using a public instance. You triggered data flood protection today",
                provider=self.name
            )
        if not Openai.Driver.from_public_env().available:
            raise ProviderException(
                "You are using a public instance\nBut current instance apikey unavailable",
                provider=self.name
            )
        return True

    async def check_times(self, times: int, uid: str):
        date = time.strftime("%Y%m%d", time.localtime())
        read = await cache.read_data(self.__database_key(uid=uid))
        if uid in WHITE_LIST:
            return True
        logger.debug(f"🍦 Public Provider Check Times UID({uid}) Read({read})")
        if read:
            _data: UserToday = UserToday.parse_obj(read)
            if str(_data.time) != str(date):
                await cache.set_data(self.__database_key(uid=uid), value=UserToday().dict())
                return True
            else:
                if _data.count > times:
                    return False
                if _data.count < times:
                    _data.count += 1
                    await cache.set_data(self.__database_key(uid=uid), value=_data.dict())
                    return True
        else:
            _data = UserToday()
            await cache.set_data(self.__database_key(uid=uid), value=_data.dict())
            return True
        return False

    async def request_driver(self, uid, token) -> Openai.Driver:
        return Openai.Driver.from_public_env()
