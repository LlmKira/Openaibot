# -*- coding: utf-8 -*-
# @Time    : 2/5/23 1:59 PM
# @FileName: blip_server_test.py
# @Software: PyCharm
# @Github    ：sudoskys
import asyncio

from utils.Blip import BlipServer


async def main():
    res = await BlipServer(api="http://127.0.0.1:10885/upload/").generate_caption(image_file="test.jpg")
    print(res)


asyncio.run(main())
