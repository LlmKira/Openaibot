# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: manager.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from contextlib import asynccontextmanager

from loguru import logger
from typing import Union, Optional, Dict, Any

from utils.data import DictUpdate
from utils.setting.config import AppConfig
from utils.setting.user import ChatSystemConfig, UserConfig

from Component.data import file_client, mongo_client
from Component.cache import CacheNameSpace


# TODO Manager使用新数据库类和数据类重写，请转移到 Manager Handler

class ConfigManager:
    """
    运行配置管理器
    """

    def __init__(self):
        self.client = file_client

    @asynccontextmanager
    async def retrieve_data(self, file_path: str = "Config/config.json"):
        try:
            _read = await self.client.async_read_json(file_path=file_path)
            if not _read:
                _read = ChatSystemConfig()
            else:
                _read = ChatSystemConfig(**_read)
            yield _read
            await self.client.async_write_json(file_path=file_path, data=_read.json())
        finally:
            pass


class ServiceManager(object):
    """
    外设组件服务管理器
    """

    def __init__(self):
        self.client = file_client

    @asynccontextmanager
    async def retrieve_data(self, file_path: str = "Config/service.json"):
        try:
            _read = await self.client.async_read_json(file_path=file_path)
            if not _read:
                _read = AppConfig()
            else:
                _read = AppConfig(**_read)
            yield _read
            await self.client.async_write_json(file_path=file_path, data=_read.json())
        finally:
            pass


class UserManager(object):
    def __init__(self, db_name: str = "openai_bot", collection: str = "user"):
        """
        """
        self.client = mongo_client.with_database(db_name).with_collection(collection)

    async def read(self, uid: int):
        _read = await self.client.find_one({"uid": uid})
        if not _read:
            _data = UserConfig(uid=uid)
        else:
            _data = UserConfig(uid=uid, **_read)
        return _data

    async def save(self, data: UserConfig):
        # 如果存在记录则更新
        if await self.client.find_one({"uid": data.uid}):
            await self.client.update_one({"uid": data.uid}, {"$set": data.dict()})
        # 如果不存在记录则插入
        else:
            await self.client.insert_one(data.dict())


class GroupManager(object):
    def __init__(self, db_name: str = "openai_bot", collection: str = "group"):
        self.client = mongo_client.with_database(db_name).with_collection(collection)

    async def read(self, uid: int):
        _read = await self.client.find_one({"uid": uid})
        if not _read:
            _data = UserConfig(uid=uid)
        else:
            _data = UserConfig(uid=uid, **_read)
        return _data

    async def save(self, data: UserConfig):
        # 如果存在记录则更新
        if await self.client.find_one({"uid": data.uid}):
            await self.client.update_one({"uid": data.uid}, {"$set": data.dict()})
        # 如果不存在记录则插入
        else:
            await self.client.insert_one(data.dict())


class Header(object):
    def __init__(self, uid):
        self._uid = str(uid)
        self.client = CacheNameSpace("header")

    async def get(self):
        _usage = self.client.read_data(f"{self._uid}")
        if not _usage:
            return ""
        else:
            return str(_usage)

    async def set(self, context):
        return self.client.read_data(f"{self._uid}", context)


"""

class OpenaiApiKey:

    def __init__(self, file_path: str = "./Config/api_keys.json"):
        self.file_path = file_path

    def _save_key(self, config: dict) -> None:
        with ThreadingLock.get_instance():
            with open(self.file_path, "w+", encoding="utf8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

    def __get_config(self):
        now_table = DefaultData.default_keys()
        if pathlib.Path(self.file_path).exists():
            with ThreadingLock.get_instance():
                with open(self.file_path, encoding="utf-8") as f:
                    _config = json.load(f)
                    DictUpdate.dict_update(now_table, _config)
                    _config = now_table
            return _config
        else:
            return now_table

    def get_key(self) -> Optional[list]:
        _config = self.__get_config()
        return _config.get('OPENAI_API_KEY')

    def add_key(self, key: str) -> str:
        _config = self.__get_config()
        _config['OPENAI_API_KEY'].append(key)
        _config["OPENAI_API_KEY"] = list(set(_config["OPENAI_API_KEY"]))
        self._save_key(config=_config)
        return key

    def pop_key(self, key: str) -> Optional[str]:
        _config = self.__get_config()
        if key not in _config['OPENAI_API_KEY']:
            return
        _config['OPENAI_API_KEY'].remove(key)
        _config["OPENAI_API_KEY"] = list(set(_config["OPENAI_API_KEY"]))
        self._save_key(config=_config)
        return key

    def warn_api_key(self, key: str, log: str = "unknown error happened"):
        self.pop_key(key)
        _masked_key = DefaultData.mask_middle(key, 4)
        logger.warning(f"Api Key be Removed:{_masked_key},because {log}")

    def check_api_key(self, resp: dict, auth: str):
        # 读取
        _error = ["invalid_request_error", "billing_not_active", "billing_not_active", "insufficient_quota"]
        # 弹出
        ERROR = resp.get("error")
        if ERROR:
            logg = None
            pop_key = False
            if ERROR.get('type') == "billing_not_active":
                pop_key = True
                logg = f"认证资料过期: --type billing_not_active --auth {DefaultData.mask_middle(auth, 4)}"
            if ERROR.get('type') == "insufficient_quota":
                pop_key = True
                logg = f"Overused ApiKey:  --type insufficient_quota --auth {DefaultData.mask_middle(auth, 4)}"
            if ERROR.get('code') == "invalid_api_key":
                pop_key = True
                logg = f"非法 ApiKey: --type invalid_api_key --auth {DefaultData.mask_middle(auth, 4)}"
            if pop_key:
                self.warn_api_key(key=auth, log=logg)
            else:
                logg = f"{ERROR.get('type')}"
                logger.warning(logg)
"""
