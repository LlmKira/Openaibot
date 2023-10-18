# -*- coding: utf-8 -*-
# @Time    : 2023/9/4 下午11:24
# @Author  : sudoskys
# @File    : sublimate.py
# @Software: PyCharm
import re
from typing import List

import numpy as np
from pydantic import BaseModel

from .evaluate import Cut, Extraction, Sim

# 六边形评测，按照排名分配初始分数。
# 采用切分分裂条目，过滤无意义语句。
# 采用关键词筛选清洗 ，挑选。
# 相似度排序，装箱。
BREAK_SHORT = [
    "訂閱", "订阅", "播放量", "点赞",
    "相关视频", "重试", "举报", "内容合作", "ICP备", "公网安备", "哔哩哔哩bilibili_",
    "自动连播", "抖音短视频", "短视频", "更多精彩", "只看楼主", "上一篇", "#热议#",
    "关注问题", "🔞", "下载APP", "违法有害信息"
]


class Order(BaseModel):
    text: str
    x_order: int = -1
    y_score: int = -1
    z_sim: int = -1


class Sublimate(object):

    def __init__(self, sentences: List[str]):
        self.origin = sentences
        self.x_factor = 9  # 初始顺序
        self.y_factor = 3  # 主题得分
        self.z_factor = 1  # 相似度检查
        self.valuate: List[Order] = []
        if not self.origin:
            raise ValueError("Bad Arg For Sublimate")

    @staticmethod
    def _count_in(key_list: List[str], target: str):
        _count = 0
        for item in key_list:
            if item in target:
                _count = _count + 1
        return _count

    @staticmethod
    def real_len(string):
        _r = re.findall(r"[^Wd]+", string)
        return len("".join(_r))

    def wipe_sentence(self, min_limit: int, must_contain: List[str] = None):
        _wipe = self.valuate.copy()
        _new_copy = []
        for item_obj in _wipe:
            if self.real_len(item_obj.text) < min_limit:
                continue
            if self._count_in(BREAK_SHORT, item_obj.text) != 0:
                continue
            if must_contain:
                if self._count_in(must_contain, item_obj.text) != len(must_contain):
                    continue
            _new_copy.append(item_obj)
        #
        self.valuate: List[Order] = _new_copy

    def valuation(self, match_sentence: str, match_keywords: List[str] = None, min_limit: int = 13):
        # 分割并赋予位置
        self.valuate: List[Order] = []
        for index, item in enumerate(self.origin):
            _child = [item]
            if index > 3 and len(item) > 20:
                _child = Cut().cut_sentence(item)
            __score = ((1 - (index / len(self.origin))) * 100) * self.x_factor  # 评估计算 order,乘影响因子
            for child_item in _child:
                self.valuate.append(Order(text=child_item, x_order=__score))

        # 清洗数据
        self.wipe_sentence(min_limit=min_limit, must_contain=match_keywords)
        if not self.valuate:
            return []

        # 提取句子成分
        _keywords = Extraction.tfidf_keywords(match_sentence)  # 高开销注意
        # 对其筛选评分
        __total = len(_keywords)
        for order_obj in self.valuate:
            # 为每个条目赋予主题评分
            __score = 0
            for key in _keywords:
                if key in order_obj.text:
                    __score = __score + 1
            # 计算当前条目分数
            _y_score = ((__score / __total + 1) * 100) * self.y_factor
            order_obj.y_score = _y_score

        # 相似度计算方法
        for order_obj in self.valuate:
            # 高开销注意
            _z_sim = ((Sim.cosion_similarity(pre=match_sentence, aft=order_obj.text)) * 100) * self.z_factor
            order_obj.z_sim = _z_sim

        # 计算
        # 初始化点
        origin = np.array((0, 0, 0))
        _result = {}
        for item_obj in self.valuate:
            _target = np.array((item_obj.x_order, item_obj.y_score, item_obj.z_sim))
            _result[item_obj.text] = float(np.linalg.norm(origin - _target))
        return sorted(_result.items(), reverse=True, key=lambda x: x[1])
