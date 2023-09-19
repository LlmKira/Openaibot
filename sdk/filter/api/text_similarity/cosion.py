# -*- coding: utf-8 -*-
from typing import Tuple, Union

import cjieba
from sklearn.metrics.pairwise import cosine_similarity

from ..solo import singleton
from ...api.keywords import STOPWORDS


@singleton
class CosionSimilarity(object):
    """
    根据余弦函数计算相似性
    one-hot编码
    """

    def __init__(self):
        self.stopwords = self.load_stopwords(STOPWORDS)

    @staticmethod
    def load_stopwords(stopwords_path):
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return set([line.strip() for line in f])

    def cut_words(self, text):
        return [word for word in cjieba.cut(text) if word not in self.stopwords]

    def str_to_vector(self, text1: str, text2: str) -> Tuple[list, list]:
        text1_words = set(self.cut_words(text1))
        text2_words = set(self.cut_words(text2))
        all_words = list(text1_words | text2_words)
        text1_vector = [1 if word in text1_words else 0 for word in all_words]
        text2_vector = [1 if word in text2_words else 0 for word in all_words]
        return text1_vector, text2_vector

    def similarity(self, text1: Union[str, list], text2: Union[str, list]):
        text1_words = set(self.cut_words(text1))
        text2_words = set(self.cut_words(text2))
        all_words = list(text1_words | text2_words)
        text1_vector = [1 if word in text1_words else 0 for word in all_words]
        text2_vector = [1 if word in text2_words else 0 for word in all_words]
        if not text1_vector or not text2_vector:
            return 0
        return cosine_similarity([text1_vector], [text2_vector])[0][0]

    @staticmethod
    def vector_similarity(text1_vector: list, text2_vector: list):
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity([text1_vector], [text2_vector])[0][0]


if __name__ == '__main__':
    text1 = "小明，你妈妈喊你回家吃饭啦"
    text2 = "回家吃饭啦，小明"
    similarity = CosionSimilarity()
    print(similarity.similarity(text1, text2))
