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
import llm_kira
from fastapi.responses import Response
from llm_kira.client import Optimizer
from llm_kira.client.llms import OpenAiParam
from pydantic import BaseModel
from App.Event import ContentDfa, TTSSupportCheck
from utils.Data import Service_Data, Openai_Api_Key, DefaultData, DictUpdate
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

llm_kira.setting.redisSetting = llm_kira.setting.RedisConfig(**_redis_conf)
OPENAI_API_KEY_MANAGER = Openai_Api_Key(filePath="./Config/api_keys.json")


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
            _Moderation_rep = await llm_kira.openai.Moderations(api_key=OPENAI_API_KEY_MANAGER.get_key()).create(
                input=check.prompt)
            _moderation_result = _Moderation_rep["results"][0]
            _harm_result = [key for key, value in _moderation_result["categories"].items() if value == True]
        except Exception as e:
            logger.error(f"Moderation:{check.prompt}-{e}")
    return FilterReply(dfa=ContentDfa.filter_all(check.prompt), flagged=_harm_result)


@app.post("/getreply")
async def get_reply(req: Prompt):
    conversation = llm_kira.client.Conversation(
        start_name=req.start_sequ,
        restart_name=req.restart_sequ,
        conversation_id=int(req.cid),
    )
    promptManager = llm_kira.client.PromptManager(profile=conversation, connect_words="\n")
    try:
        Mem = llm_kira.client.MemoryManager(profile=conversation)
        llm = llm_kira.client.llms.OpenAi(
            profile=conversation,
            api_key=OPENAI_API_KEY_MANAGER.get_key(),
            call_func=OPENAI_API_KEY_MANAGER.check_api_key,
            token_limit=3780,
            auto_penalty=not _csonfig["auto_adjust"],
        )
        chat_client = llm_kira.client.ChatBot(profile=conversation,
                                              memory_manger=Mem,
                                              optimizer=Optimizer.SinglePoint,
                                              llm_model=llm)
        response = await chat_client.predict(
            llm_param=OpenAiParam(model_name="text-davinci-003"),
            prompt=promptManager,
            predict_tokens=int(_csonfig["token_limit"]),
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
