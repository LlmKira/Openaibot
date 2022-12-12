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
    memory_list: list = []
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
    try:
        prompt = CutParent.Summer(prompt=item.prompt, extra_token=item.extra_token, memory=item.memory_list)
    except Exception as e:
        code = 400
        msg = "failed"
        prompt = e
    else:
        code = 200
        msg = "success"
    return {"code": code, "data": prompt, "msg": msg}


if __name__ == '__main__':
    uvicorn.run('prompt_server:app', host='127.0.0.1', port=9556, reload=True, log_level="debug", workers=1)

"""
some = {
    "prompt": "某个元素",
    "memory_list": [
    {"ask": "YOU:nihao", "reply": "ME:youtoo"},
     {"ask": "YOU:nihao", "reply": "ME:youtoo"}
    ]
    "history_str": "",
    "token_limit": 2000,
    "extra_token": 200,
    "restart_sequ": "\nAI:",
    "start_sequ": "\nHuman:"
}

# 非标准格式会被去除
"""
