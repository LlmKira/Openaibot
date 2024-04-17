# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午10:56
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import time
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from app.components.credential import Credential
from app.const import DBNAME
from llmkira.doc_manager import global_doc_client


class ChatCost(BaseModel):
    user_id: str
    cost_token: int = 0
    endpoint: str = ""
    cost_model: str = ""
    produce_time: int = time.time()


class GenerateHistory(object):
    def __init__(self, db_name: str = DBNAME, collection: str = "cost_history"):
        """ """
        self.client = global_doc_client.update_db_collection(
            db_name=db_name, collection_name=collection
        )

    async def save(self, history: ChatCost):
        return self.client.insert_one(history.model_dump(mode="json"))


class User(BaseModel):
    user_id: str
    last_use_time: int = time.time()
    credential: Optional[Credential] = None


class UserManager(object):
    def __init__(self, db_name: str = DBNAME, collection: str = "user"):
        """ """
        self.client = global_doc_client.update_db_collection(
            db_name=db_name, collection_name=collection
        )

    async def read(self, user_id: str) -> User:
        user_id = str(user_id)
        database_read = self.client.find_one({"user_id": user_id})
        if not database_read:
            logger.info(f"Create new user: {user_id}")
            return User(user_id=user_id)
        # database_read.update({"user_id": user_id})
        return User.model_validate(database_read)

    async def save(self, user_model: User):
        user_model = user_model.model_copy(update={"last_use_time": int(time.time())})
        # 如果存在记录则更新
        if self.client.find_one({"user_id": user_model.user_id}):
            return self.client.update_one(
                {"user_id": user_model.user_id},
                {"$set": user_model.model_dump(mode="json")},
            )
        # 如果不存在记录则插入
        else:
            return self.client.insert_one(user_model.model_dump(mode="json"))


COST_MANAGER = GenerateHistory()
USER_MANAGER = UserManager()


async def record_cost(
    user_id: str, cost_token: int, endpoint: str, cost_model: str, success: bool = True
):
    try:
        await COST_MANAGER.save(
            ChatCost(
                user_id=user_id,
                produce_time=int(time.time()),
                endpoint=endpoint,
                cost_model=cost_model,
                cost_token=cost_token if success else 0,
            )
        )
    except Exception as exc:
        logger.error(f"🔥 record_cost error: {exc}")


if __name__ == "__main__":
    pass
