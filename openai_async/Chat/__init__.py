# -*- coding: utf-8 -*-
# @Time    : 12/6/22 12:02 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys
from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import json
import os
import re

# import loguru
# import jiagu


# 基于 Completion 上层
from openai_async import Completion
from .text_analysis_tools.api.keywords.tfidf import TfidfKeywords
from .text_analysis_tools.api.summarization.tfidf_summarization import TfidfSummarization
from .text_analysis_tools.api.text_similarity.simhash import SimHashSimilarity
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
                temp_list = self.chinese_sentence_cut(temp)
                listr += temp_list
            temp = ''
            for k in range(start, end):
                temp += text[k]
            if temp != ' ':
                listr.append(temp)
            index = end
        return listr

    @staticmethod
    def isCode(sentence):
        code = False
        _reco = [
            '("',
            '")',
            ").",
            "()",
            "!=",
            "=="
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

    @staticmethod
    def get_language(sentence: str):
        language = "english"
        # 差缺中文系统
        if len([c for c in sentence if ord(c) > 127]) / len(sentence) > 0.5:
            language = "chinese"
        if Talk.isCode(sentence):
            language = "code"
        return language

    def cut_sentence(self, sentence: str) -> list:
        language = self.get_language(sentence)
        if language == "chinese":
            _reply_list = self.cut_chinese_sentence(sentence)
        elif language == "english":
            # from nltk.tokenize import sent_tokenize
            _reply_list = self.english_sentence_cut(sentence)
        else:
            _reply_list = [sentence]
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


# 聊天类


class Chatbot(object):
    def __init__(self, api_key, conversation_id, token_limit: int = 3500, restart_sequ: str = "\n某人:",
                 start_sequ: str = "\n我: ",
                 call_func=None):
        """
        chatGPT 的实现由上下文实现，所以我会做一个存储器来获得上下文
        :param api_key:
        :param conversation_id: 独立ID,每个场景需要独一个
        :param call_func: 回调
        """
        self._api_key = api_key
        self.conversation_id = str(conversation_id)
        self._MsgFlow = MsgFlow(uid=self.conversation_id)
        self._start_sequence = start_sequ
        self._restart_sequence = restart_sequ
        # 防止木头
        if not self._start_sequence.strip().endswith(":"):
            self._start_sequence = self._start_sequence + ":"
        if not self._restart_sequence.strip().endswith(":"):
            self._restart_sequence = self._restart_sequence + ":"
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
            REPLY = [""]
        # 构建一轮对话场所
        _msg = {"ask": f"{self._restart_sequence}{prompt}", "reply": f"{self._start_sequence}{REPLY[0]}"}
        # 存储成对的对话
        self._MsgFlow.saveMsg(msg=_msg)
        # 拒绝分条存储
        # self._MsgFlow.save(prompt=prompt, role=self._restart_sequence)
        # self._MsgFlow.save(prompt=REPLY[0], role=self._start_sequence)
        return REPLY

    @staticmethod
    def random_string(length):
        """
        生成随机字符串
        :param length:
        :return:
        """
        import string
        import random
        all_chars = string.ascii_letters + string.digits
        result = ''
        for i in range(length):
            result += random.choice(all_chars)
        return result

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

    def Summer(self, prompt: str, memory: list, extra_token: int = 0) -> list:
        """
        只负责处理消息桶
        :param prompt: 记忆提示
        :param extra_token: 记忆的限制
        :param memory: 记忆桶
        PS:你可以启动根目录的 fastapi server 来使用 http 请求调用处理相同格式
        :return: 新的列表
        """
        # {"ask": self._restart_sequence+prompt, "reply": self._start_sequence+REPLY[0]}
        # 刚开始玩直接返回原表
        # 提取内容
        _memory = []
        for i in memory:
            _memory.append(i["content"])
        memory = _memory

        # loguru.logger.debug(memory)

        def _dict_ou(meo):
            _list = []
            for _ir in range(len(meo)):
                if meo[_ir].get("ask") and meo[_ir].get("reply"):
                    _list.append(meo[_ir].get("ask"))
                    _list.append(meo[_ir].get("reply"))
            return _list

        if len(memory) < 3:
            return _dict_ou(memory)

        # 组建对话意图
        _Final = []

        # 遗忘黑历史
        _chat = []

        # 强调记忆
        _High = []
        _high_count = 0
        _index = []
        for i in range(len(memory)):
            if memory[i].get("ask") and memory[i].get("reply"):
                _high_count += 1
                _High.append(memory[i].get("ask"))
                _High.append(memory[i].get("reply"))
                _index.append(memory[i])
                if _high_count > 2:
                    break
        for i in _index:
            memory.remove(i)

        # 筛选标准发言机器
        _index = []
        for i in range(len(memory)):
            if memory[i].get("ask") and memory[i].get("reply"):
                ___now = memory[i]["ask"].split(":", 1)
                ___after = memory[i]["reply"].split(":", 1)
                if len(___now) < 2 or len(___after) < 2:
                    continue
                if len(___now[1]) < 3 or len(___after[1]) < 3:
                    _index.append(memory[i])
                    # 忽略对话
            else:
                # 不是标准对话
                _index.append(memory[i])
        for i in _index:
            memory.remove(i)

        # 计算待处理表需要的token
        _high_token = 0
        for i in _High:
            _high_token = _high_token + Talk.tokenizer(i)
        _create_token = self.__token_limit - _high_token - extra_token
        # 计算关联
        _sim = []
        _now_token = 0
        for i in range(len(memory)):
            __ask = memory[i].get("ask")
            __reply = memory[i].get("reply")
            _ask = __ask.split(":", 1)
            _reply = __reply.split(":", 1)
            _diff1 = Talk.simhash_similarity(pre=prompt, aft=_ask[1])
            _diff2 = Talk.simhash_similarity(pre=prompt, aft=_reply[1])
            if _diff2 < 20 or _diff1 < 20:
                _diff = _diff1 if _diff1 < _diff2 else _diff2
                if _create_token - Talk.tokenizer(__ask + __reply) < 0:
                    break
                else:
                    _sim.append({"diff": _diff, "content": memory[i]})
        # 取出
        _sim.sort(key=lambda x: x['diff'])
        _sim_content = list([x['content'] for x in _sim])

        # 计算关联并填充余量
        _create_token = _create_token - _now_token
        _relate = []
        for i in range(len(memory)):
            # 计算相似度
            __ask = memory[i].get("ask")
            __reply = memory[i].get("reply")
            _ask = __ask.split(":", 1)
            _reply = __reply.split(":", 1)
            add = False
            _key = Talk.tfidf_keywords(prompt, topK=3)
            for ir in _key:
                if ir in _ask + _reply:
                    add = True
            if add and _create_token - Talk.tokenizer(__ask + __reply) > 0:
                _relate.append(memory[i])
        _sim_content.extend(_relate)
        _sim_content = list(reversed(_sim_content))
        _useful = []
        for i in range(len(_sim_content)):
            __ask = _sim_content[i].get("ask")
            __reply = _sim_content[i].get("reply")
            _ask = __ask.split(":", 1)
            _reply = __reply.split(":", 1)
            _useful.append(__ask)
            _useful.append(__reply)
        _Final.extend(_useful)
        _Final.extend(_High)
        token_limit = self.__token_limit - extra_token
        # 裁剪
        _now = 0
        _out = False
        for i in range(len(_Final)):
            _now += Talk.tokenizer(_Final[i])
            if _now > token_limit:
                _out = True
        if _out:
            for i in range(len(_Final)):
                if Talk.tokenizer(_Final[i]) > 240:
                    if Talk.get_language(_Final[i]) == "chinese":
                        _sum = Talk.tfidf_summarization(sentence=_Final[i], ratio=0.3)
                        if len(_sum) > 7:
                            _Final[i] = _sum
        _now = 0
        _index = []
        for i in range(len(_Final)):
            _now += Talk.tokenizer(_Final[i])
            if _now > token_limit:
                _index.append(_Final[i])
        for i in _index:
            _Final.remove(i)
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
            head = f"\n{self._restart_sequence}让我们谈谈吧。"
        if character is None:
            character = ["helpful", "creative", "clever", "friendly", "lovely", "talkative"]
        _character = ",".join(character)
        if role is None:
            role = f"I am a {_character} assistant."
        else:
            role = f"I am a {_character} assistant.\n{self._start_sequence}{role}. "
        _header = f"{role}\n{head}\n"
        _prompt_s = [f"{self._restart_sequence}{prompt}."]
        _prompt_memory = self._MsgFlow.read()
        # 寻找记忆和裁切上下文
        # 占位限制
        _extra_token = int(
            len(_prompt_memory) + Talk.tokenizer(self._start_sequence) + max_tokens + Talk.tokenizer(
                _header + _prompt_s[0]))
        _prompt_apple = self.Summer(prompt=prompt, memory=_prompt_memory,
                                    extra_token=_extra_token)
        # loguru.logger.debug(_prompt_apple)
        _prompt_apple.extend(_prompt_s)
        # 拼接请求内容
        _prompt = '\n'.join(_prompt_apple) + f"\n{self._start_sequence}"  # 这里的上面要额外 （条目数量） 计算代币 /n 占一个空格
        # 重切割
        _mk = self.__token_limit - max_tokens - Talk.tokenizer(_header)  # 计算余量
        if _mk < 0:
            _mk = 0
        while Talk.tokenizer(_prompt) > _mk:
            _prompt = _prompt[1:]
        if _mk > 0:
            _prompt = _header + _prompt
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
            stop=[f"{self._start_sequence}:", f"{self._restart_sequence}:"],
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
