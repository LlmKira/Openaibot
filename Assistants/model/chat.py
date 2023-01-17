# -*- coding: utf-8 -*-
# @Time    : 1/16/23 8:09 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys
import httpx
from pydantic import BaseModel


class Prompt(BaseModel):
    cid: int
    start_sequ: str = "Human"  # 你的名字
    restart_sequ: str = "Neko"  # Ai 的名字
    prompt: str
    role: str = ""  # Ai 的自我认同
    character: list = None  # Ai 的性格
    head: str = ""  # 对话的场景定位
    model: str = "text-davinci-003"  # 模型


class Req(object):
    def gpt(self, prompt: Prompt, server: str = "http://127.0.0.1:9559"):
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        req = httpx.post(f"{server}/getreply", json=prompt.dict(), headers=headers, timeout=30)
        req.raise_for_status()
        return req.json()


class TTS(object):
    def create(self, text: str, cid: int, server: str = "http://127.0.0.1:9559"):
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        req = httpx.get(f"{server}/getvoice?text={text}&cid={cid}", headers=headers, timeout=30)
        return req
