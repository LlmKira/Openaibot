# -*- coding: utf-8 -*-
# @Time    : 12/6/22 12:02 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys
from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import json
import os
import random
import re

# import loguru
# import jiagu
from snownlp import SnowNLP
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.utils import get_stop_words

# 基于 Completion 上层
from openai_async import Completion
from .text_analysis_tools.api.keywords.tfidf import TfidfKeywords
from .text_analysis_tools.api.summarization.tfidf_summarization import TfidfSummarization
from ..utils.data import MsgFlow


class Talk(object):
    @staticmethod
    def tfidf_summarization(sentence: str, ratio=0.5):
        """
        采用tfidf进行摘要抽取
        :param sentence:
        :param ratio: 摘要占文本长度的比例
        :return:
        """
        summ = TfidfSummarization(ratio=ratio)
        summ = summ.analysis(sentence)
        return summ

    @staticmethod
    def tfidf_keywords(keywords, delete_stopwords=True, topK=5, withWeight=False):
        """
        tfidf 提取关键词
        :param keywords:
        :param delete_stopwords: 是否删除停用词
        :param topK: 输出关键词个数
        :param withWeight: 是否输出权重
        :return: [(word, weight), (word1, weight1)]
        """
        tfidf = TfidfKeywords(delete_stopwords=delete_stopwords, topK=topK, withWeight=withWeight)
        return tfidf.keywords(keywords)

    @staticmethod
    def tokenizer(s: str) -> float:
        """
        谨慎的计算器，会预留 5 token
        :param s:
        :return:
        """
        # 统计中文字符数量
        num_chinese = len([c for c in s if ord(c) > 127])
        # 统计非中文字符数量
        num_non_chinese = len([c for c in s if ord(c) <= 127])
        return int(num_chinese * 2 + num_non_chinese * 0.25) + 5

    @staticmethod
    def normal_cut_sentence(text):
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
                temp_list = self.normal_cut_sentence(temp)
                listr += temp_list
            temp = ''
            for k in range(start, end):
                temp += text[k]
            if temp != ' ':
                listr.append(temp)
            index = end
        return listr

    @staticmethod
    def get_language(sentence: str):
        language = "english"
        # 差缺中文系统
        if len([c for c in sentence if ord(c) > 127]) / len(sentence) > 0.5:
            language = "chinese"
        return language

    def cut_sentence(self, sentence: str) -> list:
        language = self.get_language(sentence)
        if language == "chinese":
            _reply_list = self.cut_chinese_sentence(sentence)
        else:
            from nltk.tokenize import sent_tokenize
            _reply_list = sent_tokenize(sentence, language=language)
        if len(_reply_list) < 1:
            return [sentence]
        return _reply_list

    def cut_ai_prompt(self, prompt: str) -> list:
        """
        切薄负载机
        :param prompt:
        :return:
        """
        _some = prompt.split(":", 1)
        _head = ""
        if len(_some) > 1:
            _head = f"{_some[0]}:"
            prompt = _some[1]
        _reply = self.cut_sentence(prompt)
        _prompt_list = []
        for item in _reply:
            _prompt_list.append(f"{_head}{item.strip()}")
        _prompt_list = list(filter(None, _prompt_list))
        return _prompt_list

    @staticmethod
    def summary_v2(sentence, n):
        # 差缺中文系统
        LANGUAGE = "english"
        # 统计中文字符数量
        if len([c for c in sentence if ord(c) > 127]) / len(sentence) > 0.5:
            _chinese = True
            LANGUAGE = "chinese"
        parser = PlaintextParser.from_string(sentence, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)
        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
        _words = summarizer(parser.document, n)
        _words = [str(i) for i in _words]
        _return = "".join(_words)
        return _return

    @staticmethod
    def summary(sentence, n):
        """
        :param sentence: 字符串
        :param n: 几句话
        :return: 总结
        """
        # 差缺中文系统
        _chinese = False
        # 统计中文字符数量
        if len([c for c in sentence if ord(c) > 127]) / len(sentence) > 0.5:
            _chinese = True
        if _chinese:
            try:
                s = SnowNLP(sentence)  # str为之前去掉符号的中文字符串
                _sum = (s.summary(round(n)))  # 进行总结 summary
                # _sum = jiagu.summarize(sentence, round(n / 10))
            except Exception as e:
                _sum = [sentence]
            content = ",".join(_sum)  # 摘要
        else:
            import nltk
            nltk.download('punkt')
            nltk.download('stopwords')
            tokens = nltk.word_tokenize(sentence)
            # 分句
            sentences = nltk.sent_tokenize(sentence)
            # 计算词频
            frequencies = nltk.FreqDist(tokens)
            # 计算每个句子的得分
            scores = {}
            for sentence_ in sentences:
                score = 0
                for word in nltk.word_tokenize(sentence_):
                    if word in frequencies:
                        score += frequencies[word]
                scores[sentence_] = score
            # 按照得分顺序排序句子
            sorted_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            # 返回前 num_sentences 个句子
            return_num = round(n / 2)
            if len(sorted_sentences) < return_num:
                return_num = len(sorted_sentences)
            _list = [sentence_[0] for sentence_ in sorted_sentences[:return_num]]
            content = ",".join(_list)
        if len(content.strip(" ")) == 0:
            content = sentence
        return content


class Chatbot(object):
    def __init__(self, api_key, conversation_id, token_limit: int = 3000, restart_sequ: str = "\nHuman:",
                 start_sequ: str = "\nAI: ",
                 call_func=None):
        """
        chatGPT 的实现由上下文实现，所以我会做一个存储器来获得上下文
        :param api_key:
        :param conversation_id: 独立ID,每个场景需要独一个
        :param call_func: 回调
        """
        self._api_key = api_key
        self.conversation_id = conversation_id
        self._MsgFlow = MsgFlow(uid=self.conversation_id)
        self._start_sequence = start_sequ
        self._restart_sequence = restart_sequ
        self.__call_func = call_func
        self.__token_limit = token_limit

    def reset_chat(self):
        # Forgets conversation
        return self._MsgFlow.forget()

    def record_ai(self, prompt, response):
        REPLY = []
        Choice = response.get("choices")
        if Choice:
            for item in Choice:
                _text = item.get("text")
                REPLY.append(_text)
        if not REPLY:
            REPLY = ["(Ai Say Nothing)"]
        self._MsgFlow.save(prompt=prompt, role=self._restart_sequence)
        self._MsgFlow.save(prompt=REPLY[0], role=self._start_sequence)
        return REPLY

    @staticmethod
    def random_string(length):
        import string  # 导入string模块
        import random  # 导入random模块

        all_chars = string.ascii_letters + string.digits  # 获取所有字符，包括大小写字母和数字

        result = ''  # 创建一个空字符串用于保存生成的随机字符

        for i in range(length):
            result += random.choice(all_chars)  # 随机选取一个字符，并添加到result中

        return result  # 返回生成的随机字符

    # _prompt = random_string(3700)

    def get_hash(self):
        import hashlib
        my_string = str(self.conversation_id)
        # 使用 hashlib 模块中的 sha256 算法创建一个散列对象
        hash_object = hashlib.sha256(my_string.encode())
        return hash_object.hexdigest()

    @staticmethod
    def zip_str(_item):
        # 读取字典
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".", "vocab.json")
        )
        with open(path, encoding="utf8") as f:
            target = json.loads(f.read())
        # 遍历字典键值对
        for key, value in target.items():
            # 使用 str.replace() 方法替换字符串中的键
            _item = _item.replace(key, value)
        return _item

    def Summer(self, prompt: str, chat_list: list, extra_token: int = 0) -> list:
        """
        负责统计超长上下文
        :param prompt:
        :param extra_token: 换行符号预期会占用的位置
        :param chat_list: 对话字符串列表，从消息桶中输入。
        PS:你可以启动根目录的 fastapi server 来使用 http 请求调用处理相同格式
        :return: 新的列表
        """
        # 定义 token = token - extra
        # 为了处理超长上下文一个 关键词提取机器 和 分词，分句子机器。
        # 我们对 prompt 进行提取关键词，选高频词。
        # 对列表进行如下处理

        # 将对话组成二维表。连续的并列发言人抛弃上一位。
        # 过滤空的，重复的，过短的提问组。
        # 将最近的3组发言转入高注意力表，进行初步简化和语义提取，计算 token，计算剩余token。
        # 使用高频词筛选关键对话加入处理表，弹出原表：(根据逗号分选长表和短表)对于短句直接加入，对于超长句进行二次分割，把关键词左中右三句加入。
        # 计算 token，如果超过了剩余 token，抛弃超短句和早的句子，从表头弹出它们。
        # 如果没达到要求，那么随机选取无关数据加入处理表。
        # 第一位 链接 处理表 链接 高注意力表。
        # 最后计算进行强制 while 裁剪
        # 刚开始玩随便了
        if len(chat_list) < 5:
            return chat_list
        # 组建最终注意力表
        _Final = []
        # 弹出第一位
        _head = chat_list.pop(0)
        # 组建待处理表
        _chat = []
        __last_author = ""
        # 筛选标准发言机器
        for i in range(len(chat_list) - 2):
            if ":" in chat_list[i]:
                ___now = chat_list[i].split(":", 1)
                ___after = chat_list[i + 1].split(":", 1)
                if len(___now[1]) < 3 or len(___after[1]) < 3:
                    continue
                if ___now[0] != ___after[0]:
                    _chat.append(chat_list[i])
        # 切割最近的数据进行高注意力控制
        _chat.extend(Talk().cut_ai_prompt(chat_list[-1]))
        _chat.extend(Talk().cut_ai_prompt(chat_list[-2]))
        # 弹出chat的最后四条
        if len(_chat) > 3:
            _High = [_chat.pop(-1), _chat.pop(-1), _chat.pop(-1)]
        else:
            _High = []
        # 计算待处理表需要的token
        _high_token = 0 + Talk.tokenizer(_head)
        for i in _High:
            _high_token = _high_token + Talk.tokenizer(i)
        _create_token = self.__token_limit - _high_token - extra_token
        if _create_token < 20:
            return chat_list
        # 切分中插
        _pre_chat = []
        for i in range(len(_chat)):
            _item = _chat[i]
            if Talk.tokenizer(_item) > 200:
                if Talk.get_language(_item) == "chinese":
                    _sum = Talk.tfidf_summarization(sentence=_item, ratio=0.3)
                    if len(_sum) > 7:
                        _pre_chat.append(_sum)
                else:
                    _cut = Talk().cut_ai_prompt(prompt=_item)
                    if len(_cut) > 3:
                        _pre_chat.append(_cut[0])
                        _pre_chat.append(_cut[1])
                        _pre_chat.append(_cut[2])
                    else:
                        _pre_chat.extend(_cut)
            else:
                _pre_chat.append(_item)
        # 累计有效Token，从下向上加入
        _now_token = 0
        _useful = []
        __useful_down = False
        for i in reversed(range(len(_pre_chat))):
            _item = _pre_chat[i]
            _key = Talk.tfidf_keywords(prompt)
            for ir in _key:
                if ir in _item:
                    _useful.append(_item)
                    _now_token = _now_token + Talk.tokenizer(_item)
                    if _now_token > _create_token:
                        __useful_down = True
                        break
        # 竟然没凑齐
        _not_useful = []
        if not __useful_down:
            for i in reversed(range(len(_pre_chat) - 1)):
                _item = random.choice(_pre_chat)
                if ":" in _pre_chat[i]:
                    ___now = _pre_chat[i].split(":", 1)
                    ___after = _pre_chat[i + 1].split(":", 1)
                    if len(___now[1]) < 3 or len(___after[1]) < 3:
                        continue
                    if ___now[0] != ___after[0]:
                        _not_useful.append(_item)
                        _now_token = _now_token + Talk.tokenizer(_item)
                        if _now_token > _create_token:
                            break
        _Final.append(_head)
        _Final.extend(_not_useful)
        _Final.extend(_useful)
        _Final.extend(_High)
        return _Final

    async def get_chat_response(self, prompt: str, max_tokens: int = 150, model: str = "text-davinci-003",
                                character: list = None, head: str = None, role: str = None) -> dict:
        """
        异步的，得到对话上下文
        :param role:
        :param head: 预设技巧
        :param max_tokens: 限制返回字符数量
        :param model: 模型选择
        :param prompt: 提示词
        :param character: 性格提示词，列表字符串
        :return:
        """
        # 预设
        if head is None:
            head = f"\nHuman: 你好，让我们开始愉快的谈话！\nAI: 我是 AI assistant ，请问你有什么问题？"
        if character is None:
            character = ["helpful", "creative", "clever", "friendly", "lovely", "talkative"]
        _character = ",".join(character)
        # 初始化
        if role is None:
            role = f"The following is a conversation with Ai assistant. The assistant is {_character}."
        _old = self._MsgFlow.read()
        # 构造内容
        _head = [f"{role}\n{head}\n"]
        _old_list = [f"{x['role']} {x['prompt']}" for x in _old]
        _now = [f"{self._restart_sequence}{prompt}."]
        # 拼接
        _prompt_table = _head + _old_list + _now
        # 截断器
        _prompt_apple = self.Summer(prompt=prompt, chat_list=_prompt_table,
                                    extra_token=int(
                                        len(_prompt_table) + Talk.tokenizer(self._start_sequence) + max_tokens))
        _header = _prompt_apple.pop(0)
        _prompt = '\n'.join(_prompt_apple) + f"\n{self._start_sequence}"  # 这里的上面要额外 （条目数量） 计算代币 /n 占一个空格
        # 重切割代币
        _mk = self.__token_limit - max_tokens - Talk.tokenizer(_header)  # 余量？
        if _mk < 0:
            _mk = 0
        while Talk.tokenizer(_prompt) > _mk - 10:
            _prompt = _prompt[1:]
        if _mk > 0:
            _prompt = _header + _prompt
        # loguru.logger.debug(_prompt)
        response = await Completion(api_key=self._api_key, call_func=self.__call_func).create(
            model=model,
            prompt=_prompt,
            temperature=0.9,
            max_tokens=max_tokens,
            top_p=1,
            n=1,
            frequency_penalty=0,
            presence_penalty=0.5,
            user=str(self.get_hash()),
            stop=["Human:", "AI:"],
        )
        self.record_ai(prompt=prompt, response=response)
        return response

    @staticmethod
    def str_prompt(prompt: str) -> list:
        range_list = prompt.split("\n")
        # 如果当前项不包含 `:`，则将其并入前一项中
        result = [range_list[i] + range_list[i + 1] if ":" not in range_list[i] else range_list[i] for i in
                  range(len(range_list))]
        # 使用列表推导式过滤掉空白项
        filtered_result = [x for x in result if x != ""]
        # 输出处理后的结果
        return filtered_result
