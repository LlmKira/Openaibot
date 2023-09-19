# -*- coding: utf-8 -*-
# @Time    : 2023/9/4 下午11:16
# @Author  : sudoskys
# @File    : evaluate.py
# @Software: PyCharm
import re
from typing import List

from loguru import logger

from .api.keyphrase.keyphrase import KeyPhraseExtraction
from .api.keywords.tfidf import TfidfKeywords
from .api.summarization.textrank_summarization import TextRankSummarization
from .api.summarization.tfidf_summarization import TfidfSummarization
from .api.text_similarity.cosion import CosionSimilarity
from .api.text_similarity.edit import EditSimilarity
from .api.text_similarity.simhash import SimHashSimilarity


class DetectSentence(object):
    """
    检测句子
    """

    @staticmethod
    def detect_language(sentence: str):
        """
        Detect language
        :param sentence: sentence
        :return: 两位大写语言代码 (EN, ZH, JA, KO, FR, DE, ES, ....)
        """
        # 如果全部是空格
        if sentence.isspace() or not sentence:
            return ""
        try:
            from . import langdetect_fasttext
            lang_type = langdetect_fasttext.detect(text=sentence.replace("\n", "").replace("\r", ""),
                                                   low_memory=True).get("lang").upper()
        except Exception as e:
            # handle error
            logger.trace(e)
            from . import langdetect_unicode
            lang_type = langdetect_unicode.detect(text=sentence.replace("\n", "").replace("\r", ""))[0][0].upper()
        return lang_type

    @staticmethod
    def detect_help(sentence: str) -> bool:
        """
        检测是否是包含帮助要求，如果是，返回True，否则返回False
        """
        _check = ['怎么做', 'How', 'how', 'what', 'What', 'Why', 'why', '复述', '复读', '要求你', '原样', '例子',
                  '解释', 'exp', '推荐', '说出', '写出', '如何实现', '代码', '写', 'give', 'Give',
                  '请把', '请给', '请写', 'help', 'Help', '写一', 'code', '如何做', '帮我', '帮助我', '请给我', '什么',
                  '为何', '给建议', '给我', '给我一些', '请教', '建议', '怎样', '如何', '怎么样',
                  '为什么', '帮朋友', '怎么', '需要什么', '注意什么', '怎么办', '助け', '何を', 'なぜ', '教えて',
                  '提案',
                  '何が', '何に',
                  '何をす', '怎麼做', '複述', '復讀', '原樣', '解釋', '推薦', '說出', '寫出', '如何實現', '代碼', '寫',
                  '請把', '請給', '請寫', '寫一', '幫我', '幫助我', '請給我', '什麼', '為何', '給建議', '給我',
                  '給我一些', '請教', '建議', '步驟', '怎樣', '怎麼樣', '為什麼', '幫朋友', '怎麼', '需要什麼',
                  '註意什麼', '怎麼辦']
        for item in _check:
            if item in sentence:
                return True
        return False

    @staticmethod
    def detect_code(sentence) -> bool:
        """
        Detect code，if code return True，else return False
        :param sentence: sentence
        :return: bool
        """
        code = False
        _reco = [
            '("',
            '")',
            ").",
            "()",
            "!=",
            "==",
        ]
        _t = len(_reco)
        _r = 0
        for i in _reco:
            if i in sentence:
                _r += 1
        if _r > _t / 2:
            code = True
        rms = [
            "print_r(",
            "var_dump(",
            'NSLog( @',
            'println(',
            '.log(',
            'print(',
            'printf(',
            'WriteLine(',
            '.Println(',
            '.Write(',
            'alert(',
            'echo(',
        ]
        for i in rms:
            if i in sentence:
                code = True
        return code


class Sim(object):
    """
    文本相似度计算，基于基础 jieba 分词 101 向量
    """

    @staticmethod
    def cosion_similarity(pre, aft):
        """
        基于余弦计算文本相似性 0 - 1 (1为最相似)
        :return: 余弦值
        """
        _cos = CosionSimilarity()
        _sim = _cos.similarity(pre, aft)
        return _sim

    @staticmethod
    def edit_similarity(pre, aft):
        """
        基于编辑计算文本相似性
        :return: 差距
        """
        _cos = EditSimilarity()
        _sim = _cos.edit_dist(pre, aft)
        return _sim

    @staticmethod
    def simhash_similarity(pre, aft):
        """
        采用simhash计算文本之间的相似性
        :return:
        """
        simhash = SimHashSimilarity()
        sim = simhash.run_simhash(pre, aft)
        # print("simhash result: {}\n".format(sim))
        return sim

    @staticmethod
    def vector_similarity(text1_vector: list, text2_vector: list):
        """
        计算两个向量的余弦相似度
        :param text1_vector: 向量1
        :param text2_vector: 向量2
        :return: 余弦相似度
        """
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity([text1_vector], [text2_vector])[0][0]


class Cut(object):
    @staticmethod
    def english_sentence_cut(text) -> list:
        list_ = list()
        for s_str in text.split('.'):
            if '?' in s_str:
                list_.extend(s_str.split('?'))
            elif '!' in s_str:
                list_.extend(s_str.split('!'))
            else:
                list_.append(s_str)
        return list_

    @staticmethod
    def chinese_sentence_cut(text) -> list:
        """
        中文断句
        """
        text = re.sub('([。！？\?])([^’”])', r'\1\n\2', text)
        # 普通断句符号且后面没有引号
        text = re.sub('(\.{6})([^’”])', r'\1\n\2', text)
        # 英文省略号且后面没有引号
        text = re.sub('(\…{2})([^’”])', r'\1\n\2', text)
        # 中文省略号且后面没有引号
        text = re.sub('([.。！？\?\.{6}\…{2}][’”])([^’”])', r'\1\n\2', text)
        # 断句号+引号且后面没有引号
        return text.split("\n")

    def cut_chinese_sentence(self, text):
        """
        中文断句
        """
        p = re.compile("“.*?”")
        listr = []
        index = 0
        for i in p.finditer(text):
            temp = ''
            start = i.start()
            end = i.end()
            for j in range(index, start):
                temp += text[j]
            if temp != '':
                temp_list = self.chinese_sentence_cut(temp)
                listr += temp_list
            temp = ''
            for k in range(start, end):
                temp += text[k]
            if temp != ' ':
                listr.append(temp)
            index = end
        return listr

    def cut_sentence(self, sentence: str) -> List[str]:
        """
        分句
        :param sentence:
        :return:
        """
        language = DetectSentence.detect_language(sentence)
        if language == "CN":
            _reply_list = self.cut_chinese_sentence(sentence)
        elif language == "EN":
            # from nltk.tokenize import sent_tokenize
            _reply_list = self.english_sentence_cut(sentence)
        else:
            _reply_list = [sentence]
        if len(_reply_list) < 1:
            return [sentence]
        return _reply_list


class Extraction(object):
    @staticmethod
    def key_phrase_extraction(sentence: str):
        """
        关键词抽取
        """
        return KeyPhraseExtraction().key_phrase_extraction(text=sentence)

    @staticmethod
    def textrank_summarization(sentence: str, ratio=0.2):
        """
        采用 textrank 进行摘要抽取
        :param sentence: 待处理语句
        :param ratio: 摘要占文本长度的比例
        :return:
        """
        _sum = TextRankSummarization(ratio=ratio)
        _sum = _sum.analysis(sentence)
        return _sum

    @staticmethod
    def tfidf_summarization(sentence: str, ratio=0.5):
        """
        采用tfidf进行摘要抽取
        :param sentence:
        :param ratio: 摘要占文本长度的比例
        :return:
        """
        _sum = TfidfSummarization(ratio=ratio)
        _sum = _sum.analysis(sentence)
        return _sum

    @staticmethod
    def tfidf_keywords(keywords, delete_stopwords=True, top_k=5, with_weight=False):
        """
        tfidf 提取关键词
        :param keywords:
        :param delete_stopwords: 是否删除停用词
        :param top_k: 输出关键词个数
        :param with_weight: 是否输出权重
        :return: [(word, weight), (word1, weight1)]
        """
        tfidf = TfidfKeywords(delete_stopwords=delete_stopwords, topK=top_k, withWeight=with_weight)
        return tfidf.keywords(keywords)
