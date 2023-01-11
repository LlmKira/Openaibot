# -*- coding: utf-8 -*-
# @Time    : 1/11/23 1:34 PM
# @FileName: lang.py
# @Software: PyCharm
# @Github    ：sudoskys
import pycorrector

traditional_sentence = '忧郁的乌龟asdasd憂郁的烏龜'
simplified_sentence = pycorrector.traditional2simplified(traditional_sentence)
print(traditional_sentence, '=>', simplified_sentence)

simplified_sentence = '忧郁的乌龟'
traditional_sentence = pycorrector.simplified2traditional(simplified_sentence)
print(simplified_sentence, '=>', traditional_sentence)
