# -*- coding: utf-8 -*-
# @Time    : 1/16/23 3:33 PM
# @FileName: spark.py
# @Software: PyCharm
# @Github    ：sudoskys
import json
import pathlib
import tempfile

import pycorrector
from loguru import logger
import model.recognize as Recognize
import model.spark as Spark
import model.utils.data as data
import model.chat as Chat
from playsound import playsound


# IO
def load_config():
    global _assistant_config
    now_table = data.DefaultAssistants.defaultConfig()
    if pathlib.Path("../Config/assistants.json").exists():
        with open("../Config/assistants.json", encoding="utf-8") as f:
            _assistant_config = json.load(f)
    else:
        _assistant_config = {}
    data.DictUpdate.dict_update(now_table, _assistant_config)
    _assistant_config = now_table
    return _assistant_config


def save_csonfig(pLock=None):
    if pLock:
        pLock.acquire()
    with open("../Config/config.json", "w+", encoding="utf8") as f:
        json.dump(_assistant_config, f, indent=4, ensure_ascii=False)
    if pLock:
        pLock.release()


load_config()

TRIGGER_KEY = _assistant_config["rec"]["porcupine"]["key"]

STT_CONFIG = _assistant_config["sst"]
STT_METHOD = STT_CONFIG["select"]
STT_LANG = STT_CONFIG["lang"]
STT_KEY = STT_CONFIG["server"][STT_METHOD][0]
if STT_LANG not in ["ja", "zh", "JA", "ZH"]:
    logger.warning("TTS MAY UNSUPPORTED WHEN YOU USE Vits")

PROMPT_CONFIG = _assistant_config["prompt"]
PROMPT_CONFIG: dict
assert isinstance(PROMPT_CONFIG, dict), "PROMPT_CONFIG MUST DICT"

CID = _assistant_config["userid"]

CHAT_CONFIG = _assistant_config["chat"]
GPT_SERVER = CHAT_CONFIG["gpt_server"]


def think_loop():
    prompt = Recognize.Wake(method=STT_METHOD,
                            lang=STT_LANG,
                            api_key=STT_KEY)
    prompt = pycorrector.traditional2simplified(prompt)
    logger.info(f"Input:{prompt}")
    if len(prompt) < 5:
        prompt.strip("?").strip("？")
    _req_table = PROMPT_CONFIG.copy()
    _req_table.update({
        "cid": CID,
        "prompt": prompt,
    })
    _prompt = Chat.Prompt(**_req_table)
    _reply = Chat.Req().gpt(prompt=_prompt, server=GPT_SERVER)
    if not _reply.get("status") or not _reply.get('response'):
        logger.warning(f"NO REPLY:{_reply.get('response')}")
    reply = _reply['response']["choices"][0]["text"]
    logger.info(f"Output:{reply}")

    _tts = Chat.TTS().create(text=reply, server=GPT_SERVER, cid=CID)
    if not _tts.status_code == 200:
        logger.warning(f"NO TTS:{_tts.status_code}")
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(_tts.content)
            f.flush()
            playsound(f.name)


Spark.trigger(access_key=TRIGGER_KEY,
              callback_func=think_loop
              )
