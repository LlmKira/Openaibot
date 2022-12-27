# -*- coding: utf-8 -*-
# @Time    : 12/20/22 10:19 PM
# @FileName: vits_nlp.py
# @Software: PyCharm
# @Github    ：sudoskys
import time

from openai_async.utils.Talk import Talk

res = Talk().cut_chinese_sentence(
    "これから日本...大家好，我是可莉，我建议大家不要有其它的营养，所以不能只看它的热量就作为应急食品来使用。")
print(res)
from fatlangdetect import detect

t1 = time.time()
result = detect(text="你好", low_memory=True)
print(result)
result = detect(text="你好你好,これから日本", low_memory=True)
print(result)
result = detect(text="怎麼不給爺嘿嘿呢", low_memory=True)
print(result)
t2 = time.time()
print(t2 - t1)
