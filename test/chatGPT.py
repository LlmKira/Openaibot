# -*- coding: utf-8 -*-
# @Time    : 12/6/22 10:50 AM
# @FileName: chatGPT.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio

from App.chatGPT import PrivateChat


async def test_api():
    return await PrivateChat.load_response(user=100, group=100)


response = asyncio.run(test_api())
# TEST
print(response)

