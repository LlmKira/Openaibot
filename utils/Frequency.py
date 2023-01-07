# -*- coding: utf-8 -*-
# @Time    : 1/5/23 10:05 AM
# @FileName: Frequency.py
# @Software: PyCharm
# @Github    ：sudoskys
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


# 热力扳机

class Vitality(object):
    def __init__(self, group_id):

        self.group_id = str(group_id)
        self.message_cache = Tigger.getList(self.group_id)
        self.time_interval = 60 * 10
        # 使用 deque 存储请求时间戳
        self.request_timestamps = Tigger.getList(f"group_{self.group_id}")

    def get_request_frequency(self):
        while self.request_timestamps and self.request_timestamps[0] < time.time() - self.time_interval:
            self.request_timestamps.pop(0)
        request_frequency = len(self.request_timestamps)
        return request_frequency

    def tigger(self, Message: User_Message, config):
        """
        追踪群组消息上下文为 Catch 提供养分
        :param Message:
        :param config:
        :return:
        """
        _text = Message.text
        self.request_timestamps.append(time.time())
        Tigger.addToList(f"group_{self.group_id}", listData=list(self.request_timestamps))
        self.message_cache.append(_text)
        Tigger.addToList(f"{self.group_id}", listData=[_text])

        _oid = f"-{abs(Message.from_chat.id)}"
        receiver = Chat.Chatbot(
            api_key="1",
            conversation_id=int(_oid),
            token_limit=1500,
        )
        receiver.record_message(ask=_text, reply="")

    def check(self):
        tagger = False
        # 检查频次锁
        if Tigger.getKey(self.group_id):
            return False
        print(self.message_cache)
        if not len(self.message_cache) > 10:
            return False
        # 上下文
        _cache = self.message_cache[:10]
        # 计算
        from openai_kira.utils.Talk import Talk
        _CHA = []
        _max = 0
        _index = 0
        for item in range(len(_cache)):
            if len(_cache[item]) > _max:
                _max = len(_cache[item])
                _index = item
        _theme = Talk.tfidf_keywords(keywords=_cache[_index], delete_stopwords=True, topK=5, withWeight=False)
        _score = []
        _cache.remove(_cache[_index])
        for items in _cache:
            _now = Talk.tfidf_keywords(keywords=items, delete_stopwords=True, topK=5, withWeight=False)
            _know = [item for item in _now if item in _theme]
            _score.append(len(_know))
        _get_score = sum(_score) / len(_score) * 5
        if _get_score > 0.5:
            tagger = True
        # 频次计算机器
        _fr = self.get_request_frequency()
        print(_fr)
        if 5 > _fr or _fr > 100:
            tagger = True
        if tagger:
            # 注册频次锁
            Tigger.setKey(self.group_id, True, exN=60 * 10)
        return tagger
