# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午10:18
# @Author  : sudoskys
# @File    : client.py
# @Software: PyCharm
import time
from abc import ABC
from typing import List, Optional

from pymongo.errors import DuplicateKeyError

from llmkira.cache.mongo import mongo_client
from .schema import UserCost, UserConfig

__DB_NAME__ = "llm_bot"


class Client(ABC):
    client = mongo_client.with_database(__DB_NAME__)

    def use_collection(self, collection_name: str):
        return self.client.with_collection(collection_name)


class UserCostClient(Client):
    def __init__(self):
        self.client = self.use_collection("user_cost")

    async def insert(self, data: UserCost):
        await self.client.insert_one(data.dict())
        return data

    async def read_by_uid(self, uid: str) -> List[UserCost]:
        _data_list = await self.client.find_many({"uid": uid})
        return [UserCost(**_data) for _data in _data_list]


class UserConfigClient(Client):
    def __init__(self):
        self.client = self.use_collection("user_config")

    async def update(self, uid: str, data: UserConfig, validate: bool = True) -> UserConfig:
        if validate:
            assert data.uid == uid, "update validate:uid 不一致"
        data.__dict__.update({
            "last_use_time": int(time.time()),
            "uid": uid}
        )
        await self.client.collection.create_index(
            [("uid", 1)], unique=True
        )
        try:
            await self.client.insert_one(data.dict())
        except DuplicateKeyError:
            await self.client.update_one({"uid": uid}, {"$set": data.dict()})
        return data

    async def read_by_uid(self, uid: str) -> Optional[UserConfig]:
        _raw_data = await self.client.find_one({"uid": uid})
        if not _raw_data:
            return None
        return UserConfig(**_raw_data)
