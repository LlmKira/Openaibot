# -*- coding: utf-8 -*-
# @Time    : 12/29/22 12:30 PM
# @FileName: Manager.py
# @Software: PyCharm
# @Github    ：sudoskys
# 全局共享管理器
from typing import Union, Optional

from loguru import logger
from pydantic import BaseModel

from utils.Data import ServiceData, RedisConfig, DefaultData, DictUpdate

_bot_profile = {}


# TODO Manager使用新数据库类和数据类重写，请转移到 Manager Handler

def _init_():
    global _bot_profile
    try:
        _bot_profile.get("1")
    except:
        _bot_profile = {}


_init_()


class ProfileReturn(BaseModel):
    bot_id: Union[str, int] = 0
    bot_name: str = ""
    mentions: Optional[str] = None


class ProfileManager(object):
    global _bot_profile

    @staticmethod
    def name_generate(first_name, last_name):
        # 反转内容
        _bot_full_name = f"{first_name}{last_name}"
        _bot_split_name = _bot_full_name.split()
        _bot_split_name: list
        _bot_name = _bot_full_name if not len(_bot_split_name) > 1 else _bot_split_name[1]
        _bot_name = _bot_name if _bot_name else "Assistant"
        _bot_name = _bot_name[:12]
        return _bot_name

    def access_api(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="sign_api", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init API Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="sign_api"))

    def access_telegram(self, bot_name: str = None, bot_id: int = None, mentions: str = None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="telegram", bot_id=bot_id, bot_name=bot_name, mentions=mentions)
            logger.success(f"Init Telegram Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="telegram"))

    def access_qq(self, bot_name=None, bot_id=None, init=False):
        global _bot_profile
        if init:
            _profile = self.set_bot_profile(domain="qq", bot_id=bot_id, bot_name=bot_name)
            logger.success(f"Init QQ Bot Profile: {_profile}")
            return _profile
        else:
            return ProfileReturn(**self.get_bot_profile(domain="qq"))

    def set_bot_profile(self, domain=None, bot_id=None, bot_name=None, **kwargs):
        global _bot_profile
        if not domain:
            raise Exception("ProfileManager:Missing Name")
        if not bot_id or not bot_name:
            raise Exception("BOT:NONE")
        _data = {"bot_id": bot_id, "bot_name": bot_name}
        _data.update(**kwargs)
        _bot_profile[domain] = _data
        return _data

    def get_bot_profile(self, domain=None):
        global _bot_profile
        if not _bot_profile.get(domain):
            raise Exception("ProfileManager:Missing Name")
        return _bot_profile.get(domain)


class Header(object):
    def __init__(self, uid):
        self._uid = str(uid)
        _service = ServiceData.get_key()
        _redis_conf = _service["redis"]
        _redis_config = RedisConfig(**_redis_conf)
        self.__Data = DataWorker(host=_redis_config.host,
                                 port=_redis_config.port,
                                 db=_redis_config.db,
                                 password=_redis_config.password,
                                 prefix="Open_Ai_bot_user_head")

    def get(self):
        _usage = self.__Data.getKey(f"{self._uid}")
        if not _usage:
            return ""
        else:
            return str(_usage)

    def set(self, context):
        return self.__Data.setKey(f"{self._uid}", context)


class Style(object):
    def __init__(self, uid):
        self._uid = str(uid)
        _service = ServiceData.get_key()
        _redis_conf = _service["redis"]
        _redis_config = RedisConfig(**_redis_conf)
        self.__Data = DataWorker(host=_redis_config.host,
                                 port=_redis_config.port,
                                 db=_redis_config.db,
                                 password=_redis_config.password,
                                 prefix="Open_Ai_bot_user_style")

    def get(self):
        _usage = self.__Data.getKey(f"{self._uid}")
        if not _usage:
            return {}
        else:
            return _usage

    def set(self, context):
        return self.__Data.setKey(f"{self._uid}", context)


class UserManager(object):
    def __init__(self, uid: int):
        """
        """
        self._uid = str(abs(uid))
        load_csonfig()
        self.user = _csonfig["User"].get(self._uid)
        if not self.user:
            self.user = {}
        self._user = DefaultData.defaultUser()
        DictUpdate.dict_update(self._user, self.user)
        self._renew(self._user)

    def _renew(self, item):
        """
        UpDTA进去
        :param item:
        :return:
        """
        load_csonfig()
        # 更新默认设置的必要结构
        _item = item
        _reply = self._user
        DictUpdate.dict_update(_reply, _item)
        _csonfig["User"][self._uid] = _reply
        save_csonfig()

    def save(self, setting: dict = None):
        if not setting:
            return None
        _reply = self._user
        DictUpdate.dict_update(_reply, setting)
        return self._renew(_reply)

    def read(self, key) -> Union[any]:
        _item = self._user
        return _item.get(key)

    def reset(self):
        self._renew(DefaultData.defaultUser())
        return True


class GroupManager(object):
    def __init__(self, uid: int):
        """
        """
        self._uid = str(abs(uid))
        load_csonfig()
        self.user = _csonfig["Group"].get(self._uid)
        if not self.user:
            self.user = {}
        self._user = DefaultData.defaultGroup()
        DictUpdate.dict_update(self._user, self.user)
        self._renew(self._user)

    def _renew(self, item):
        """
        UpDTA进去
        :param item:
        :return:
        """
        load_csonfig()
        # 更新默认设置的必要结构
        _item = item
        _reply = self._user
        DictUpdate.dict_update(_reply, _item)
        _csonfig["Group"][self._uid] = _reply
        save_csonfig()

    def save(self, setting: dict = None):
        if not setting:
            return None
        _reply = self._user
        DictUpdate.dict_update(_reply, setting)
        return self._renew(_reply)

    def read(self, key) -> Union[any]:
        _item = self._user
        return _item.get(key)
