# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:59 PM
# @FileName: DataWorker.py
# @Software: PyCharm
# @Github    ：sudoskys
import ast
import json
import pathlib
import random
import re
import time
# 缓冲
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List, Optional, Union
from loguru import logger
from pydantic import BaseModel

from utils.Lock import pLock

redis_installed = True

try:
    from redis import Redis, ConnectionPool
except Exception:
    redis_installed = False


class from_chat(BaseModel):
    id: int
    name: str = "作业群"


class from_user(BaseModel):
    id: int
    name = "猫娘"
    admin: bool = False


class User_Message(BaseModel):
    id: int = 0
    from_user: from_user
    from_chat: from_chat
    text: str
    prompt: list
    date: int = int(time.time() * 1000)
    reply_user_id: Optional[int]
    reply_chat_id: Optional[int]


def create_message(
        user_id: int,
        user_name,
        group_id: int,
        group_name,
        text: str,
        state: int,
        reply_chat_id: Optional[int] = None,
        reply_user_id: Optional[int] = None,
        prompt: Union[str, list] = None,
        date=time.time()):
    state = abs(state)
    if state != 0:
        group_id = int(f"{group_id}{state}")
        user_id = int(f"{user_id}{state}")
    if prompt is None:
        prompt = [text]
    if isinstance(prompt, str):
        prompt = [prompt]
    message = {
        "text": text,
        "prompt": prompt,
        "from_user": from_user(id=user_id, name=user_name),
        "from_chat": from_chat(id=group_id, name=group_name),
        "reply_user_id": reply_user_id,
        "reply_chat_id": reply_chat_id,
        "date": date
    }
    return User_Message(**message)


class PublicReturn(BaseModel):
    status: bool = False
    msg: str = ""
    data: Union[str, dict, bytes, list] = None
    voice: Optional[bytes] = None
    reply: Optional[str] = None
    trace: str = ""


class Usage_Data(BaseModel):
    user: str
    now: int
    usage: int
    total_usage: int


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = None


class ProxyConfig(BaseModel):
    status: bool
    url: str


class DefaultData(object):
    """
    数据提供类
    """

    @staticmethod
    def getWaitAnswer():
        _wait_child = ["6 ", "? ", "别 ", "呃呃 ", "我不好说，", "害怕，",
                       "？？？？", "....", "666 ", "勿Cue，", "忙着呢 ", "等我打个电话...",
                       "等我查查字典...", "亲，", "别急", "", "", "", "", "",
                       "啊哈哈哈。", "尴尬。", "Oppose..", "你知道的。", "停停...", "手机信号不好，", "手机信号不好，",
                       '到底说啥呐？', '我不懂', '笑死，', '不明白了，', "哇！", "牛的"
                       ]
        _wait = ["稍等，土豆炸了", "服务器真的炸了",
                 "有点小问题", "发生了啥",
                 "Crash了", "ServerBoom",
                 "服务器进水了", "服务器飞走了",
                 "服务器稍微有点问题...", "服务器被我吃掉了...",
                 "....", "那个", "", "", "", "？"
                 ]
        _compose_list1 = [random.choice(_wait_child), random.choice(_wait)]
        _compose_list2 = [random.choice(_wait_child), random.choice(_wait_child), " ", random.choice(_wait)]
        _compose_list = random.choice([_compose_list2, _compose_list1])
        _info = f"\n{' '.join(_compose_list)}"
        return _info

    @staticmethod
    def getRefuseAnswer():
        _censor_child = ["你说啥呢？", "我不说,", "不懂年轻人,", "6 ", "? ", "别 ", "呃呃 ", "我不好说，", "害怕，",
                         "我想说的是", "我想强调的是...", "没意思", "无聊...", "你以为我会回你？", "",
                         "我想指出的是，", "我想重申的是，", "[叛逆]", "[傲娇]", "？？？？", "....", "666 ",
                         "什么事儿呀，", "是啊，是啊。", "你猜啊，", "就是啊，", "勿Cue，", "忙着呢 ", "等我打个电话...",
                         "等我查查字典...", "亲，", "别急", "", "", "", "", "", "[不屑]", "[微笑]", "[微笑]", "[微笑]",
                         "哎呀，真的吗？", "啊哈哈哈。", "你知道的。", "停停...", "手机信号不好，", "手机信号不好，",
                         '到底说啥呐？', '我不懂', '笑死，', '不明白了，', '你能解释一下吗，', '太复杂了，都不懂,', "哇！"
                         ]
        _censor = ["有点离谱，不想回答。", "别为难我。",
                   "累了，歇会儿。", "能不能换个话题？",
                   "我不想说话。", "没什么好说的。", "你觉得我会回复你？", "别急。", "别急！", "别急..",
                   "这里不适合说这个。", "我没有什么可说的。",
                   "我不喜欢说话。", "反正我拒绝回答。",
                   "我不喜欢被问这个。", "我觉得这个问题并不重要。",
                   "我不想谈论这个话题。", "我不想对这个问题发表意见！",
                   '你觉得该换个话题了吗？', '我们能不能换个话题聊聊？',
                   '让我们换个话题聊聊？', '谈点别的话题吧！',
                   '要不要换个话题？', '说这个多没意思。',
                   '换个话题呗...', '你想换个话题吗？', '我们换个话题谈啊！',
                   '你觉得该换个话题了吗？', '别谈这个话题了！', '我们能不能换个话题聊聊？',
                   '换个新鲜的话题吧！', '谈点别的话题吧！',
                   '要不要换个话题？', '换个话题来聊聊吧！', '换个新题目聊聊吧！',
                   '别管我了。', '你走开。', '我不理你了。', '算了吧。', '算了吧。',
                   '算了吧。', '算了吧。', '算了吧。', '再见了。',
                   '你听不懂我了。', '何不换个话题？', '我们换个话题谈啊！',
                   '你觉得该换个话题了吗？', '别谈这个话题了！',
                   '我们能不能换个话题聊聊？', '换个新鲜的话题吧！',
                   '谈点别的话题吧！', '要不要换个话题？', '这一切都结束了。', '我不在乎你。', '再也不跟你说话了。',
                   '别再烦我了。', '别搭理我。', '闭嘴', '别找我了',
                   '这个话题太旧了，来谈谈其他的吧！', '低情商。',
                   '换个话题来聊聊吧！', '换个新题目聊聊吧！']
        _compose_list1 = [random.choice(_censor_child), random.choice(_censor)]
        _compose_list2 = [random.choice(_censor_child), random.choice(_censor_child), random.choice(_censor)]
        _compose_list = random.choice([_compose_list2, _compose_list1])
        _info = f"\n{' '.join(_compose_list)}"
        return _info

    @staticmethod
    def composing_uid(user_id, chat_id):
        # return f"{user_id}:{chat_id}"
        return f"{user_id}"

    @staticmethod
    def name_split(sentence: str, limit: int, safe_replace: bool = True) -> str:
        if safe_replace:
            sentence = sentence.replace(":", "：")
        if len(sentence) < limit:
            return sentence
        str_list = re.split("[, !]#《》:：【】", sentence)
        str_list.sort(key=len, reverse=True)
        for item in str_list:
            if len(item) < limit:
                return item
        return sentence[:limit]

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
            "input_limit": 800,
            "token_limit": 1000,
            "hour_limit": 20000,
            "per_user_limit": 1,
            "usercold_time": 10,
            "groupcold_time": 1,
            "User": {},
            "Group": {},
            "whiteUserSwitch": True,
            "whiteGroupSwitch": True,
            "Model": {
            },
            "auto_adjust": False,
            "allow_change_style": True,
            "allow_change_head": True
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
                try:
                    _data = json.load(f)
                except:
                    _data = {}
                DictUpdate.dict_update(_Analysis, _data)
        DictUpdate.dict_update(_Analysis, kwargs)
        with open("./analysis.json", "w+", encoding="utf8") as f:
            json.dump(_Analysis, f, indent=4, ensure_ascii=False)

    @staticmethod
    def defaultUser():
        return {
            "white": False,
            "block": False,
            "usage": 1,
            "voice": False
        }

    # 单独配额，如果这里不是 1,优先按这这分配额度
    @staticmethod
    def defaultGroup():
        return {
            "cross": True,
            "trace": False,
            "silent": False,
            "white": False,
            "block": False,
            "trigger": False
        }

    @staticmethod
    def defaultService():
        return {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None
            },
            "proxy": {
                "status": False,
                "url": "http://127.0.0.1:7890"
            },
            "plugin": {
            },
            "backend": {
                "type": "chatgpt",
                "openai": {
                    "model": "text-davinci-003",
                    "token_limit": 4000
                },
                "chatgpt": {
                    "model": "gpt-3.5-turbo",
                    "token_limit": 4000
                },
            },
            "media": {
                "blip": {
                    "status": False,
                    "api": "http://127.0.0.1:10885/upload/"
                },
                "sticker": {
                    "status": True,
                    "penalty": 0.95
                }
            },
            "moderation_type": [
                "self-harm",
                # "hate",
                "sexual",
                "hate/threatening",
                "sexual/minors",
                "violence",
                "violence/graphic"
            ],
            "tts": {
                "status": False,
                "type": "vits",
                "vits": {
                    "api": "http://127.0.0.1:9557/tts/generate",
                    "limit": 70,
                    "model_name": "some.pth",
                    "speaker_id": 0
                },
                "azure": {
                    "key": [""],
                    "limit": 70,
                    "speaker": {
                        "ZH": "zh-CN-XiaoxiaoNeural"
                    },
                    "location": "japanwest"
                }
            }
        }


class Service_Data(object):
    """
    管理 Api
    """

    @staticmethod
    def get_key(filePath: str = "./Config/service.json"):
        now_table = DefaultData.defaultService()
        if pathlib.Path(filePath).exists():
            with open(filePath, encoding="utf-8") as f:
                _config = json.load(f)
                DictUpdate.dict_update(now_table, _config)
                _config = now_table
            return _config
        else:
            return now_table

    @staticmethod
    def save_key(_config, filePath: str = "./Config/service.json"):
        with open(filePath, "w+", encoding="utf8") as f:
            json.dump(_config, f, indent=4, ensure_ascii=False)


class Openai_Api_Key(object):
    """
    管理 Api
    """

    def __init__(self, filePath: str = "./Config/api_keys.json"):
        self.__filePath = filePath

    def _save_key(self, config: dict) -> None:
        pLock.getInstance().acquire()
        with open(self.__filePath, "w+", encoding="utf8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        pLock.getInstance().release()

    def __get_config(self):
        now_table = DefaultData.defaultKeys()
        if pathlib.Path(self.__filePath).exists():
            pLock.getInstance().acquire()
            with open(self.__filePath, encoding="utf-8") as f:
                _config = json.load(f)
                DictUpdate.dict_update(now_table, _config)
                _config = now_table
            pLock.getInstance().release()
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

    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix='Openaibot_'):
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
