# -*- coding: utf-8 -*-
# @Time    : 12/8/22 12:07 PM
# @FileName: prompt_cutter.py
# @Software: PyCharm
# @Github    ：sudoskys
from openai_async import Chat

import uvicorn
from fastapi import FastAPI, Depends, status, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    prompt: str
    history_list: list = []
    history_str: str = ""
    token_limit: int = 2500
    extra_token: int = 500
    restart_sequ: str = "\nAI:"
    start_sequ: str = "\nHuman:"


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/prompt/cut")
async def create_item(item: Item):
    limit = item.token_limit
    CutParent = Chat.Chatbot(api_key="none", conversation_id="none", token_limit=limit,
                             restart_sequ=item.restart_sequ, start_sequ=item.start_sequ)
    if not any(item.dict().keys()):
        return {"code": 404, "data": "", "msg": "没有数据"}
    prompt = item.history_str
    if item.history_str:
        item.history_list = CutParent.str_prompt(item.history_str)
    try:
        prompt = CutParent.Summer(prompt=item.prompt, extra_token=item.extra_token, chat_list=item.history_list)
    except Exception as e:
        code = 400
        msg = "failed"
        prompt = e
    else:
        code = 200
        msg = "success"
    return {"code": code, "data": prompt, "msg": msg}


if __name__ == '__main__':
    uvicorn.run('case_server:app', host='127.0.0.1', port=9556, reload=True, log_level="debug", workers=1)

"""
some = {
    "prompt": "某个元素",
    "history_list": [
        "我的软肋是看不透舍不得输不起放不下每个人都有自己的人生冷暖自知无论生活还是网络好象都是一场旅行前路漫漫不可能把所有的美丽与美景尽收眼底总有一些人和事会被自己遗忘在路上虽然有时我们并不想扔下这些曾经的美好 学会接受残缺是人生的成熟人无完人缺憾是人生的常态人生有成就有败有聚就有散没有谁能得天独厚一手遮天鱼和熊掌不可兼得不强求凡事尽人事随缘而安追求完美是美好的理想接受残缺是美好的心态",
        "Human:Using OpenAi's Aeve chatGPT func|在 Telegram ",
        "Human:Using OpenAi's Apihieve chatGPT func|在 Telegram ",
        "Human:Using OpenAi's Api hatGPT func|在 Telegram ",
        "Human:Using OpenAi's egram to achieve chatGPT func|在 Telegram ",
        "Human:Using OpenAi'sto achieve chatGPT func|在 Telegram ",
        "AI:Using OpenAi's Api on Telee chatGPT func|在 Telegram ",
        "Human:Using OpenAi'so achieve chatGPT func|在 Telegram ",
        "AI:在python中判断 list 中是否包含某个元素"],
    "history_str": "",
    "token_limit": 2000,
    "extra_token": 200,
    "restart_sequ": "\nAI:",
    "start_sequ": "\nHuman:"
}
"""
