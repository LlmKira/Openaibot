# -*- coding: utf-8 -*-
# @Time    : 12/6/22 12:02 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys

import json
import os
import random
import re
import openai_async
# import loguru
# import jiagu


# 基于 Completion 上层
from ..resouce import Completion
from .text_analysis_tools.api.keywords.tfidf import TfidfKeywords
from .text_analysis_tools.api.summarization.tfidf_summarization import TfidfSummarization
from .text_analysis_tools.api.text_similarity.simhash import SimHashSimilarity
from ..utils.data import MsgFlow
from transformers import GPT2TokenizerFast

gpt_tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")


class Talk(object):
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
        return len(gpt_tokenizer.encode(s))

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
    def __init__(self, api_key: str = None, conversation_id: int = 1, token_limit: int = 3505,
                 restart_sequ: str = "\nSomeone:",
                 start_sequ: str = "\nReply: ",
                 call_func=None):
        """
        chatGPT 的实现由上下文实现，所以我会做一个存储器来获得上下文
        :param api_key:
        :param conversation_id: 独立ID,每个场景需要独一个
        :param call_func: 回调
        """
        if api_key is None:
            api_key = openai_async.api_key
        if isinstance(api_key, list):
            api_key: list
            if not api_key:
                raise RuntimeError("NO KEY")
            api_key = random.choice(api_key)
            api_key: str
        self.__api_key = api_key
        if not api_key:
            raise RuntimeError("NO KEY")
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
        _msg = {"weight": 0, "ask": f"{self._restart_sequence}{prompt}", "reply": f"{self._start_sequence}{REPLY[0]}"}
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

    def convert_msgflow_to_list(self, msg_list: list) -> list:
        """
        提取以单条 msgflow 组成的列表的回复。
        :param msg_list:
        :return:
        """
        _result = []
        for ir in msg_list:
            ask, reply = self._MsgFlow.get_content(ir, sign=True)
            _result.append(ask)
            _result.append(reply)
        return _result

    def Summer(self, prompt: str, memory: list, attention: int = 4, extra_token: int = 0) -> list:
        """
        以单条消息为对象处理达标并排序时间轴
        数据清洗采用权重设定，而不操作元素删减
        :param attention: 注意力
        :param prompt: 记忆提示
        :param extra_token: 记忆的限制
        :param memory: 记忆桶
        :return: 新的列表
        """
        # 单条消息的内容 {"ask": self._restart_sequence+prompt, "reply": self._start_sequence+REPLY[0]}
        _create_token = self.__token_limit - extra_token
        # 入口检查
        if len(memory) - attention < 0:
            return self.convert_msgflow_to_list(memory)
        # 组建
        for i in range(len(memory) - attention, len(memory)):
            memory[i]["content"]["weight"] = 1000
        # 筛选标准发言机器
        _index = []
        for i in range(0, len(memory) - attention):
            ask, reply = self._MsgFlow.get_content(memory[i], sign=False)
            if len(ask) < 1 or len(reply) < 1:
                memory[i]["content"]["weight"] = 0
        # 相似度检索
        for i in range(0, len(memory) - attention):
            ask, reply = self._MsgFlow.get_content(memory[i], sign=False)
            _diff1 = Talk.simhash_similarity(pre=prompt, aft=ask)
            _diff2 = Talk.simhash_similarity(pre=prompt, aft=reply)
            _diff = (_diff1 + _diff2) / 2
            memory[i]["content"]["weight"] = (100 - _diff)  # 相比于关键词检索有 2个优先级
        # 主题检索
        _key = Talk.tfidf_keywords(prompt, topK=3)
        for i in range(0, len(memory) - attention):
            ask, reply = self._MsgFlow.get_content(memory[i], sign=False)
            for ir in _key:
                if ir in f"{ask}{reply}":
                    memory[i]["content"]["weight"] = 150
        # 进行筛选，计算限制
        _msg_flow = []
        _now_token = 0
        memory = sorted(memory, key=lambda x: x['time'], reverse=True)
        for i in range(0, len(memory)):
            if memory[i]["content"]["weight"] > 80:
                ask, reply = self._MsgFlow.get_content(memory[i], sign=True)
                _now_token += Talk.tokenizer(f"{ask}{reply}")
                if _now_token > _create_token:
                    # print(f"{ask}-> {_now_token}")
                    break
                _msg_flow.append(memory[i])
        _msg_flow = sorted(_msg_flow, key=lambda x: x['time'], reverse=False)
        # print(_msg_flow)
        _msg_flow_list = self.convert_msgflow_to_list(_msg_flow)
        """
                if _out:
            for i in range(len(_Final)):
                if Talk.tokenizer(_Final[i]) > 240:
                    if Talk.get_language(_Final[i]) == "chinese":
                        _sum = Talk.tfidf_summarization(sentence=_Final[i], ratio=0.3)
                        if len(_sum) > 7:
                            _Final[i] = _sum
        """
        return _msg_flow_list

    async def get_chat_response(self, prompt: str, max_tokens: int = 200, model: str = "text-davinci-003",
                                character: list = None, head: str = None, role: str = "") -> dict:
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
        _role = f"I am [{self._start_sequence}] following.\nI am a [{_character}] assistant.\n"
        if role:
            if len(f"{role}") > 5:
                _role = f"I am [{self._start_sequence}] following.\n{role}.\n"
        _header = f"{_role}\n{head}\n"
        # 构建主体
        _prompt_s = [f"{self._restart_sequence}{prompt}."]
        _prompt_memory = self._MsgFlow.read()

        # 占位限制
        _extra_token = int(
            len(_prompt_memory) +
            Talk.tokenizer(self._start_sequence) +
            max_tokens +
            Talk.tokenizer(_header + _prompt_s[0]))
        _prompt_apple = self.Summer(prompt=prompt, memory=_prompt_memory, extra_token=_extra_token)
        _prompt_apple.extend(_prompt_s)

        # 拼接提示词汇
        _prompt = '\n'.join(_prompt_apple) + f"\n{self._start_sequence}"

        # 重切割
        _limit = self.__token_limit - max_tokens - Talk.tokenizer(_header)
        _mk = _limit if _limit > 0 else 0
        while Talk.tokenizer(_prompt) > _mk:
            _prompt = _prompt[1:]
        _prompt = _header + _prompt
        # 响应
        response = await Completion(api_key=self.__api_key, call_func=self.__call_func).create(
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
