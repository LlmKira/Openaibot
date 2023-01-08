# -*- coding: utf-8 -*-
# @Time    : 1/5/23 10:05 AM
# @FileName: Frequency.py
# @Software: PyCharm
# @Github    ：sudoskys
import random
import time

from openai_kira import Chat

from utils.Data import User_Message, Service_Data, RedisConfig, DataWorker

service = Service_Data.get_key()
redis_conf = service["redis"]
redis_config = RedisConfig(**redis_conf)
# 工具数据类型
Tigger = DataWorker(host=redis_config.host,
                    port=redis_config.port,
                    db=redis_config.db,
                    password=redis_config.password,
                    prefix="Open_Ai_bot_tigger_")


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
        _time_matrix = Tigger.getKey(_tid)
        if _time_matrix:
            if not isinstance(_time_matrix, list):
                matrix = []
            matrix = _time_matrix
        else:
            matrix = []
        matrix.append(time.time())
        Tigger.setKey(_tid, matrix, exN=60 * 5)

    def _get_chat_vitality(self):
        _tid = self.__tid()
        _time_matrix = Tigger.getKey(_tid)
        if not isinstance(_time_matrix, list):
            return len([])
        if _time_matrix:
            return len(_time_matrix)
        else:
            return len([])

    def tigger(self, Message: User_Message, config):
        """
        追踪群组消息上下文为 Catch 提供养分
        :param Message:
        :param config:
        :return:
        """
        _text = Message.text
        self._grow_request_vitality()
        self.receiver.record_message(ask=_text, reply="")

    def check(self):
        # 检查频次锁
        if Tigger.getKey(self.group_id):
            return False
        # 抽签
        _lucky = random.randint(1, 100)
        if _lucky < 5:
            Tigger.setKey(self.group_id, "True", exN=60 * 20)
            return True

        # 频次计算机器
        _frequency = self._get_chat_vitality()
        # 一分钟内的次数
        if _frequency > 20:
            Tigger.setKey(self.group_id, "True", exN=60 * 10)
            return True

        # 计算初始
        message_cache = self.receiver.read_memory(plain_text=True, sign=False)
        message_cache: list
        message_cache = [item for item in message_cache if item]
        if not len(message_cache) > 20:
            return False

        _cache = message_cache[:20]
        from openai_kira.utils.Talk import Talk
        _keywords = []
        for items in _cache:
            _keywords.extend(Talk.tfidf_keywords(keywords=items, delete_stopwords=True, topK=5, withWeight=False))
        if len(_keywords) < 5:
            return False
        _get_score = len(list(set(_keywords))) / len(_keywords)
        # 得分越低代表越相似
        if _get_score < 0.5:
            Tigger.setKey(self.group_id, "True", exN=60 * 20)
            return True

        return False
