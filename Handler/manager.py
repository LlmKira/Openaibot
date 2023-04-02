# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: manager.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from contextlib import asynccontextmanager

from loguru import logger
# from typing import Union, Optional, Dict, Any
# from utils.data import DictUpdate
from utils.chat import MessageToolBox
from utils.setting.config import AppConfig
from utils.setting.user import ChatSystemConfig, UserConfig, GroupConfig
from utils.setting.keymanager import ApiKeySettings
from Component.data import file_client, mongo_client
from Component.cache import CacheNameSpace


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
            _read.update({"uid": uid})
            _data = UserConfig(uid=uid)
            _data = _data.parse_obj(_read)
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
            _data = GroupConfig(uid=uid)
        else:
            _read.update({"uid": uid})
            _data = GroupConfig(uid=uid)
            _data = _data.parse_obj(_read)
        return _data

    async def save(self, data: GroupConfig):
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
        return self.client.set_data(f"{self._uid}", context)


class ApiKeyManager(object):
    ERROR_MESSAGES = {
        "billing_not_active": "认证资料过期: --type billing_not_active --auth {}",
        "insufficient_quota": "Overused ApiKey: --type insufficient_quota --auth {}",
        "invalid_api_key": "Invalid ApiKey: --type invalid_api_key --auth {}"
    }

    def __init__(self, file_path):
        self.client = file_client
        self.file_path = file_path

    async def get_keys(self) -> ApiKeySettings:
        _key_data = await self.client.async_read_json(file_path=self.file_path)
        _object = ApiKeySettings(**_key_data)
        return _object

    async def set_keys(self, keys: ApiKeySettings):
        await self.client.async_write_json(file_path=self.file_path, data=keys.json())

    async def warn_openai_key(self, key: str, log: str = "unknown error happened"):
        _object = await self.get_keys()
        _masked_key = MessageToolBox.mask_middle(key, 4)
        logger.warning(f"Api Key be Removed:{_masked_key},because {log}")
        _object.Openai.pop(key, None)
        await self.set_keys(_object)

    async def callback_api_key(self, resp: dict, auth: str):
        _error_type = ["invalid_request_error", "billing_not_active", "billing_not_active", "insufficient_quota"]
        # 弹出
        error = resp.get("error")
        if error:
            error_type = error.get('type')
            if error_type in self.ERROR_MESSAGES:
                logg = self.ERROR_MESSAGES[error_type].format(MessageToolBox.mask_middle(auth, 4))
                await self.warn_openai_key(key=auth, log=logg)
            else:
                logg = f"{error.get('type')} -- {error.get('message')}"
                logger.warning(logg)
