# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:42
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import os
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from .base import singleton, BaseRuntime
from .mongo import MongoClientWrapper
from .redis import RedisClientWrapper
from ..utils import sync


@singleton
class MongodbRuntime(BaseRuntime):
    client: Optional["MongoClientWrapper"] = None
    init_already = False
    dsn = None

    @staticmethod
    def check_mongodb_dsn(dsn):
        client = MongoClientWrapper(dsn)
        assert sync(client.ping()), f"MongoDB {dsn} Disconnect"

    def check_mongodb(self):
        load_dotenv()
        self.dsn = os.getenv('MONGODB_DSN', "mongodb://admin:8a8a8a@localhost:27017/?authSource=admin")
        try:
            self.check_mongodb_dsn(self.dsn)
        except Exception as e:
            logger.error(f'\n⚠️ Mongodb DISCONNECT, pls set MONGODB_DSN in .env\n--error {e} \n--dsn {self.dsn}')
            raise e
        else:
            logger.success(f'🍩 MongoClientWrapper Loaded --dsn {self.dsn}')
            self.client = MongoClientWrapper(self.dsn)
            if "mongodb://admin:8a8a8a@" in self.dsn:
                logger.warning(
                    f"\n⚠️ You Are Using The Default MongoDB Password"
                    f"\nMake Sure You Handle The Port `27017` And Set Firewall Rules"
                )

    def init_mongodb(self,
                     verbose=False):
        if verbose:
            logger.info("Try To Connect To MongoDb")
        self.check_mongodb()
        self.init_already = True
        assert isinstance(self.client, MongoClientWrapper), f"MongoDb type error {type(self.client)}"
        return self.client

    def get_mongodb(self) -> "MongoClientWrapper":
        if not self.init_already:
            self.init_mongodb()
            assert isinstance(self.client, MongoClientWrapper), f"MongoDb error {type(self.client)}"
        else:
            assert isinstance(self.client, MongoClientWrapper), f"Inited MongoDb error {type(self.client)}"
        return self.client


@singleton
class RedisRuntime(BaseRuntime):
    client: Optional["RedisClientWrapper"] = None
    init_already = False
    dsn = None

    @staticmethod
    def check_redis_dsn(dsn):
        import redis
        r = redis.from_url(dsn)
        assert r.ping() is True

    def check_redis(self):
        load_dotenv()
        self.dsn = os.getenv('REDIS_DSN', 'redis://localhost:6379/0')
        try:
            self.check_redis_dsn(self.dsn)
        except Exception as e:
            logger.error(f'\n⚠️ Redis Disconnect, Please set `REDIS_DSN` env  --error {e} --dsn {self.dsn}')
            raise e
        else:
            logger.success(f'🍩 RedisClientWrapper Loaded --dsn {self.dsn}')
            self.client = RedisClientWrapper(self.dsn)
            if self.dsn == 'redis://localhost:6379/0':
                logger.warning("\n⚠️ You are using a non-password-protected local REDIS database.")

    def init_cache(self,
                   verbose=False) -> "RedisClientWrapper":
        if verbose:
            logger.info("Try To Connect To Cache")
        self.check_redis()
        self.init_already = True
        assert isinstance(self.client, RedisClientWrapper), f"Cache type error {type(self.client)}"
        return self.client

    def get_redis(self) -> "RedisClientWrapper":
        if not self.init_already:
            self.init_cache()
            assert isinstance(self.client, RedisClientWrapper), f"Cache type error {type(self.client)}"
        else:
            assert isinstance(self.client, RedisClientWrapper), f"Inited cache type error {type(self.client)}"
        return self.client


global_cache_runtime: RedisRuntime = RedisRuntime()
global_mongodb_runtime: MongodbRuntime = MongodbRuntime()
