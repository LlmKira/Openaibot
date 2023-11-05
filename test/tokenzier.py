# -*- coding: utf-8 -*-
# @Time    : 2023/11/5 下午9:56
# @Author  : sudoskys
# @File    : tokenzier.py
# @Software: PyCharm

len([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
some = tokenizer("你好", return_tensors="pt")
print(some)

