# -*- coding: utf-8 -*-
# @Time    : 2023/8/24 下午11:36
# @Author  : sudoskys
# @File    : duckduck.py
# @Software: PyCharm
from duckduckgo_search import DDGS

from llmkira.sdk import Sublimate

search = "评价一下刀郎的罗刹海市？"
key = ["刀郎"]

with DDGS(timeout=20) as ddgs:
    _text = []
    for r in ddgs.text(search):
        _title = r.get("title")
        _href = r.get("href")
        _body = r.get("body")
        _text.append(_body)
    print(_text)
    _test_result = Sublimate(_text).valuation(match_sentence=search, match_keywords=key)
    for key in _test_result:
        print(key)
