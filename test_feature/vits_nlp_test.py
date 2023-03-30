# -*- coding: utf-8 -*-
# @Time    : 12/20/22 10:19 PM
# @FileName: vits_nlp.py
# @Software: PyCharm
# @Github    ：sudoskys
import time
from Component.langdetect_fasttext import detect

t1 = time.time()
result = detect(text="你好", low_memory=True)
print(result)
result = detect(text="你好你好,これから日本", low_memory=True)
print(result)
result = detect(text="0", low_memory=True)
print(result)
t2 = time.time()
print(t2 - t1)
