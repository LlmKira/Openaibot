# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: base.py
# @Software: PyCharm
# @Github    ：sudoskys
import rtoml


class TOMLConfig(object):
    def __init__(self, config=None):
        self.config = config

    def dict_to_obj(self, dict_obj):
        if not isinstance(dict_obj, dict):
            return dict_obj
        obj = type('', (), {})()
        for key, value in dict_obj.items():
            setattr(obj, key, self.dict_to_obj(value))
        return obj

    def get(self):
        return self.config

    def parse_file(self, path, to_obj: bool = True):
        data = rtoml.load(open(path, 'r'))
        self.config = data
        if to_obj:
            self.config = self.dict_to_obj(data)
        return self.config

    def parse_dict(self, data):
        self.config = self.dict_to_obj(data)
        return self.config

    @staticmethod
    def save_dict(path, data):
        return rtoml.dump(data, open(path, 'w'))
