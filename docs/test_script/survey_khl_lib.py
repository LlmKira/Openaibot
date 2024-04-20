# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 下午1:26
# @Author  : sudoskys
# @File    : khl.py
# @Software: PyCharm
import asyncio

from khl import Bot, api, HTTPRequester, Cert, MessageTypes

# import nest_asyncio
# nest_asyncio.apply()

bot_token = "xxx"
# init Bot
bot = Bot(cert=Cert(token=bot_token))


# register command, send `/hello` in channel to invoke
async def world():
    httpr = HTTPRequester(cert=Cert(token=bot_token))
    _request = await httpr.exec_req(
        api.DirectMessage.create(
            target_id="15648861098",  # :)
            type=9,
            content="hello23",
            # temp_target_id=msg.author.id,
        )
    )
    _request = await httpr.exec_req(
        api.DirectMessage.create(
            target_id="15648861098",
            type=9,
            content="hello232342",
            # temp_target_id=msg.author.id,
        )
    )
    # return
    await bot.client.gate.exec_req(
        api.DirectMessage.create(
            target_id="15648861098",
            content="hello!---",
            type=9,
        )
    )
    # return
    msg = None
    await bot.client.send(target=msg.ctx.channel, content="hello")
    # return
    print(msg.ctx.channel.id)
    print(await msg.ctx.channel.send("h"))
    await HTTPRequester(cert=Cert(token=bot_token)).exec_req(
        api.Message.create(
            target_id=msg.ctx.channel.id,
            type=MessageTypes.KMD.value,
            content="hello!",
            # temp_target_id=msg.author.id,
        )
    )


print("hello world")
loop = asyncio.get_event_loop()
loop.run_until_complete(world())
