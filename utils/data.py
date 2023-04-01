# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:59 PM
# @FileName: DataWorker.py
# @Software: PyCharm
# @Github    ：sudoskys
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional, Union
from pydantic import BaseModel


class DictUpdate:
    """
    用于深度合并两个字典
    """

    @staticmethod
    def deep_merge_dicts(raw_dict: dict, new_dict: dict):
        """
        输入两个字典，将 new_dict 深度合并到 raw_dict 中，raw_dict 会被修改

        Args:
            raw_dict (dict): 被更新的字典
            new_dict (dict): 更新来源字典
        """
        for key, value in new_dict.items():
            if isinstance(value, dict) and key in raw_dict:
                DictUpdate.deep_merge_dicts(raw_dict[key], value)
            else:
                raw_dict[key] = value

        for key in set(new_dict.keys()) - set(raw_dict.keys()):
            raw_dict[key] = new_dict[key]
        return raw_dict


class PublicReturn(BaseModel):
    status: bool = False
    msg: str = ""
    data: Union[str, dict, bytes, list] = None
    voice: Optional[bytes] = None
    reply: Optional[str] = None
    trace: str = ""


class FrequencyCounter:
    def __init__(self):
        self.counter = {}

    def count(self, key):
        if key in self.counter:
            self.counter[key] += 1
        else:
            self.counter[key] = 1

    def get_count(self, key):
        return self.counter.get(key, 0)

    def reset(self):
        self.counter.clear()

    def sync_to_event(self, event, prefix=""):
        for key, value in self.counter.items():
            event.add(prefix + key, value)


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


def limit_dict_size(dicts, max_size):
    if len(dicts) > max_size:
        # 如果字典中的键数量超过了最大值，则删除一些旧的键
        dicts = dicts[max_size:]
    return dicts


def extract_arg(arg):
    return arg.split()[1:]
