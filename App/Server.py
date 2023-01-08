# -*- coding: utf-8 -*-
# @Time    : 1/5/23 6:58 PM
# @FileName: LumiServer.py
# @Software: PyCharm
# @Github    ：sudoskys
# app.py

import json
import pathlib
from typing import Optional

from fastapi import FastAPI
import openai_kira
from pydantic import BaseModel
from App.Event import ContentDfa, TTSSupportCheck
from utils.Data import Service_Data, Api_keys, DefaultData, DictUpdate
from loguru import logger

_service = Service_Data.get_key()
_redis_conf = _service["redis"]
_tts_conf = _service["tts"]
_plugin_table = _service["plugin"]
global _csonfig

app = FastAPI()


# IO
def load_csonfig():
    global _csonfig
    now_table = DefaultData.defaultConfig()
    if pathlib.Path("./Config/config.json").exists():
        with open("./Config/config.json", encoding="utf-8") as f:
            _csonfig = json.load(f)
    else:
        _csonfig = {}
    DictUpdate.dict_update(now_table, _csonfig)
    _csonfig = now_table
    return _csonfig


load_csonfig()

openai_kira.setting.redisSetting = openai_kira.setting.RedisConfig(**_redis_conf)
openai_kira.setting.openaiApiKey = Api_keys.get_key("./Config/api_keys.json")["OPENAI_API_KEY"]


class Prompt(BaseModel):
    cid: int
    start_sequ: str = "Neko:"
    restart_sequ: str = "Human:"
    prompt: str
    role: str = ""


class Reply(BaseModel):
    status: bool
    data: Optional[bytes] = None
    response: Optional[dict] = None


@app.post("/filter")
def filter_str(strs):
    return ContentDfa.filter_all(strs)


@app.post("/getreply")
async def get_reply(req: Prompt):
    receiver = openai_kira.Chat.Chatbot(
        conversation_id=req.cid,
        call_func=Api_keys.pop_api_key,
        token_limit=3751,
        start_sequ=req.start_sequ,
        restart_sequ=req.restart_sequ,
    )
    try:
        response = await receiver.get_chat_response(model="text-davinci-003",
                                                    prompt=str(req.prompt),
                                                    max_tokens=int(_csonfig["token_limit"]),
                                                    role=req.role,
                                                    web_enhance_server=_plugin_table
                                                    )
        _got = Reply(status=True, response=response)
    except Exception as e:
        logger.error(e)
        return Reply(status=False)
    else:
        return _got


@app.post("/getvoice")
async def get_voice(text: str, cid: int):
    try:
        _req = await TTSSupportCheck(text=text, user_id=cid)
    except Exception as e:
        logger.error(e)
        return Reply(status=False)
    else:
        status = False
        if _req:
            status = True
        return Reply(status=status, data=_req)
