# -*- coding: utf-8 -*-
# @Time    : 12/8/22 12:07 PM
# @FileName: prompt_cutter.py
# @Software: PyCharm
# @Github    ：sudoskys
from openai_async import Chat

import uvicorn
from fastapi import FastAPI, Depends, status, HTTPException
from pydantic import BaseModel

CutParent = Chat.Chatbot(api_key="none", conversation_id="none")
app = FastAPI()


class Item(BaseModel):
    prompt_list: list = []
    prompt_str: str = ""
    prompt_type: list = []


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/prompt/cut")
async def create_item(item: Item):
    if not any(item.dict().keys()):
        return {"code": 404, "data": "", "msg": "没有数据"}
    prompt = item.prompt_str
    if item.prompt_str:
        item.prompt_list = CutParent.str_prompt(item.prompt_str)
    try:
        prompt = CutParent.cutter(item.prompt_list)
    except Exception as e:
        code = 400
        msg = "failed"
    else:
        code = 200
        msg = "success"
    return {"code": code, "data": prompt, "msg": msg}


if __name__ == '__main__':
    uvicorn.run('case_server:app', host='127.0.0.1', port=9556, reload=True, log_level="debug", workers=1)
