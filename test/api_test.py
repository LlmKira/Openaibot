# -*- coding: utf-8 -*-
# @Time    : 12/5/22 5:00 PM
# @FileName: Apitest.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio

# 最小单元测试
import openai_async
from utils.Data import Api_keys

openai_async.api_key = Api_keys.get_key("../Config/api_keys.json")["OPENAI_API_KEY"]

print(openai_async.api_key)


async def main():
    response = await openai_async.Completion().create(model="text-davinci-003",
                                                      prompt="Say this is a test",
                                                      temperature=0,
                                                      max_tokens=20)
    # TEST
    print(response)
    print(type(response))


asyncio.run(main())
