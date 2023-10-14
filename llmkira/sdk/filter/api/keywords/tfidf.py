# -*- coding: utf-8 -*-

import cjieba

from ..solo import singleton


@singleton
class TfidfKeywords:
    def __init__(self, delete_stopwords=True, topK=20, withWeight=False):
        self.topk = topK
        self.with_wight = withWeight

    def keywords(self, sentence):
        return cjieba.extract(text=sentence, top_k=self.topk, with_weight=self.with_wight)
        # return jieba.analyse.extract_tags(sentence, topK=self.topk, withWeight=self.with_wight)
