from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pymongo
from dotenv import load_dotenv
from loguru import logger
from montydb import errors as monty_errors, MontyClient, set_storage
from pydantic import model_validator, Field
from pydantic_settings import BaseSettings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.errors import ServerSelectionTimeoutError


class DatabaseClient(ABC):
    @abstractmethod
    def ping(self):
        pass

    @abstractmethod
    def update_db_collection(self, db_name, collection_name):
        pass

    @abstractmethod
    def insert_one(self, document: Dict[str, Any]):
        pass

    @abstractmethod
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_one(
        self, filter_query: Dict[str, Any], update_query: Dict[str, Any]
    ) -> bool:
        pass


class MontyDatabaseClient(DatabaseClient):
    def __init__(self, db_name=None, collection_name=None):
        local_repo = ".montydb"
        set_storage(
            local_repo, storage="lightning"
        )  # required, to set lightning as engine
        self.client = MontyClient(local_repo)
        self.update_db_collection(db_name, collection_name)

    def update_db_collection(self, db_name, collection_name):
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        return self

    def ping(self):
        return True  # MontyDB doesn't have a ping method.

    def insert_one(self, document: Dict[str, Any]):
        try:
            self.collection.insert_one(document)
            return True
        except monty_errors.MontyError:
            return False

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.collection.find_one(query)

    def update_one(
        self, filter_query: Dict[str, Any], update_query: Dict[str, Any]
    ) -> bool:
        result = self.collection.update_one(filter_query, update_query)
        return result.matched_count > 0


class MongoDbClient(DatabaseClient):
    def __init__(self, uri, db_name=None, collection_name=None):
        self.client = pymongo.MongoClient(uri)
        self.update_db_collection(db_name, collection_name)

    def update_db_collection(self, db_name, collection_name):
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        return self

    def ping(self):
        try:
            self.client.admin.command("ping")
        except ConnectionFailure:
            return False
        return True

    def insert_one(self, document: Dict[str, Any]):
        result = self.collection.insert_one(document)
        return result.inserted_id

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = self.collection.find_one(query)
        return result

    def update_one(
        self, filter_query: Dict[str, Any], update_query: Dict[str, Any]
    ) -> bool:
        result = self.collection.update_one(filter_query, {"$set": update_query})
        return result.modified_count > 0


class MongoDb(BaseSettings):
    mongodb_dsn: str = Field("mongodb://localhost:27017", validation_alias="MONGO_DSN")
    """MongoDB 配置"""
    available: bool = True

    @model_validator(mode="after")
    def mongodb_validator(self):
        try:
            client = MongoClient(
                self.mongodb_dsn, serverSelectionTimeoutMS=1000
            )  # 设置超时时间
            client.admin.command("ping")
            # 获取服务器信息
            client.server_info()
            # 尝试执行需要管理员权限的命令
            client.admin.command("listDatabases")
        except ServerSelectionTimeoutError:
            self.available = False
            logger.warning(
                f"\n🍀MongoDB Connection Error -- timeout when connecting to {self.mongodb_dsn}"
            )
        except pymongo.errors.OperationFailure:
            self.available = False
            logger.warning("\n🍀MongoDB Connection Error -- insufficient permissions")
        except Exception as e:
            self.available = False
            logger.warning(f"\n🍀MongoDB Connection Error -- error {e}")
        else:
            logger.success(f"\n🍀MongoDB Connection Success --dsn {self.mongodb_dsn}")
        return self


load_dotenv()
MongoSetting = MongoDb()

if MongoSetting.available:
    global_doc_client = MongoDbClient(MongoSetting.mongodb_dsn, "test", "test")
else:
    global_doc_client = MontyDatabaseClient("test", "test")
    logger.info("🍀MontyDB is used as a fallback database.")
