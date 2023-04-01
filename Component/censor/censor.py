# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午10:21
# @Author  : sudoskys
# @File    : censor.py
# @Software: PyCharm
import base64
import pathlib
import re

import httpx
import pycorrector
from loguru import logger


class Censor(object):
    @staticmethod
    def initialize_word_lists(urls: dict, home_dir: str = "./", proxy=None):
        errors = []
        for name, url_list in urls.items():
            words = []
            for url in url_list:
                try:
                    url = str(base64.b64decode(url), 'utf-8')
                except Exception as e:
                    # ignore
                    continue
                try:
                    response = httpx.get(url, proxies=proxy)
                    if response.status_code == 200:
                        tmp_list = response.text.encode(response.encoding).decode('utf-8').split("\n")
                        for word in tmp_list:
                            cleaned_word = word.strip(",").strip("\n")
                            if cleaned_word and len(cleaned_word) >= 2:
                                words.append(cleaned_word)
                    else:
                        logger.error(f"Failed to initialize word list from {url}")
                        errors.append(url)
                except Exception as e:
                    logger.error(f"Failed to request {url} ({str(e)})")
                    errors.append(url)
            # 去重
            if words:
                with open(home_dir + name, "w+", encoding='utf-8') as f:
                    f.write("\n".join(list(set(words))))
                logger.error(f"Initialized word list {name} with {len(words)} words")
            else:
                logger.warning(f"No words found while initializing {name}")
        return list(urls.keys()), errors


class DFA:
    def __init__(self, path: str = None):
        self.ban_words_set = set()
        self.ban_words_list = list()
        self.ban_words_dict = dict()
        if not path:
            self.path = 'Data/Danger.form'
        else:
            self.path = path
        self.get_words()

    # 获取敏感词列表
    def get_words(self):
        with open(self.path, 'r', encoding='utf-8-sig') as f:
            for s in f:
                if s.find('\\r'):
                    s = s.replace('\r', '')
                s = s.replace('\n', '')
                s = s.strip()
                if len(s) == 0:
                    continue
                if str(s) and s not in self.ban_words_set:
                    self.ban_words_set.add(s)
                    self.ban_words_list.append(str(s))
                    sentence = pycorrector.simplified2traditional(s)
                    if sentence != s:
                        self.ban_words_set.add(sentence)
                        self.ban_words_list.append(str(sentence))
        self.add_hash_dict(self.ban_words_list)

    def change_words(self, path):
        self.ban_words_list.clear()
        self.ban_words_dict.clear()
        self.ban_words_set.clear()
        self.path = path
        self.get_words()

    # 将敏感词列表转换为DFA字典序
    def add_hash_dict(self, new_list):
        for x in new_list:
            self.add_new_word(x)

    # 添加单个敏感词
    def add_new_word(self, new_word):
        new_word = str(new_word)
        # print(new_word)
        now_dict = self.ban_words_dict
        i = 0
        for x in new_word:
            if x not in now_dict:
                x = str(x)
                new_dict = dict()
                new_dict['is_end'] = False
                now_dict[x] = new_dict
                now_dict = new_dict
            else:
                now_dict = now_dict[x]
            if i == len(new_word) - 1:
                now_dict['is_end'] = True
            i += 1

    # 寻找第一次出现敏感词的位置
    def find_illegal(self, _str):
        now_dict = self.ban_words_dict
        i = 0
        start_word = -1
        is_start = True  # 判断是否是一个敏感词的开始
        while i < len(_str):
            if _str[i] not in now_dict:
                if is_start is True:
                    i += 1
                    continue
                i = start_word + 1
                start_word = -1
                is_start = True
                now_dict = self.ban_words_dict
            else:
                if is_start is True:
                    start_word = i
                    is_start = False
                now_dict = now_dict[_str[i]]
                if now_dict['is_end'] is True:
                    return start_word
                else:
                    i += 1
        return -1

    # 查找是否存在敏感词
    def exists(self, sentence):
        pos = self.find_illegal(sentence)
        _sentence = re.sub('\W+', '', sentence).replace("_", '')
        _pos = self.find_illegal(_sentence)
        if pos == -1 and _pos == -1:
            return False
        else:
            return True

    # 将指定位置的敏感词替换为*
    def filter_words(self, filter_str, pos):
        now_dict = self.ban_words_dict
        end_str = int()
        for i in range(pos, len(filter_str)):
            if now_dict[filter_str[i]]['is_end'] is True:
                end_str = i
                break
            now_dict = now_dict[filter_str[i]]
        num = end_str - pos + 1
        filter_str = filter_str[:pos] + '喵' * num + filter_str[end_str + 1:]
        return filter_str

    def filter_all(self, s):
        pos_list = list()
        ss = DFA.draw_words(s, pos_list)
        illegal_pos = self.find_illegal(ss)
        while illegal_pos != -1:
            ss = self.filter_words(ss, illegal_pos)
            illegal_pos = self.find_illegal(ss)
        i = 0
        while i < len(ss):
            if ss[i] == '喵':
                start = pos_list[i]
                while i < len(ss) and ss[i] == '喵':
                    i += 1
                i -= 1
                end = pos_list[i]
                num = end - start + 1
                s = s[:start] + '喵' * num + s[end + 1:]
            i += 1
        return s

    @staticmethod
    def draw_words(_str, pos_list):
        ss = str()
        for i in range(len(_str)):
            if '\u4e00' <= _str[i] <= '\u9fa5' or '\u3400' <= _str[i] <= '\u4db5' or '\u0030' <= _str[i] <= '\u0039' \
                    or '\u0061' <= _str[i] <= '\u007a' or '\u0041' <= _str[i] <= '\u005a':
                ss += _str[i]
                pos_list.append(i)
        return ss


