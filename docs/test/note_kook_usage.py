# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午2:02
# @Author  : sudoskys
# @File    : khl_2.py
# @Software: PyCharm
from khl import Bot, Message, api, HTTPRequester, Cert, MessageTypes

bot_token = "xxxx"
# init Bot
bot = Bot(token=bot_token)
# bot.client.create_asset(file="")


# register command, send `/hello` in channel to invoke
@bot.command(name='wss')
async def world(msg: Message):
    await msg.reply('world!')
    print(msg.author_id)
    # return
    print(msg.ctx.channel.id)
    print(await msg.ctx.channel.send("h"))
    await HTTPRequester(cert=Cert(token=bot_token)).exec_req(api.Message.create(
        target_id=msg.ctx.channel.id,
        type=MessageTypes.KMD.value,
        content='hello!',
        # temp_target_id=msg.author.id,
    )
    )


print('hello world')
# everything done, go ahead now!

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


# 示例用法
sdk = KookHttpClient(bot_token)
# sdk.create_channel_message('channel_id', 'Hello, KOOK!')
_res = sdk.create_direct_message('1564611098', 'Hey there!')
print(_res)
