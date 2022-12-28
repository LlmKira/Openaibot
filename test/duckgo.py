# -*- coding: utf-8 -*-
# @Time    : 12/28/22 4:35 PM
# @FileName: duckgo.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio
from duckpy import AsyncClient

client = AsyncClient()


async def get_results():
    results = await client.search("Python Wikipedia")

    # Prints first result title
    print(results[0].title)

    # Prints first result URL
    print(results[0].url)

    # Prints first result description
    print(results[0].description)


asyncio.run(get_results())

