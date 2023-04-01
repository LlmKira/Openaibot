# -*- coding: utf-8 -*-
# @Time    : 2023/4/1 下午1:54
# @Author  : sudoskys
# @File    : file.py
# @Software: PyCharm
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor


class FileClientWrapper:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.file_path = None

    def read_json(self, file_path):
        self.file_path = file_path
        with open(file_path) as f:
            data = json.load(f)
        return data

    def write_json(self, file_path, data):
        self.file_path = file_path
        with open(file_path, 'w+') as f:
            json.dump(data, f)

    async def async_read_json(self, file_path):
        async with self.lock:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(self.executor, self.read_json, file_path)
        return data

    async def async_write_json(self, file_path, data):
        async with self.lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self.write_json, file_path, data)


file_client = FileClientWrapper()
