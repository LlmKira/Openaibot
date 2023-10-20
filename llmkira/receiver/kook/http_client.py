# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午5:33
# @Author  : sudoskys
# @File    : http_client.py
# @Software: PyCharm
import requests


class KookHttpClient(object):
    def __init__(self, token):
        self.base_url = 'https://www.kookapp.cn'
        self.bot_token = token

    def request(self, method, url, data=None):
        headers = {
            'Authorization': f'Bot {self.bot_token}'
        }
        response = requests.request(method, f'{self.base_url}{url}', headers=headers, json=data)
        return response.json()

    def create_channel_message(self, target_id, content, quote=None):
        data = {
            'type': 1,
            'target_id': target_id,
            'content': content,
            'quote': quote
        }
        return self.request('POST', '/api/v3/message/create', data)

    def create_direct_message(self, target_id, content, quote=None):
        data = {
            'type': 1,
            'target_id': target_id,
            'content': content,
            'quote': quote
        }
        return self.request('POST', '/api/v3/direct-message/create', data)
