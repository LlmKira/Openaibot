# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:00 PM
# @FileName: Apitest.py
# @Software: PyCharm
# @Github    ：sudoskys

# 最小单元测试
import openai
from utils.Base import ReadConfig

config = ReadConfig().parseFile("../Config/app.toml")
openai.api_key = config.bot.OPENAI_API_KEY
response = openai.Completion.create(model="text-davinci-003", prompt="Say this is a test", temperature=0,
                                    max_tokens=20)

# TEST
print(response)
print(type(response))
print(response.get("choise"))
print(response.get("choices"))
