# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:42
import os
import pathlib
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

from .elara_runtime import ElaraClientAsyncWrapper
from .lmdb_runtime import LMDBClientAsyncWrapper
from .redis_runtime import RedisClientWrapper
from .runtime_schema import singleton, BaseRuntime


@singleton
class LMDBRuntime(BaseRuntime):
    client: Optional["LMDBClientAsyncWrapper"] = None
    init_already = False
    dsn = None

    @staticmethod
    def check_client_dsn(dsn):
        """
        :raise ValueError: Please Use Local Path
        """
        if "://" in dsn:
            raise ValueError("Please Use Local Path")

    def check_client(self):
        if self.dsn is None:
            pathlib.Path().cwd().joinpath(".cache").mkdir(exist_ok=True)
            self.dsn = pathlib.Path().cwd().joinpath(".cache") / "lmdb_dir"
        self.client = LMDBClientAsyncWrapper(str(self.dsn))
        logger.debug(f"🍩 LMDBClientAsyncWrapper Loaded --folder {self.dsn}")
        return True

    def init_client(self, verbose=False):
        if verbose:
            logger.info("Try To Connect To LMDBClientAsyncWrapper")
        self.check_client()
        self.init_already = True
        assert isinstance(
            self.client, LMDBClientAsyncWrapper
        ), f"LMDBClientAsyncWrapper type error {type(self.client)}"
        return self.client

    def get_client(self) -> "LMDBClientAsyncWrapper":
        if not self.init_already:
            self.init_client()
            assert isinstance(
                self.client, LMDBClientAsyncWrapper
            ), f"LMDBClientAsyncWrapper error {type(self.client)}"
        else:
            assert isinstance(
                self.client, LMDBClientAsyncWrapper
            ), f"Inited LMDBClientAsyncWrapper error {type(self.client)}"
        return self.client


@singleton
class ElaraRuntime(BaseRuntime):
    client: Optional["ElaraClientAsyncWrapper"] = None
    init_already = False
    dsn = None

    @staticmethod
    def check_client_dsn(dsn):
        """
        :raise ValueError: Please Use Local Path
        """
        if "://" in dsn:
            raise ValueError("Please Use Local Path")

    def check_client(self):
        if self.dsn is None:
            pathlib.Path().cwd().joinpath(".cache").mkdir(exist_ok=True)
            self.dsn = pathlib.Path().cwd().joinpath(".cache") / "elara.db"
        self.client = ElaraClientAsyncWrapper(str(self.dsn))
        logger.debug(f"🍩 ElaraClientWrapper Loaded --dsn {self.dsn}")
        return True

    def init_client(self, verbose=False):
        if verbose:
            logger.info("Try To Connect To ElaraClient")
        self.check_client()
        self.init_already = True
        assert isinstance(
            self.client, ElaraClientAsyncWrapper
        ), f"ElaraClient type error {type(self.client)}"
        return self.client

    def get_client(self) -> "ElaraClientAsyncWrapper":
        if not self.init_already:
            self.init_client()
            assert isinstance(
                self.client, ElaraClientAsyncWrapper
            ), f"ElaraClient error {type(self.client)}"
        else:
            assert isinstance(
                self.client, ElaraClientAsyncWrapper
            ), f"Inited ElaraClient error {type(self.client)}"
        return self.client


@singleton
class RedisRuntime(BaseRuntime):
    client: Optional["RedisClientWrapper"] = None
    init_already = False
    dsn = None

    @staticmethod
    def check_client_dsn(dsn):
        import redis

        r = redis.from_url(dsn)
        assert r.ping() is True

    def check_client(self):
        load_dotenv()
        self.dsn = os.getenv("REDIS_DSN", "redis://localhost:6379/0")
        try:
            self.check_client_dsn(self.dsn)
        except Exception as e:
            logger.debug(
                f"\n⚠️ Redis Disconnect, Please set `REDIS_DSN` env  --error {e} --dsn {self.dsn}"
            )
            return False
        else:
            logger.debug(f"🍩 RedisClientWrapper Loaded --dsn {self.dsn}")
            self.client = RedisClientWrapper(self.dsn)
            if self.dsn == "redis://localhost:6379/0":
                logger.warning(
                    "\n⚠️ You are using a non-password-protected local REDIS database."
                )
            return True

    def init_client(self, verbose=False) -> "RedisClientWrapper":
        if verbose:
            logger.info("Try To Connect To Cache")
        self.check_client()
        self.init_already = True
        assert isinstance(
            self.client, RedisClientWrapper
        ), f"Cache type error {type(self.client)}"
        return self.client

    def get_client(self) -> "RedisClientWrapper":
        if not self.init_already:
            self.init_client()
            assert isinstance(
                self.client, RedisClientWrapper
            ), f"Cache type error {type(self.client)}"
        else:
            assert isinstance(
                self.client, RedisClientWrapper
            ), f"Inited cache type error {type(self.client)}"
        return self.client


if RedisRuntime().check_client():
    global_cache_runtime: BaseRuntime = RedisRuntime()
else:
    global_cache_runtime: BaseRuntime = LMDBRuntime()
