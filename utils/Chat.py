# -*- coding: utf-8 -*-
# @Time    : 12/9/22 8:15 AM
# @FileName: Chat.py
# @Software: PyCharm
# @Github    ：sudoskys
import json
import time
from typing import Union

import pathlib

from utils.Data import RedisConfig
from utils.Data import DefaultData, DataWorker, DictUpdate, Usage_Data, Service_Data
from loguru import logger

service = Service_Data.get_key()
redis_conf = service["redis"]
redis_config = RedisConfig(**redis_conf)
# 工具数据类型
DataUtils = DataWorker(host=redis_config.host,
                       port=redis_config.port,
                       db=redis_config.db,
                       password=redis_config.password,
                       prefix="Open_Ai_bot_")

MsgsRecordUtils = DataWorker(host=redis_config.host,
                             port=redis_config.port,
                             db=redis_config.db,
                             password=redis_config.password,
                             prefix="Open_Ai_bot_msg_record")
PhotoRecordUtils = DataWorker(host=redis_config.host,
                              port=redis_config.port,
                              db=redis_config.db,
                              password=redis_config.password,
                              prefix="Open_Ai_bot_photo_record")

ConfigUtils = DataWorker(host=redis_config.host,
                         port=redis_config.port,
                         db=redis_config.db,
                         password=redis_config.password,
                         prefix="Open_Ai_bot_config")

global _csonfig


# IO
def load_csonfig():
    global _csonfig
    now_table = DefaultData.defaultConfig()
    _csonfig = ConfigUtils.getKey("config")
    DictUpdate.dict_update(now_table, _csonfig)
    _csonfig = now_table
    return _csonfig


def save_csonfig():
    ConfigUtils.setKey("config", _csonfig)
    with open("./Config/config.json", "w+", encoding="utf8") as f:
        json.dump(_csonfig, f, indent=4, ensure_ascii=False)


class Header(object):
    def __init__(self, uid):
        self._uid = str(uid)
        _service = Service_Data.get_key()
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
        _service = Service_Data.get_key()
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


class Utils(object):
    @staticmethod
    def forget_me(user_id, group_id):
        from llm_kira.utils.data import MsgFlow
        _cid = DefaultData.composing_uid(user_id=user_id, chat_id=group_id)
        return MsgFlow(uid=_cid).forget()

    @staticmethod
    def extract_arg(arg):
        return arg.split()[1:]

    @staticmethod
    def tokenizer(s: str) -> float:
        """
        谨慎的计算器，会预留 5 token
        :param s:
        :return:
        """
        # 统计中文字符数量
        num_chinese = len([c for c in s if ord(c) > 127])
        # 统计非中文字符数量
        num_non_chinese = len([c for c in s if ord(c) <= 127])
        return int(num_chinese * 2 + num_non_chinese * 0.25) + 5

    @staticmethod
    def Humanization(strs):
        return strs.lstrip('？?!！：。')

    @staticmethod
    def WaitFlood(user, group, usercold_time: int = None, groupcold_time: int = None):
        load_csonfig()
        if usercold_time is None:
            usercold_time = _csonfig["usercold_time"]
        if groupcold_time is None:
            groupcold_time = _csonfig["groupcold_time"]
        if DataUtils.getKey(f"flood_user_{user}"):
            # double req in 3 seconds
            return True
        else:
            if _csonfig["usercold_time"] > 1:
                DataUtils.setKey(f"flood_user_{user}", "FAST", exN=usercold_time)
        # User
        if DataUtils.getKey(f"flood_group_{group}"):
            # double req in 3 seconds
            return True
        else:
            if _csonfig["groupcold_time"] > 1:
                DataUtils.setKey(f"flood_group_{group}", "FAST", exN=groupcold_time)
        return False

    @staticmethod
    def get_head_foot(prompt: str, cap: int = 12):
        body = prompt
        head = ""
        if ":" in prompt[:cap]:
            _split = prompt.split(":", 1)
            if len(_split) > 1:
                body = _split[1]
                head = _split[0]
        return head, body

    @staticmethod
    def checkMsg(msg_uid):
        _Group_Msg = MsgsRecordUtils.getKey(msg_uid)
        # print(Group_Msg.get(str(msg_uid)))
        return _Group_Msg

    @staticmethod
    def trackMsg(msg_uid, user_id):
        return MsgsRecordUtils.setKey(msg_uid, str(user_id), exN=86400 * 2)

    @staticmethod
    def removeList(key, command):
        load_csonfig()
        info = []
        for group in Utils.extract_arg(command):
            groupId = "".join(list(filter(str.isdigit, group)))
            if int(groupId) in _csonfig[key]:
                _csonfig[key].remove(str(groupId))
                info.append(f'{key} Removed {groupId}')
                logger.info(f"SETTING:{key} Removed {group}")
        if isinstance(_csonfig[key], list):
            _csonfig[key] = list(set(_csonfig[key]))
        save_csonfig()
        _info = '\n'.join(info)
        return f"删除了\n{_info}"

    @staticmethod
    def addList(key, command):
        load_csonfig()
        info = []
        for group in Utils.extract_arg(command):
            groupId = "".join(list(filter(str.isdigit, group)))
            _csonfig[key].append(str(groupId))
            info.append(f'{key} Added {groupId}')
            logger.info(f"SETTING:{key} Added {group}")
        if isinstance(_csonfig[key], list):
            _csonfig[key] = list(set(_csonfig[key]))
        save_csonfig()
        _info = '\n'.join(info)
        return f"加入了\n{_info}"


# 弃用
class rqParser(object):
    @staticmethod
    def get_response_text(response):
        REPLY = []
        Choice = response.get("choices")
        if Choice:
            for item in Choice:
                _text = item.get("text")
                REPLY.append(_text)
        if not REPLY:
            REPLY = ["Nothing to say:response null~"]
        return REPLY

    @staticmethod
    def get_response_usage(response):
        usage = len("机器资源")
        if response.get("usage"):
            usage = response.get("usage").get("total_tokens")
        return usage


class Usage(object):
    def __init__(self, uid: Union[int, str]):
        self.__uid = str(uid)
        _service = Service_Data.get_key()
        _redis_conf = _service["redis"]
        _redis_config = RedisConfig(**_redis_conf)
        self.__Data = DataWorker(host=_redis_config.host,
                                 port=_redis_config.port,
                                 db=_redis_config.db,
                                 password=_redis_config.password,
                                 prefix="Open_Ai_bot_usage_")

    def __get_usage(self):
        _usage = self.__Data.getKey(f"{self.__uid}_usage")
        if _usage:
            return Usage_Data(**_usage)
        else:
            return None

    def __set_usage(self, now, usage, total_usage):
        _data = Usage_Data(now=now, user=str(self.__uid), usage=usage, total_usage=total_usage)
        self.__Data.setKey(f"{self.__uid}_usage",
                           _data.dict())
        return _data

    def resetTotalUsage(self):
        GET = self.__get_usage()
        GET.total_usage = 0
        self.__Data.setKey(f"{self.__uid}_usage",
                           GET.dict())

    def isOutUsage(self):
        """
        累计
        :return: bool
        """
        # 时间
        load_csonfig()
        key_time = int(time.strftime("%Y%m%d%H", time.localtime()))
        GET = self.__get_usage()
        # 居然没有记录
        if not GET:
            GET = self.__set_usage(now=key_time, usage=0, total_usage=0)
            return {"status": False, "use": GET.dict(), "time": key_time}
        # 重置
        if GET.now != key_time:
            GET.usage = 0
            GET.now = key_time
            self.__Data.setKey(f"{self.__uid}_usage",
                               GET.dict())
        # 按照异常返回的逻辑
        # 小时计量
        if _csonfig["hour_limit"] > 1:
            # 设定了，又超额了
            if GET.usage > _csonfig["hour_limit"]:
                return {"status": True, "use": GET.dict(), "time": key_time}
        # 用户额度计量---特殊额度---还有通用额度
        USER_ = _csonfig["per_user_limit"]
        _LIMIT = UserManager(int(self.__uid)).read("usage")
        if not isinstance(_LIMIT, int):
            _LIMIT = 10000
        if _LIMIT != 1:
            USER_ = _LIMIT
        # 没有设置限制
        if USER_ == 1 and _LIMIT == 1:
            return {"status": False, "use": GET.dict(), "time": key_time}
        # 覆盖完毕
        if GET.total_usage > USER_:
            return {"status": True, "use": GET.dict(), "time": key_time}
        return {"status": False, "use": GET.dict(), "time": key_time}

    def renewUsage(self, usage: int):
        key_time = int(time.strftime("%Y%m%d%H", time.localtime()))
        GET = self.__get_usage()
        if not GET:
            GET = self.__set_usage(now=key_time, usage=0, total_usage=0)
        GET.total_usage = GET.total_usage + usage
        GET.usage = GET.usage + usage
        self.__Data.setKey(f"{self.__uid}_usage",
                           GET.dict())
        # double req in 3 seconds
        return GET
