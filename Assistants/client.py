# -*- coding: utf-8 -*-
# @Time    : 1/16/23 3:33 PM
# @FileName: spark.py
# @Software: PyCharm
# @Github    ：sudoskys
import time
import json
import pathlib
import tempfile

import pycorrector

import model.chat as chat
import model.spark as spark
import model.utils.data as data
from playsound import playsound
import model.recognize as recognize

from loguru import logger


# IO
def load_config(path: str = "../Config/assistants.json"):
    global _assistant_config
    now_table = data.DefaultAssistants.defaultConfig()
    if pathlib.Path(path).exists():
        with open(path, encoding="utf-8") as f:
            _assistant_config = json.load(f)
    else:
        _assistant_config = {}
    data.DictUpdate.dict_update(now_table, _assistant_config)
    _assistant_config = now_table
    return _assistant_config


def save_csonfig(path: str = "../Config/config.json", pLock=None):
    if pLock:
        pLock.acquire()
    with open(path, "w+", encoding="utf8") as f:
        json.dump(_assistant_config, f, indent=4, ensure_ascii=False)
    if pLock:
        pLock.release()


load_config(path="../Config/assistants.json")

TRIGGER_KEY = _assistant_config["rec"]["porcupine"]["key"]

STT_CONFIG = _assistant_config["sst"]
STT_METHOD = STT_CONFIG["select"]
STT_LANG = STT_CONFIG["lang"]
STT_SELECT_CONFIG = STT_CONFIG[STT_METHOD]
if STT_LANG not in ["ja", "zh", "JA", "ZH"]:
    logger.warning("TTS MAY UNSUPPORTED WHEN YOU USE Vits")

PROMPT_CONFIG = _assistant_config["prompt"]
PROMPT_CONFIG: dict
assert isinstance(PROMPT_CONFIG, dict), "PROMPT_CONFIG MUST DICT"

CID = _assistant_config["userid"]

CHAT_CONFIG = _assistant_config["chat"]
GPT_SERVER = CHAT_CONFIG["gpt_server"]
SAVE_SOUND = _assistant_config["sound"]["save"]
SOUND_DIR = _assistant_config["sound"]["dir"]

pathlib.Path(SOUND_DIR).mkdir(exist_ok=True)


def think_loop():
    prompt = recognize.Wake(method=STT_METHOD,
                            lang=STT_LANG,
                            config=STT_SELECT_CONFIG)
    prompt = pycorrector.traditional2simplified(prompt)
    logger.info(f"Input:{prompt}")
    if len(prompt) < 5:
        prompt.strip("?").strip("？")
    _req_table = PROMPT_CONFIG.copy()
    _req_table.update({
        "cid": CID,
        "prompt": prompt,
    })
    _prompt = chat.Prompt(**_req_table)
    _reply = chat.Req().gpt(prompt=_prompt, server=GPT_SERVER)
    if not _reply:
        logger.warning(f"NO REPLY")
        return
    reply = _reply['response']["choices"][0]["text"]
    logger.info(f"Output:{reply}")

    _tts = chat.TTS().create(text=reply, server=GPT_SERVER, cid=CID)
    if not _tts:
        logger.warning(f"NO TTS")
    else:
        if SAVE_SOUND:
            _name = str(time.strftime("%Y%m%d_%H%M%S", time.localtime()))
            with pathlib.Path(f"{SOUND_DIR}/{_name}.ogg").open("wb+") as f:
                f.write(_tts.content)
                f.flush()
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(_tts.content)
            f.flush()
            playsound(f.name)


spark.trigger(access_key=TRIGGER_KEY,
              callback_func=think_loop
              )
