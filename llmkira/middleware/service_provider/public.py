# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午11:46
# @Author  : sudoskys
# @File    : public.py
# @Software: PyCharm
import time

from loguru import logger
from pydantic import BaseModel, Field

from config import provider_settings
from llmkira.sdk.cache.redis import cache
from . import resign_provider
from .schema import BaseProvider, ProviderException
from ...sdk.endpoint import Driver

QUOTA = 24
WHITE_LIST = []
if provider_settings.get("public", default=None) is not None:
    QUOTA = provider_settings.public.get("public_quota", default=24)
    WHITE_LIST = provider_settings.public.get("public_white_list", default=[])
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
        if not Driver.from_public_env().available:
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
            _data: UserToday = UserToday.model_validate(read)
            if str(_data.time) != str(date):
                await cache.set_data(self.__database_key(uid=uid), value=UserToday().model_dump())
                return True
            else:
                if _data.count > times:
                    return False
                if _data.count < times:
                    _data.count += 1
                    await cache.set_data(self.__database_key(uid=uid), value=_data.model_dump())
                    return True
        else:
            _data = UserToday()
            await cache.set_data(self.__database_key(uid=uid), value=_data.model_dump())
            return True
        return False

    async def request_driver(self, uid, token) -> Driver:
        return Driver.from_public_env()
