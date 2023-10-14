# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:05
# @Author  : sudoskys
# @File    : action.py
# @Software: PyCharm
import hashlib
import json
from typing import List

import tiktoken
from pydantic import BaseModel

from llmkira.sdk.filter.evaluate import Sim
from llmkira.sdk.schema import Message, standardise


# 生成MD5
def generate_md5(string):
    hl = hashlib.md5()
    hl.update(string.encode(encoding='utf-8'))
    return str(hl.hexdigest())


class Tokenizer(object):
    __encode_cache = {}

    def clear_cache(self):
        self.__encode_cache = {}

    def num_tokens_from_messages(self, messages: List[Message], model="gpt-3.5-turbo-0613") -> int:
        """Return the number of tokens used by a list of messages_box."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}."""
            )
        num_tokens = 0
        for message in messages:
            message = standardise(message)
            num_tokens += tokens_per_message
            for key, value in message.dict().items():
                if isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                _uid = generate_md5(str(value))
                # 缓存获取 cache，减少重复 encode 次数
                if _uid in self.__encode_cache:
                    _tokens = self.__encode_cache[_uid]
                else:
                    _tokens = len(encoding.encode(value))
                    self.__encode_cache[_uid] = _tokens
                num_tokens += _tokens
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


TokenizerObj = Tokenizer()


class Scraper(BaseModel):
    """
    刮削器
    始终按照顺序排列，削除得分低的条目
    Scraper is a class that sorts a list of messages_box by their score.
    """

    class Sorter(BaseModel):
        message: Message
        # 得分
        score: float
        # 顺序
        order: int

    # 消息列表
    messages_box: List[Sorter] = []
    # 最大消息数
    max_messages: int = 12

    # 计数器
    tick: int = 0

    # 方法：添加消息
    def add_message(self, message: Message, score: float):
        if not hasattr(message, "content"):
            return None
        self.messages_box.append(self.Sorter(message=message, score=score, order=self.tick))
        self.tick += 1
        # 按照顺序排序
        self.messages_box.sort(key=lambda x: x.order)
        while len(self.messages_box) > self.max_messages:
            self.messages_box.pop(0)

    # 方法：获取消息
    def get_messages(self) -> List[Message]:
        # 按照顺序排序
        # self.messages_box.sort(key=lambda x: x.order)
        _message = [standardise(sorter.message) for sorter in self.messages_box]
        # 去重
        # [*dict.fromkeys(_message)]
        # -> unhashable type: 'Message'
        # logger.debug(_message)
        return _message

    def build_messages(self):
        # 只取三个，末位匹配
        _message = self.get_messages()
        if len(_message) < 3:
            return _message
        _build = []
        _must = _message[-3:]
        _check_list = _message[:-3]
        _match_sentence = _message[-1:][0].content
        for item_obj in _check_list:
            if Sim.cosion_similarity(pre=_match_sentence, aft=item_obj.content) < 0.9:
                _build.append(item_obj)
            else:
                pass
                # logger.warning(f"ignore sim item {item_obj}")
        _build.extend(_must)
        return _build

    # 方法：获取消息数
    def get_num_messages(self) -> int:
        return len(self.messages_box)

    # 方法：清除消息到负载
    def reduce_messages(self, limit: int = 2048):
        # 预留位
        if limit > 1000:
            limit = limit - 250
        else:
            limit = limit - 70

        # 执行删除操作
        if TokenizerObj.num_tokens_from_messages(self.get_messages()) > limit:
            # 从最旧开始删除
            self.messages_box.sort(key=lambda x: x.order)
            while TokenizerObj.num_tokens_from_messages(self.get_messages()) > limit:
                if len(self.messages_box) > 1:
                    self.messages_box.pop(0)
                else:
                    self.messages_box[0].message.content = self.messages_box[0].message.content[:limit]
        # 按照顺序排序
        self.messages_box.sort(key=lambda x: x.order)
