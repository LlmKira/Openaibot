# -*- coding: utf-8 -*-
# @Time    : 12/17/22 10:50 AM
# @FileName: playground.py
# @Software: PyCharm
# @Github    ：sudoskys
import re

prompt = "你好 [1][niah]"
match = re.findall(r"\[(.*?)\]", prompt)
match2 = re.findall(r"\"(.*?)\"", prompt)
match.extend(match2)
print(match)
if match:
    prompt = match[0]
