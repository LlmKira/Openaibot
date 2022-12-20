# -*- coding: utf-8 -*-
# @Time    : 12/20/22 10:51 AM
# @FileName: network.py
# @Software: PyCharm
# @Github    ：sudoskys

import httpx


class MakeRequest(object):
    def __init__(self):
        self.client = httpx.AsyncClient()

    def send(self):
        self.client.get('https://www.example.com/')
