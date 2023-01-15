# -*- coding: utf-8 -*-
# @Time    : 1/5/23 10:05 AM
# @FileName: Frequency.py
# @Software: PyCharm
# @Github    ：sudoskys
import random
import time

from openai_kira import Chat
from openai_kira.utils.chat import Utils

from utils.Data import User_Message, Service_Data, RedisConfig, DataWorker

service = Service_Data.get_key()
redis_conf = service["redis"]
redis_config = RedisConfig(**redis_conf)
# 工具数据类型
Trigger = DataWorker(host=redis_config.host,
                     port=redis_config.port,
                     db=redis_config.db,
                     password=redis_config.password,
                     prefix="Open_Ai_bot_trigger_")


class CheckSeq(object):
    def __init__(self):
        self._help_keywords = ["怎么",
                               "How",
                               "今天",
                               "吗？",
                               "什么",
                               "知道",
                               "无聊",
                               "啊？",
                               "What",
                               "what",
                               "who",
                               "how",
                               "Who",
                               "Why",
                               "why",
                               "Where",
                               "谁能",
                               "呢",
                               "吗",
                               "How to",
                               "how to",
                               "如何做",
                               "帮我",
                               "帮助我",
                               "请给我",
                               "给出建议",
                               "给建议",
                               "给我",
                               "给我一些",
                               "请教",
                               "介绍",
                               "如何",
                               "帮朋友",
                               "需要什么",
                               "注意什么",
                               "草",
                               "呀",
                               "怎么办"
                               ]

    def help(self, text):
        has = False
        for item in self._help_keywords:
            if item in text:
                has = True
        return has


class Vitality(object):
    def __init__(self, group_id: int):
        self.group_id = str(group_id)
        self.time_interval = 60 * 10
        _oid = f"-{abs(group_id)}"
        self.receiver = Chat.Chatbot(
            api_key="1",
            conversation_id=int(_oid),
            token_limit=1500,
        )

    def __tid(self):
        return self.group_id + str(time.strftime("%Y%m%d%H%M", time.localtime()))

    def _grow_request_vitality(self):
        _tid = self.__tid()
        _time_matrix = Trigger.getKey(_tid)
        if _time_matrix:
            if not isinstance(_time_matrix, list):
                matrix = []
            matrix = _time_matrix
        else:
            matrix = []
        matrix.append(time.time())
        Trigger.setKey(_tid, matrix, exN=60 * 5)

    def _get_chat_vitality(self):
        _tid = self.__tid()
        _time_matrix = Trigger.getKey(_tid)
        if not isinstance(_time_matrix, list):
            return len([])
        if _time_matrix:
            return len(_time_matrix)
        else:
            return len([])

    def trigger(self, Message: User_Message, config):
        """
        追踪群组消息上下文为 Catch 提供养分
        :param Message:
        :param config:
        :return:
        """
        _text = Message.text
        _name = Message.from_user.name
        self._grow_request_vitality()
        if len(_text) < 3:
            return False
        self.receiver.record_message(ask=f"{_name}:{_text}", reply=".:.")

    @staticmethod
    def isHighestSentiment(text, cache):
        now = Utils.sentiment(text).get("score")
        for item in cache:
            _score = Utils.sentiment(item).get("score")
            if _score > now:
                return False
        return True

    def check(self, Message: User_Message):
        _text = Message.text
        _min = random.randint(10, 100)
        if len(_text) < 5:
            return False
        # 检查频次锁，提前返回
        if Trigger.getKey(self.group_id):
            return False

        # 频次计算机器
        _frequency = self._get_chat_vitality()
        # 提前返回
        if _frequency < 5:
            return False

        # 合格检查，上下文阶段
        status = False
        # 抽签
        _lucky = random.randint(1, 100)
        if _lucky > 80:
            status = True

        # 最后的内容检查
        _check = CheckSeq()
        if _check.help(_text):
            status = True

        if status:
            status = False
            _score = Utils.sentiment(_text).get("score")
            if isinstance(_score, float):
                if _score > 1.8 or _score < -2:
                    status = True

        # 检查
        if status:
            Trigger.setKey(self.group_id, "True", exN=60 * _min)
        return status


"""
                # 计算初始
                message_cache = self.receiver.read_memory(plain_text=True, sign=True)
                message_cache: list
                message_cache = [item for item in message_cache if item]
                if len(message_cache) < 20:
                    return False
                _cache = message_cache[:20]
                if self.isHighestSentiment(text=_text, cache=_cache):
"""
