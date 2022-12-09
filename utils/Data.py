# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:59 PM
# @FileName: DataWorker.py
# @Software: PyCharm
# @Github    ：sudoskys
import ast
import json
import pathlib
# 缓冲
from collections import OrderedDict
from datetime import datetime, timedelta

from loguru import logger
from pydantic import BaseModel

redis_installed = True

try:
    from redis import Redis, ConnectionPool
except Exception:
    redis_installed = False


class Usage_Data(BaseModel):
    user: str
    now: int
    usage: int
    total_usage: int


class Api_keys(object):
    """
    管理 Api
    """

    @staticmethod
    def get_key():
        now_table = DefaultData.defaultKeys()
        if pathlib.Path("./Config/api_keys.json").exists():
            with open("./Config/api_keys.json", encoding="utf-8") as f:
                _config = json.load(f)
                DictUpdate.dict_update(now_table, _config)
                _config = now_table
            return _config
        else:
            return now_table

    @staticmethod
    def save_key(_config):
        with open("./Config/api_keys.json", "w+", encoding="utf8") as f:
            json.dump(_config, f, indent=4, ensure_ascii=False)

    @staticmethod
    def add_key(key: str):
        _config = Api_keys.get_key()
        _config['OPENAI_API_KEY'].append(key)
        _config["OPENAI_API_KEY"] = list(set(_config["OPENAI_API_KEY"]))
        with open("./Config/api_keys.json", "w", encoding="utf8") as f:
            json.dump(_config, f, indent=4, ensure_ascii=False)
        return key

    @staticmethod
    def pop_key(key: str):
        _config = Api_keys.get_key()
        if key not in _config['OPENAI_API_KEY']:
            return
        _config['OPENAI_API_KEY'].remove(key)
        _config["OPENAI_API_KEY"] = list(set(_config["OPENAI_API_KEY"]))
        with open("./Config/api_keys.json", "w", encoding="utf8") as f:
            json.dump(_config, f, indent=4, ensure_ascii=False)
        return key

    @staticmethod
    def pop_api_key(resp, auth):
        _path = str(pathlib.Path.cwd()) + "/Config/app.toml"
        # 读取
        _config = Api_keys.get_key()
        _config: dict
        # 弹出
        ERROR = resp.get("error")
        if ERROR:
            if ERROR.get('type') == "insufficient_quota":
                if isinstance(_config["OPENAI_API_KEY"], list) and auth in _config["OPENAI_API_KEY"]:
                    _config["OPENAI_API_KEY"].remove(auth)
                    logger.error(
                        f"弹出过期ApiKey:  --type insufficient_quota --auth {DefaultData.mask_middle(auth, 4)}")
                    # 存储
            if ERROR.get('code') == "invalid_api_key":
                if isinstance(_config["OPENAI_API_KEY"], list) and auth in _config["OPENAI_API_KEY"]:
                    _config["OPENAI_API_KEY"].remove(auth)
                    logger.error(f"弹出非法ApiKey: --type invalid_api_key --auth {DefaultData.mask_middle(auth, 4)}")
        Api_keys.save_key(_config)


class DefaultData(object):
    """
    数据提供类
    """

    @staticmethod
    def composing_uid(user_id, chat_id):
        return f"{user_id}:{chat_id}"

    @staticmethod
    def mask_middle(s: str, n: int) -> str:
        # 计算需要替换的字符数
        num_chars = len(s) - 2 * n
        # 构造替换字符串
        mask = "*" * num_chars
        # 将替换字符串插入到原字符串的指定位置
        return s[:n] + mask + s[n + num_chars:]

    @staticmethod
    def defaultConfig():
        return {
            "statu": True,
            "input_limit": 250,
            "token_limit": 300,
            "hour_limit": 15000,
            "per_user_limit": 1,
            "usercold_time": 10,
            "groupcold_time": 1,
            "User": {},
            "Group": {},
            "whiteUserSwitch": True,
            "whiteGroupSwitch": True,
            "Model": {
            }
        }

    @staticmethod
    def defaultKeys():
        return {"OPENAI_API_KEY": []}

    @staticmethod
    def defaultAnalysis():
        return {"frequency": 0, "usage": {}}

    def setAnalysis(self,
                    **kwargs
                    ):
        """
        frequency,
        usage,
        :param self:
        :param kwargs:
        :return:
        """
        _Analysis = self.defaultAnalysis()
        if pathlib.Path("./analysis.json").exists():
            with open("./analysis.json", encoding="utf-8") as f:
                DictUpdate.dict_update(_Analysis, json.load(f))
        DictUpdate.dict_update(_Analysis, kwargs)
        with open("./analysis.json", "w", encoding="utf8") as f:
            json.dump(_Analysis, f, indent=4, ensure_ascii=False)

    @staticmethod
    def defaultUser():
        return {"white": False,
                "block": False,
                "usage": 1
                }

    # 单独配额，如果这里不是 1,优先按这这分配额度
    @staticmethod
    def defaultGroup():
        return {
            "white": False,
            "block": False
        }


class ExpiringDict(OrderedDict):
    """
    过期字典
    """

    def __init__(self, *args, **kwargs):
        self.expirations = {}
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.expirations[key] = datetime.now() + timedelta(seconds=value)
        super().__setitem__(key, value)

    def set_expiration(self, key, expiration_time):
        self.expirations[key] = expiration_time

    def cleanup(self):
        for key, expiration_time in self.expirations.items():
            if datetime.now() > expiration_time:
                super().pop(key)


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


class DictUpdate(object):
    """
    字典深度更新
    """

    @staticmethod
    def dict_update(raw, new):
        DictUpdate.dict_update_iter(raw, new)
        DictUpdate.dict_add(raw, new)

    @staticmethod
    def dict_update_iter(raw, new):
        for key in raw:
            if key not in new.keys():
                continue
            if isinstance(raw[key], dict) and isinstance(new[key], dict):
                DictUpdate.dict_update(raw[key], new[key])
            else:
                raw[key] = new[key]

    @staticmethod
    def dict_add(raw, new):
        update_dict = {}
        for key in new:
            if key not in raw.keys():
                update_dict[key] = new[key]
        raw.update(update_dict)


def getPuffix(self, fix):
    connection = Redis(connection_pool=self.redis)
    listGet = connection.scan_iter(f"{fix}*")
    connection.close()
    return listGet


def limit_dict_size(dicts, max_size):
    if len(dicts) > max_size:
        # 如果字典中的键数量超过了最大值，则删除一些旧的键
        dicts = dicts[max_size:]
    return dicts
