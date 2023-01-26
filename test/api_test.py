# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:00 PM
# @FileName: Apitest.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio

# 最小单元测试
import llm_kira
from utils.Data import Openai_Api_Key

llm_kira.setting.openaiApiKey = Openai_Api_Key(filePath="../Config/api_keys.json").get_key()

print(openai_kira.setting.openaiApiKey)


async def main():
    response = await openai_kira.Completion().create(model="text-davinci-003",
                                                     prompt="Say this is a test",
                                                     temperature=0,
                                                     max_tokens=20)
    # TEST
    print(response)
    print(type(response))


asyncio.run(main())
