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
from fastapi.responses import Response
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
    start_sequ: str = "Human"  # 你的名字
    restart_sequ: str = "Neko"  # Ai 的名字
    prompt: str
    role: str = ""  # Ai 的自我认同
    character: list = None  # Ai 的性格
    head: str = ""  # 对话的场景定位
    model: str = "text-davinci-003"  # 模型


class Filter(BaseModel):
    prompt: str
    moderation: bool = True


class Reply(BaseModel):
    status: bool
    data: Optional[bytes] = None
    response: Optional[dict] = None


class FilterReply(BaseModel):
    dfa: str
    flagged: list


@app.post("/filter")
async def filter_str(check: Filter):
    # 内容审计
    _harm_result = []
    if check.moderation:
        try:
            _Moderation_rep = await openai_kira.Moderations().create(input=check.prompt)
            _moderation_result = _Moderation_rep["results"][0]
            _harm_result = [key for key, value in _moderation_result["categories"].items() if value == True]
        except Exception as e:
            logger.error(f"Moderation:{check.prompt}-{e}")
    return FilterReply(dfa=ContentDfa.filter_all(check.prompt), flagged=_harm_result)


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
        response = await receiver.get_chat_response(model=req.model,
                                                    prompt=str(req.prompt),
                                                    max_tokens=int(_csonfig["token_limit"]),
                                                    role=req.role,
                                                    web_enhance_server=_plugin_table,
                                                    optimizer=None,
                                                    no_penalty=not _csonfig["auto_adjust"],
                                                    character=req.character,
                                                    head=req.head,
                                                    )
        _got = Reply(status=True, response=response)
    except Exception as e:
        logger.error(e)
        return Reply(status=False)
    else:
        return _got


@app.get("/getvoice")
async def get_voice(text: str, cid: int):
    try:
        _req = await TTSSupportCheck(text=text, user_id=cid)
    except Exception as e:
        logger.error(e)
        return Response(status_code=417)
    else:
        status = False
        if _req:
            status = True
        if status:
            import base64
            httpRes = Response(content=_req, media_type='audio/ogg')
            httpRes.headers['X-Bot-Reply'] = str(base64.b64encode(text.encode('utf-8')), 'utf-8')
            return httpRes
        return Response(status_code=417)
