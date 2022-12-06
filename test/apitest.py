# -*- coding: utf-8 -*-
# @Time    : 12/5/22 10:23 PM
# @FileName: apitest.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio

import openai_sync
from utils.Base import ReadConfig

config = ReadConfig().parseFile("../Config/app.toml")
click = openai_sync.Completion(api_key=config.bot.OPENAI_API_KEY)


async def test_api():
    return await click.create(model="text-davinci-003", prompt="Say this is a test", temperature=0,
                              max_tokens=20, user="001")


response = asyncio.run(test_api())
# TEST
print(response)
