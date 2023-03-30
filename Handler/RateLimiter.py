# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午5:23
# @Author  : sudoskys
# @File    : RateLimiter.py
# @Software: PyCharm
from typing import Union
from loguru import logger
from Handler.Manager import UserManager
from utils.Data import DefaultData, ServiceData, RedisConfig, UsageData

import time


class RateLimiter:
    def __init__(self, max_requests, interval):
        self.max_requests = max_requests
        self.interval = interval
        self.requests = []

    def allow_request(self):
        now = int(time.time())
        cutoff = now - self.interval

        # Remove any requests that fall outside the interval window
        self.requests = [r for r in self.requests if r > cutoff]

        # Check if the number of remaining requests is less than the allowed maximum
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        else:
            return False


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


class Usage(object):
    def __init__(self, uid: Union[int, str]):
        self.__uid = str(uid)
        _service = ServiceData.get_key()
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
            return UsageData(**_usage)
        else:
            return None

    def __set_usage(self, now, usage, total_usage):
        _data = UsageData(now=now, user=str(self.__uid), usage=usage, total_usage=total_usage)
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
