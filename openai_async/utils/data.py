# -*- coding: utf-8 -*-
# @Time    : 12/6/22 6:55 PM
# @FileName: data.py
# @Software: PyCharm
# @Github    ：sudoskys
import ast
import json

# 这里是数据基本类

redis_installed = True

try:
    from redis import Redis, ConnectionPool
except Exception:
    redis_installed = False


class MsgFlow(object):
    """
    数据存储桶，用于上下文分析时候提取桶的内容
    """

    def __init__(self, uid):
        """
        消息流存储器
        :param uid: 独立 id ，是一个消息桶
        """
        self.uid = str(uid)
        self.MsgFlowData = DataWorker(prefix="Open_Ai_memory_")
        self.memory: int = 50

    @staticmethod
    def composing_uid(user_id, chat_id):
        return f"{user_id}:{chat_id}"

    def _get_uid(self, uid):
        return self.MsgFlowData.getKey(uid)

    def _set_uid(self, uid, message_streams):
        return self.MsgFlowData.setKey(uid, message_streams)

    def save(self, prompt, role: str = "Human") -> None:
        import time
        time_s = int(time.time() * 1000)
        content = {"prompt": prompt, "role": str(role), "time": time_s}
        _message_streams = self._get_uid(self.uid)
        if "msg" in _message_streams:
            _message_streams["msg"] = sorted(_message_streams["msg"], key=lambda x: x['time'])
            # 记忆容量重整
            if len(_message_streams["msg"]) > self.memory:
                for i in range(len(_message_streams["msg"]) - self.memory + 1):
                    # 多弹出一个用于腾出容量，不能在前面弹出，会造成无法记忆的情况！
                    _message_streams["msg"].pop(0)
            _message_streams["msg"].append(content)
        else:
            _message_streams["msg"] = [content]
        self._set_uid(self.uid, _message_streams)

    def read(self) -> dict:
        message_streams = self._get_uid(self.uid)
        if "msg" in message_streams:
            _msg = message_streams["msg"]
            return _msg
        else:
            return {}

    def forget(self):
        _message_streams = self._get_uid(self.uid)
        if "msg" in _message_streams:
            _message_streams["msg"] = []
            self._set_uid(self.uid, _message_streams)
        return True

    def visit(self, visit_uid, role: str = "Someone", deep: int = 5):
        """
        复制对方对话 4 条进入我的桶
        后续可能会启用名称的
        :param role: 预留
        :param deep: 复制深度
        :param visit_uid 拜访用户桶，来完成跨桶交互
        :return:
        """
        # 混流器
        _visit_streams = self._get_uid(visit_uid)
        if "msg" not in _visit_streams:
            return False
        _msg = _visit_streams["msg"]
        if not (_msg >= deep):
            return False
        _sorted = sorted(_msg, key=lambda x: x['time'], reverse=True)
        for ir in range(deep):
            i = _sorted[ir]
            self.save(prompt=i['prompt'], role=i['role'])
        return True


class DataWorker(object):
    """
    Redis 数据基类
    """

    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix='Telecha_'):
        self.redis = ConnectionPool(host=host, port=port, db=db, password=password)
        # self.con = Redis(connection_pool=self.redis) -> use this when necessary
        #
        # {chat_id: {user_id: {'state': None, 'data': {}}, ...}, ...}
        self.prefix = prefix
        if not redis_installed:
            raise Exception("Redis is not installed. Install it via 'pip install redis'")

    def setKey(self, key, obj, exN=None):
        connection = Redis(connection_pool=self.redis)
        connection.set(self.prefix + str(key), json.dumps(obj), ex=exN)
        connection.close()
        return True

    def deleteKey(self, key):
        connection = Redis(connection_pool=self.redis)
        connection.delete(self.prefix + str(key))
        connection.close()
        return True

    def getKey(self, key):
        connection = Redis(connection_pool=self.redis)
        result = connection.get(self.prefix + str(key))
        connection.close()
        if result:
            return json.loads(result)
        else:
            return {}

    def addToList(self, key, listData: list):
        data = self.getKey(key)
        if isinstance(data, str):
            listGet = ast.literal_eval(data)
        else:
            listGet = []
        listGet = listGet + listData
        listGet = list(set(listGet))
        if self.setKey(key, str(listGet)):
            return True

    def getList(self, key):
        listGet = ast.literal_eval(self.getKey(key))
        if not listGet:
            listGet = []
        return listGet
