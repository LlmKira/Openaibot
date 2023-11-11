# -*- coding: utf-8 -*-


import cjieba

from ..solo import singleton
from ..summarization import STOPWORDS


def load_stopwords(stopwords_path):
    """
    加载停用词词典
    :param stopwords_path:
    :return:
    """
    with open(stopwords_path, encoding='utf-8') as f:
        return [line.strip() for line in f]


def split_doc(doc):
    separators = ['。', '!', '！', '？', '?']
    for sep in separators:
        doc = doc.replace(sep, sep + '##')
    sentences = doc.split('##')
    return sentences[:-1]


def calculate_sentence_score(sentence, stopwords):
    # jieba_ret = jieba.analyse.extract_tags(sentence, topK=100, withWeight=True)  # , allowPOS=('ns', 'n', 'vn', 'v'))
    jieba_ret = cjieba.extract(sentence, top_k=100, with_weight=True)
    sentence_score = 0
    for word, score in jieba_ret:
        if word not in stopwords:
            sentence_score += score
    return sentence_score


@singleton
class TfidfSummarization:
    def __init__(self, ratio=0.2):
        self.ratio = ratio

    def analysis(self, doc):
        stopwords = load_stopwords(STOPWORDS)

        # 对文本进行分割
        sentences = split_doc(doc)

        # 存放句子顺序
        sentences_order = {sent: idx for idx, sent in enumerate(sentences)}

        # 存放句子得分
        sentences_score = {sent: calculate_sentence_score(sent, stopwords) for sent in sentences}

        # 根据得分，选出较高得分的句子
        sentences_score_order = sorted(sentences_score.items(), key=lambda item: -item[1])[
                                : int(len(sentences) * self.ratio)]

        # 将较高的分的句子按原文本进行排序输出
        selected_sentences = {sent: sentences_order[sent] for sent, score in sentences_score_order}
        summary = ''.join([sent for sent, order in sorted(selected_sentences.items(), key=lambda item: item[1])])

        return summary


if __name__ == '__main__':
    doc = """为科技和产业发展提供更加充分的人才支撑。"""
