# -*- coding: utf-8 -*-
# @Time    : 11/9/22 8:46 AM
# @FileName: DfaDetect.py
# @Software: PyCharm
# @Github    ：spirit-yzk
import base64
import httpx
import re
from utils import Setting
from utils.Base import StrListTool
import pycorrector


def get_start_name(prompt: str, bot_name=None):
    _code_symbol = ["class", "test", "debug", "_", ")", "(", "}", "{", "=", "Python", "lua", "nodejs", "rust", "code",
                    "补全", "代码", "数据包"]
    STARTNAME = bot_name if bot_name else "Girl:"
    STARTNAME = STARTNAME if not prompt.endswith(("?", "？")) else "Athene:"

    STARTNAME = STARTNAME if not StrListTool.isStrIn(prompt=prompt, keywords=_code_symbol, r=0.1) else "Engineer:"
    STARTNAME = STARTNAME if not StrListTool.isStrIn(prompt=prompt, keywords=["teach me", "教教我", "解释一下"],
                                                     r=0.01) else "Teacher:"
    STARTNAME = STARTNAME if not prompt.endswith(("!", "！")) else "Girl:"
    STARTNAME = STARTNAME if not prompt.endswith(("!!", "！！")) else "God:"
    STARTNAME = STARTNAME if not prompt.endswith("——") else "Cat:"
    STARTNAME = STARTNAME if not prompt.endswith(("...", "。。。")) else "Angel:"
    STARTNAME = STARTNAME if not prompt.endswith(("~", "～")) else "Neko:"
    return STARTNAME


def strToBase64(s):
    strEncode = base64.b64encode(s.encode('utf8'))
    return str(strEncode, encoding='utf8')


def base64ToStr(s):
    strDecode = base64.b64decode(bytes(s, encoding='utf8'))
    return str(strDecode, encoding='utf8')


class Cn(object):
    @staticmethod
    def is_chinese(word):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    @staticmethod
    def is_contain_chinese(check_str):
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False


class Censor:
    @staticmethod
    def initWords(url: dict, home_dir: str = "./", proxy=None):
        error = []
        for item in url:
            _Words = []
            _Item_url = url[item]
            for _url in _Item_url:
                try:
                    _url = str(base64.b64decode(_url), 'utf-8')
                except Exception:
                    _url = _url
                try:
                    response = httpx.get(_url, proxies=proxy)
                    # response.encoding = response.charset_encoding
                except Exception as e:
                    print(f"词库请求失败 -> {_url}")
                    error.append({e})
                else:
                    if response.status_code == 200:
                        tmpList = response.text.encode(response.encoding).decode('utf-8').split("\n")
                        for sid in tmpList:
                            censor_words = str(sid.strip(",").strip("\n"))
                            if censor_words and Cn.is_contain_chinese(censor_words) and len(censor_words) >= 2:
                                _Words.append(censor_words)
                    else:
                        print(f"词库初始化失败 -> {_url}")
                        error.append({_url})
            if _Words:
                with open(home_dir + item, "w+", encoding='utf-8') as code:
                    code.write("\n".join(list(set(_Words))))
                print(f"初始化写入 -> {item}-{len(_Words)}")
            else:
                print(f"写入了空白? -> {item}")
        return url.keys(), error


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
