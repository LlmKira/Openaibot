# -*- coding: utf-8 -*-
# @Time    : 12/20/22 10:19 PM
# @FileName: vits_nlp.py
# @Software: PyCharm
# @Github    ：sudoskys
from openai_async.utils.Talk import Talk

res = Talk.chinese_sentence_cut("大家好，我是可莉，我建议大家不要将莲子粥作为应急食品，它应该属于每天的饮食中的一部分，但不是应急食品。因为莲子粥的热量确实相对比较低，但它也含有其它的营养，所以不能只看它的热量就作为应急食品来使用。")

print(res)
