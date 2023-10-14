# -*- coding: utf-8 -*-
# @Time    : 2023/9/4 下午10:49
# @Author  : sudoskys
# @File    : reduce.py
# @Software: PyCharm
from typing import List, Any

import cjieba
import numpy as np
from sklearn.cluster import Birch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer


class Cluster(object):

    def __init__(self):
        self.weight = None
        self.cluster = None
        self.title_dict: dict = {}

    def init(self, sentence_list):
        corpus = []
        self.title_dict = {}
        index = 0
        for line in sentence_list:
            title = line.strip()
            self.title_dict[index] = title
            output = ' '.join(['%s' % x for x in list(cjieba.cut(title, cut_all=False))]).encode('utf-8')  # 空格拼接
            index += 1
            corpus.append(output.strip())
        _vectorizer = CountVectorizer()
        transformer = TfidfTransformer()
        tfidf = transformer.fit_transform(_vectorizer.fit_transform(corpus))
        word = _vectorizer.get_feature_names_out()
        self.weight = tfidf.toarray()

    def birch_cluster(self, sentence_list: List[str], threshold: int = 0.6) -> None:
        self.init(sentence_list=sentence_list)
        self.cluster = Birch(threshold=threshold, n_clusters=None)
        self.cluster.fit_predict(self.weight)

    def build(self) -> List[Any]:
        # self.cluster.labels_  对应 类别 {index: 类别} 类别值int值 相同值代表同一类
        # cluster_dict key为Birch聚类后的每个类，value为 title对应的index
        cluster_dict = {}
        for index, value in enumerate(self.cluster.labels_):
            if value not in cluster_dict:
                cluster_dict[value] = [index]
            else:
                cluster_dict[value].append(index)
        # print("-----before cluster Birch count title:", len(self.title_dict))
        # result_dict key为Birch聚类后距离中心点最近的title，value为sum_similar求和
        result_dict = {}
        for _index in cluster_dict.values():
            latest_index = _index[0]
            similar_num = len(_index)
            if len(_index) >= 2:
                min_s = np.sqrt(np.sum(np.square(
                    self.weight[_index[0]] - self.cluster.subcluster_centers_[self.cluster.labels_[_index[0]]])))
                for index in _index:
                    s = np.sqrt(np.sum(
                        np.square(self.weight[index] - self.cluster.subcluster_centers_[self.cluster.labels_[index]])))
                    if s < min_s:
                        min_s = s
                        latest_index = index
            title = self.title_dict[latest_index]
            result_dict[title] = similar_num
        return list(result_dict.keys())
