# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Event.py
# @Software: PyCharm
# @Github: sudoskys

import json
import math
import random
import pathlib
import asyncio
import re
import time

# from io import BytesIO
from typing import Union, Tuple

from loguru import logger

# from App.chatGPT import PrivateChat
from utils.Chat import Utils, Usage, GroupManager, UserManager, Header, Style, ConfigUtils
from utils.Data import DictUpdate, DefaultData, Openai_Api_Key, Service_Data, User_Message, PublicReturn, ProxyConfig
from utils.Setting import ProfileReturn
from utils.TTS import TTS_Clint, TTS_REQ
from utils.Detect import DFA, Censor, Detect
from utils.Logging import LoadResponseError

import llm_kira
from llm_kira.utils.chat import Cut
from llm_kira.client.types import PromptItem
from llm_kira.client.llms.openai import OpenAiParam
from llm_kira.client import Optimizer, Conversation
from llm_kira.client.llms.base import LlmBase
from llm_kira.creator.think import ThinkEngine, Hook
from llm_kira.creator.engine import PromptEngine
from llm_kira.error import RateLimitError, ServiceUnavailableError, AuthenticationError, LLMException
from llm_kira.radio.anchor import DuckgoCraw, SearchCraw

OPENAI_API_KEY_MANAGER = Openai_Api_Key(filePath="./Config/api_keys.json")

# fast text langdetect_kira

_service = Service_Data.get_key()
REDIS_CONF = _service["redis"]
TTS_CONF = _service["tts"]
PLUGIN_TABLE = _service["plugin"]
# End
PLUGIN_TABLE.pop("search", None)
PLUGIN_TABLE.pop("duckgo", None)

PROXY_CONF = ProxyConfig(**_service["proxy"])
HARM_TYPE = _service["moderation_type"]
HARM_TYPE = list(set(HARM_TYPE))

# Backend
BACKEND_CONF = _service["backend"]
CHAT_OPTIMIZER = Optimizer.SinglePoint

# Limit
if not BACKEND_CONF.get("type"):
    logger.warning("Model Type Not Set:Service.json")

# Proxy
if PROXY_CONF.status:
    llm_kira.setting.proxyUrl = PROXY_CONF.url

CHATGPT_CONF = BACKEND_CONF.get("chatgpt")
OPENAI_CONF = BACKEND_CONF.get("openai")

global LLM_TYPE
global LLM_MODEL_PARAM
global MODEL_TOKEN_LIMIT
global LLM_CLIENT
MODEL_TOKEN_LIMIT = OPENAI_CONF.get("token_limit") if OPENAI_CONF.get("token_limit") else 3000


def CreateLLM():
    global LLM_TYPE
    global LLM_MODEL_PARAM
    global MODEL_TOKEN_LIMIT
    global LLM_CLIENT
    if BACKEND_CONF.get("type") == "openai":
        logger.info("Using Openai Api")
        MODEL_NAME = OPENAI_CONF.get("model")
        MODEL_TOKEN_LIMIT = OPENAI_CONF.get("token_limit") if OPENAI_CONF.get("token_limit") else 3000
        LLM_MODEL_PARAM = llm_kira.client.llms.OpenAiParam(model_name=MODEL_NAME)
        LLM_CLIENT = llm_kira.client.llms.OpenAi
    elif BACKEND_CONF.get("type") == "chatgpt":
        logger.info("Using ChatGPT Server")
        MODEL_NAME = CHATGPT_CONF.get("model")
        MODEL_TOKEN_LIMIT = CHATGPT_CONF.get("token_limit") if CHATGPT_CONF.get("token_limit") else 3000
        LLM_MODEL_PARAM = llm_kira.client.llms.ChatGptParam(model_name=MODEL_NAME)
        LLM_CLIENT = llm_kira.client.llms.ChatGpt


CreateLLM()

llm_kira.setting.redisSetting = llm_kira.setting.RedisConfig(**REDIS_CONF)
llm_kira.setting.llmRetryTime = 2
llm_kira.setting.llmRetryTimeMax = 30
llm_kira.setting.llmRetryTimeMin = 3
llm_kira.setting.llmRetryAttempt = 2

urlForm = {
    "Danger.form": [
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2Z3d2RuL3NlbnNpdGl2ZS1zdG9wLXdvcmRzL21hc3Rlci8lRTYlOTQlQkYlRTYlQjIlQkIlRTclQjElQkIudHh0",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL1RlbGVjaGFCb3QvQW50aVNwYW0vbWFpbi9EYW5nZXIudHh0",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FkbGVyZWQvRGFuZ2Vyb3VzU3BhbVdvcmRzL21hc3Rlci9EYW5nZXJvdXNTcGFtV29yZHMvR2VuZXJhbF9TcGFtV29yZHNfVjEuMC4xX0NOLm1pbi50eHQ=",
        # 腾讯词库
        # "aHR0cHM6Ly9naXRodWIuY29tL2NqaDA2MTMvdGVuY2VudC1zZW5zaXRpdmUtd29yZHMvYmxvYi9tYWluL3NlbnNpdGl2ZV93b3Jkc19saW5lcy50eHQ=",
        # 国家 + 政党 + 人种
        # "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FkbGVyZWQvRGFuZ2Vyb3VzU3BhbVdvcmRzL21hc3Rlci9EYW5nZXJvdXNTcGFtV29yZHMvR2VuZXJhbF9TcGFtV29yZHNfVjEuMC4xX0NOLm1pbi50eHQ=",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0phaW1pbjEzMDQvc2Vuc2l0aXZlLXdvcmQtZGV0ZWN0b3IvbWFpbi9zYW1wbGVfZmlsZXMvc2FtcGxlX2Jhbm5lZF93b3Jkcy50eHQ=",
    ]
}


def initCensor():
    if PROXY_CONF.status:
        proxies = {
            'all://': PROXY_CONF.url,
        }  # 'http://127.0.0.1:7890'  # url
        return Censor.initWords(url=urlForm, home_dir="./Data/", proxy=proxies)
    else:
        return Censor.initWords(url=urlForm, home_dir="./Data/")


if not pathlib.Path("./Data/Danger.form").exists():
    initCensor()
# 过滤器
ContentDfa = DFA(path="./Data/Danger.form")

global _csonfig


# IO
def load_csonfig():
    global _csonfig
    now_table = DefaultData.defaultConfig()
    _csonfig = ConfigUtils.getKey("config")
    DictUpdate.dict_update(now_table, _csonfig)
    _csonfig = now_table
    return _csonfig


def save_csonfig():
    ConfigUtils.setKey("config", _csonfig)


try:
    ConfigUtils.getKey("config")
except Exception as e:
    logger.error(f"U Should Config Redis First")
    exit(1)

# Init
if not ConfigUtils.getKey("config"):
    if pathlib.Path("./Config/config.json").exists():
        with open("./Config/config.json", encoding="utf-8") as f:
            _csonfig = json.load(f)
        save_csonfig()


async def TTSSupportCheck(text, user_id, limit: bool = True):
    global TTS_CONF
    """
    处理消息文本并构造请求返回字节流或者空
    :return:
    """
    if not TTS_CONF["status"]:
        return
    if TTS_CONF['type'] == 'none':
        return

    try:
        from fatlangdetect import detect
        lang_type = detect(text=text.replace("\n", "").replace("\r", ""), low_memory=True).get("lang").upper()
    except Exception as e:
        from langdetect_kira import detect
        lang_type = detect(text=text.replace("\n", "").replace("\r", ""))[0][0].upper()

    if TTS_CONF["type"] == "vits":
        _vits_config = TTS_CONF["vits"]
        if lang_type not in ["ZH", "JA"]:
            return
        if len(text) > _vits_config["limit"] and limit:
            return
        cn_res = Cut.chinese_sentence_cut(text)
        cn = {i: f"[{lang_type}]" for i in cn_res}
        # 合成
        _spell = [f"{cn[x]}{x}{cn[x]}" for x in cn.keys()]
        _new_text = "".join(_spell)
        _new_text = "[LENGTH]1.4[LENGTH]" + _new_text
        # 接受数据
        result, _error = await TTS_Clint.request_vits_server(
            url=_vits_config["api"],
            params=TTS_REQ(task_id=user_id,
                           text=_new_text,
                           model_name=_vits_config["model_name"],
                           speaker_id=_vits_config["speaker_id"],
                           audio_type="ogg"
                           )
        )
        if not result:
            logger.error(f"TTS:{user_id} --type:vits --content: {text}:{len(text)} --{_error}")
            return
        logger.info(f"TTS:{user_id} --type:vits --content: {text}:{len(text)}")
        # 返回字节流
        return result
    # USE AZURE
    elif TTS_CONF["type"] == "azure":
        _azure_config = TTS_CONF["azure"]
        _new_text = text
        _speaker = _azure_config["speaker"].get(lang_type)
        if len(text) > _azure_config["limit"]:
            return
        if not _speaker:
            logger.info(f"TTS:{user_id} --type:azure --content: {text}:{len(text)} --this type lang not supported")
            return
        result, _error = await TTS_Clint.request_azure_server(
            key=_azure_config["key"],
            location=_azure_config["location"],
            text=_new_text,
            speaker=_speaker
        )
        if not result:
            logger.error(f"TTS:{user_id} --type:azure --content: {text}:{len(text)} --{_error}")
            return

        logger.info(f"TTS:{user_id} --type:azure --content: {text}:{len(text)}")
        # 返回字节流
        return result
    else:
        return


async def Forget(user_id: int, chat_id: int):
    """
    重置消息流
    :param chat_id:
    :param user_id:
    :return:
    """
    receiver = llm_kira.client
    _cid = DefaultData.composing_uid(user_id=user_id, chat_id=chat_id)
    conversation = receiver.Conversation(
        start_name="start_name",
        restart_name="restart_name",
        conversation_id=int(_cid),
    )
    # conversation.hash_secret = str(int(time.time()))
    mem = receiver.MemoryManager(profile=conversation)
    return mem.reset_chat()


class Reply(object):
    def __init__(self, user, group, api_key=None):
        # 用量检测
        self.user = user
        self.group = group
        self.api_key = api_key
        self._UsageManager = Usage(uid=self.user)

    async def openai_moderation(self, prompt: str) -> bool:
        if not self.api_key:
            return False
        # 内容审计
        try:
            _harm = False
            if HARM_TYPE:
                _Moderation_rep = await llm_kira.openai.Moderations(api_key=self.api_key).create(
                    input=str(prompt))
                _moderation_result = _Moderation_rep["results"][0]
                _harm_result = [key for key, value in _moderation_result["categories"].items() if value == True]
                for item in _harm_result:
                    if item in HARM_TYPE:
                        _harm = item
        except Exception as e:
            logger.error(f"Moderation：{prompt}:{e}")
            _harm = False
        return _harm

    def pre_check(self) -> Tuple[bool, str]:
        # Flood
        if Utils.WaitFlood(user=self.user, group=self.group):
            return False, "TOO FAST"
        _Usage = self._UsageManager.isOutUsage()
        if _Usage["status"]:
            return False, f"小时额度或单人总额度用完，请重置或等待下一个小时\n{_Usage['use']}"
        return True, ""

    async def load_response(self,
                            profile: Conversation,
                            llm_model: LlmBase,
                            prompt: PromptEngine = None,
                            method: str = "chat") -> PublicReturn:
        """
        发起请求
        :param profile: 身份验证类
        :param llm_model: LLM 模型
        :param prompt: 提示引擎
        :param method: 回复类型
        :return:
        """
        load_csonfig()
        #
        _think = ThinkEngine(profile=self.group)
        _think.register_hook(Hook(name="sad", trigger="very sad", value=3, last=60, time=int(time.time())))
        _think.register_hook(Hook(name="bored", trigger="very bored", value=3, last=60, time=int(time.time())))
        # 关键检查
        status, log = self.pre_check()
        if not status:
            _think.hook(random.choice(["bored"]))
            return PublicReturn(status=True, trace="Req", reply=log)

        # Api Key 检查
        if not self.api_key:
            logger.error("Api Check:Api Key pool empty")
            raise LoadResponseError("Found:Api Key pool empty")

        # 内容安全策略
        _prompt = prompt.prompt
        _harm = await self.openai_moderation(prompt=_prompt.prompt)
        if _harm:
            _info = DefaultData.getRefuseAnswer()
            await asyncio.sleep(random.randint(1, 4))
            _think.hook(random.choice(["sad"]))
            return PublicReturn(status=True, trace="Req", reply=f"{_info}\nYou talk too {_harm}.")

        # 初始化记忆管理器
        try:
            # 分发类型
            if method == "write":
                llm_param = LLM_MODEL_PARAM
                response = await llm_model.run(prompt=str(_prompt.text),
                                               predict_tokens=int(_csonfig["token_limit"]),
                                               llm_param=llm_param
                                               )
                _deal = response.reply[0]
                _usage = response.usage
                logger.success(
                    f"Write:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {_prompt.text} --req: {_deal}"
                )
            elif method == "catch":
                chat_client = llm_kira.client.ChatBot(profile=profile, llm_model=llm_model)
                llm_param = LLM_MODEL_PARAM
                response = await chat_client.predict(
                    llm_param=llm_param,
                    prompt=prompt,
                    predict_tokens=math.ceil(int(_csonfig["token_limit"]) * 0.7),
                )
                prompt.clean(clean_prompt=True)
                _deal = response.reply
                _usage = response.llm.usage
                logger.success(
                    f"CHAT:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {_prompt.text} --req: {_deal} "
                )
            elif method == "chat":
                _head = None
                if _csonfig.get("allow_change_head"):
                    _head = Header(uid=self.user).get()
                    _head = ContentDfa.filter_all(_head)
                    if len(_head) < 6:
                        _head = None
                _style = {}
                if _csonfig.get("allow_change_style"):
                    _style = Style(uid=self.user).get()
                    if len(_style) < 10:
                        _style = {}
                _result = []
                try:
                    if len(_prompt.text) > 5 and Detect().isQuery(_prompt.text):
                        _result = await prompt.build_skeleton(query=_prompt,
                                                              llm_task="Summary Text" if len(
                                                                  _prompt.text) > 20 else None,
                                                              skeleton=random.choice([SearchCraw(), DuckgoCraw()])
                                                              )
                except Exception as e:
                    logger.warning(e)
                for item in _result:
                    prompt.insert_knowledge(knowledge=item)
                chat_client = llm_kira.client.ChatBot(profile=profile, llm_model=llm_model)
                prompt: PromptEngine
                if _head:
                    prompt.description += str(_head)[:400]
                llm_param = LLM_MODEL_PARAM
                llm_param.temperature = 0.5
                llm_param.logit_bias = _style
                llm_param.presence_penalty = 0.5
                response = await chat_client.predict(
                    prompt=prompt,
                    predict_tokens=int(_csonfig["token_limit"]),
                    llm_param=llm_param
                )
                prompt.clean(clean_prompt=True)
                _deal = response.reply
                _usage = response.llm.usage
                logger.success(
                    f"CHAT:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {_prompt.text} --req: {_deal} ")
            else:
                return PublicReturn(status=False, trace="Req", msg="NO SUPPORT METHOD")
        except RateLimitError as e:
            _usage = 0
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:RateLimitError Reach Limit|Overload"
            logger.error(f"RUN:Openai Error:{e}")
        except ServiceUnavailableError as e:
            _usage = 0
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:ServiceUnavailableError Server:500"
            logger.error(f"RUN:Openai Error:{e}")
        except AuthenticationError as e:
            _usage = 0
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:AuthenticationError"
            logger.error(f"RUN:Openai Error:{e}")
        except LLMException as e:
            _usage = 0
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:llm-kira tips error"
            logger.error(f"RUN:Openai Error:{e}")
        except Exception as e:
            _usage = 0
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:Unknown Error"
            logger.error(f"RUN:Openai Error:{e}")
        # 更新额度
        _AnalysisUsage = self._UsageManager.renewUsage(usage=_usage)
        # 更新统计
        DefaultData().setAnalysis(usage={f"{self.user}": _AnalysisUsage.total_usage})
        # 人性化处理
        _deal = ContentDfa.filter_all(_deal)
        _deal = Utils.Humanization(_deal)
        if _usage == 0:
            return PublicReturn(status=False, trace="Req", msg=_deal)
        else:
            return PublicReturn(status=True, trace="Req", reply=_deal)


async def WhiteUserCheck(user_id: int, WHITE: str = "") -> PublicReturn:
    """
    :param user_id: user id
    :param WHITE: 白名单提示
    :return: TRUE,msg -> 在白名单
    """
    if _csonfig["whiteUserSwitch"]:
        # 没有在白名单里！
        if UserManager(user_id).read("white"):
            return PublicReturn(status=True, trace="WhiteUserCheck")
        msg = f"{user_id}:Check the settings to find that you is not whitelisted!...{WHITE}"
        if UserManager(user_id).read("block"):
            msg = f"{user_id}:Blocked!...{WHITE}"
        return PublicReturn(status=False,
                            trace="WhiteUserCheck",
                            msg=msg)
    else:
        return PublicReturn(status=True, trace="WhiteUserCheck")


async def WhiteGroupCheck(group_id: int, WHITE: str = "") -> PublicReturn:
    """
    :param group_id: group id
    :param WHITE:
    :return: TRUE,msg -> 在白名单
    """
    #
    if _csonfig["whiteGroupSwitch"]:
        # 没有在白名单里！
        if GroupManager(group_id).read("white"):
            return PublicReturn(status=True, trace="WhiteUserCheck")
        msg = f"{group_id}:Check the settings to find that you is not whitelisted!...{WHITE}"
        if GroupManager(group_id).read("block"):
            msg = f"{group_id}:Blocked!...{WHITE}"
        return PublicReturn(status=False,
                            trace="WhiteUserCheck",
                            msg=msg)
    else:
        return PublicReturn(status=True, trace="WhiteUserCheck")


async def RemindSet(user_id,
                    start_name: str = "Human",
                    restart_name: str = "Ai",
                    text: str = "") -> PublicReturn:
    """
    :param restart_name: 机器人自己的名字
    :param start_name: 交谈人的名字
    :param user_id:
    :param text:
    :return: Ture 代表设定成功
    """
    _text = text
    _user_id = user_id
    _remind_r = _text.split(" ", 1)
    if len(_remind_r) < 2:
        return PublicReturn(status=False, msg=f"", trace="Remind")
    _remind = _remind_r[1]
    if Utils.tokenizer(_remind) > 333:
        return PublicReturn(status=True, msg=f"过长:{_remind}", trace="Remind")
    if _csonfig.get("allow_change_head"):
        # _remind = _remind.replace("你是", "ME*扮演")
        _remind = _remind.replace("你", "<|ME|>")
        _remind = _remind.replace("我", "<|YOU|>")
        _remind = _remind.replace("<|YOU|>", DefaultData.name_split(sentence=start_name, limit=10))
        _remind = _remind.replace("<|ME|>", DefaultData.name_split(sentence=restart_name, limit=10))
        _safe_remind = ContentDfa.filter_all(_remind)
        Header(uid=_user_id).set(_safe_remind)
        return PublicReturn(status=True, msg=f"设定:{_remind}\nNo reply this msg", trace="Remind")
    Header(uid=_user_id).set({})
    return PublicReturn(status=True, msg=f"I refuse Remind Command", trace="Remind")


async def StyleSet(user_id, text) -> PublicReturn:
    """
    :param user_id:
    :param text:
    :return: Ture 代表设定成功
    """
    _text = text
    _user_id = user_id
    _style_r = _text.split(" ", 1)
    if len(_style_r) < 2:
        return PublicReturn(status=False, msg=f"", trace="StyleSet")
    _style = _style_r[1]
    if Utils.tokenizer(_style) > 800:
        return PublicReturn(status=True, msg=f"过长:{_style}", trace="StyleSet")
    _style_token_list = re.split("[,，]", _style)
    _token = {}
    if _csonfig.get("allow_change_style"):
        for item in _style_token_list:
            item = str(item)
            _weight = round(item.count("(") + item.count("{") + 1 - item.count("[") * 1.5)
            item = item.replace("(", "").replace("{", "").replace("[", "").replace(")", "").replace("}", "").replace(
                "]", "")
            _weight = _weight if _weight <= 20 else 2
            _weight = _weight if _weight >= -80 else 0
            _encode_token = llm_kira.utils.chat.gpt_tokenizer.encode(item)
            _love = {str(token): _weight for token in _encode_token}
            _child_token = {}
            for token, weight in _love.items():
                token = str(token)
                if token in _token.keys():
                    __weight = _token.get(token) + _weight
                else:
                    __weight = _weight
                _child_token[token] = __weight
            _token.update(_child_token)
        Style(uid=_user_id).set(_token)
        return PublicReturn(status=True, msg=f"Style:{_style}\nNo reply this msg", trace="StyleSet")
    Style(uid=_user_id).set(_token)
    return PublicReturn(status=True, msg=f"I refuse StyleSet Command", trace="StyleSet")


async def PromptType(text, types: str = "group") -> PublicReturn:
    """
    消息预处理，命令识别和与配置的交互层
    :param text:
    :param types:
    :return: TRUE,msg -> 继续执行
    """
    load_csonfig()
    # 拿到 prompt
    _raw_prompt = text
    _prompt_types = "unknown"
    _prompt = ""
    # 不会重复的流程组
    # Chat
    if _raw_prompt.startswith("/chat"):
        _prompt_r = _raw_prompt.split(" ", 1)
        if len(_prompt_r) > 1:
            _prompt = _prompt_r[1]
        _prompt_types = "chat"
    # Write
    if _raw_prompt.startswith("/catch"):
        _prompt_r = _raw_prompt.split(" ", 1)
        if len(_prompt_r) > 1:
            _prompt = _prompt_r[1]
        _prompt_types = "catch"
    # Write
    if _raw_prompt.startswith("/write"):
        _prompt_r = _raw_prompt.split(" ", 1)
        if len(_prompt_r) > 1:
            _prompt = _prompt_r[1]
        _prompt_types = "write"
    # 处置空，也许是多余的
    if len(_prompt) < 1:
        _prompt_types = "unknown"
    # 校验结果
    if _prompt_types == "unknown":
        # 不执行
        return PublicReturn(status=False, msg=types, data=_prompt_types, trace="PromptPreprocess")
    return PublicReturn(status=True, msg=types, data=_prompt_types, trace="PromptPreprocess")


async def Group(Message: User_Message, bot_profile: ProfileReturn, config) -> PublicReturn:
    """
    根据文本特征分发决策
    :param bot_profile:
    :param Message:
    :param config:
    :return: True 回复用户
    """
    load_csonfig()
    _prompt = list(reversed(Message.prompt))
    _text = Message.text
    _user_id = Message.from_user.id
    _chat_id = Message.from_chat.id
    _user_name = Message.from_user.name
    _bot_name = bot_profile.bot_name
    # 状态
    if not _csonfig.get("statu"):
        return PublicReturn(status=True, msg="BOT:Under Maintenance", trace="Statu")

    # 白名单检查
    _white_user_check = await WhiteGroupCheck(_chat_id, config.WHITE)
    _white_user_check: PublicReturn
    if not _white_user_check.status:
        return PublicReturn(status=True, trace="WhiteGroupCheck", msg=_white_user_check.msg)
    # Prompt 创建
    _prompt_type = await PromptType(text=_text, types="group")
    _prompt_type: PublicReturn
    _cid = DefaultData.composing_uid(user_id=_user_id, chat_id=_chat_id) if _prompt_type.data != "catch" else _chat_id
    start_name = DefaultData.name_split(sentence=_user_name, limit=10)
    restart_name = DefaultData.name_split(sentence=_bot_name, limit=10)

    conversation = llm_kira.client.Conversation(
        start_name=start_name,
        restart_name=restart_name,
        conversation_id=int(_cid),
    )
    _think = ThinkEngine(profile=_chat_id)
    _think.register_hook(Hook(name="happy", trigger="very happy", value=3, last=60, time=int(time.time())))
    _think.register_hook(Hook(name="sad", trigger="very sad", value=4, last=120, time=int(time.time())))
    _think.register_hook(Hook(name="bored", trigger="very bored", value=5, last=30, time=int(time.time())))
    _think.register_hook(
        Hook(name="sleepy", trigger="very sleepy,want sleep", value=2, last=120, time=int(time.time())))
    if _think.is_night:
        _think.hook("sleepy")
    if random.randint(1, 100) > 80:
        _think.hook("happy")

    # 线性决策
    if _text.startswith("/remind"):
        _remind_set = await RemindSet(user_id=_user_id, start_name=_user_name, restart_name=_bot_name, text=_text)
        _remind_set: PublicReturn
        return PublicReturn(status=True, trace="Remind", reply=_remind_set.msg)

    if _text.startswith("/style"):
        _style_set = await StyleSet(user_id=_user_id, text=_text)
        _style_set: PublicReturn
        return PublicReturn(status=True, trace="Style", reply=_style_set.msg)

    if _text.startswith("/forgetme"):
        await Forget(user_id=_user_id, chat_id=_chat_id)
        _think.hook("sad")
        return PublicReturn(status=True, reply=f"Down,Miss you", trace="ForgetMe")

    if _text.startswith("/voice"):
        _user_manger = UserManager(_user_id)
        _set = True
        if _user_manger.read("voice"):
            _set = False
        _user_manger.save({"voice": _set})
        return PublicReturn(status=True, reply=f"TTS:{_set}", trace="VoiceSet")

    # 对话层
    if not _prompt_type.status:
        return PublicReturn(status=False, msg=f"No Match Type", trace="PromptPreprocess")
    API_KEY = OPENAI_API_KEY_MANAGER.get_key()
    if not API_KEY and isinstance(LLM_MODEL_PARAM, OpenAiParam):
        return PublicReturn(status=True, msg=f"I finished eating the Api key, I'm so hungry", trace="Error")
    # LLM
    llm_model = LLM_CLIENT(
        profile=conversation,
        api_key=API_KEY,
        call_func=OPENAI_API_KEY_MANAGER.check_api_key,
        token_limit=MODEL_TOKEN_LIMIT,
        auto_penalty=_csonfig["auto_adjust"],
    )
    # 构建
    _description = "📱💬|Now " + str(time.strftime("%Y/%m/%d %H:%M", time.localtime())) + "|"
    _description += f" 🌙" if _think.is_night else random.choice([" 🌻", " 🌤", " 🌦"])
    _description += f"\n{restart_name}-{''.join(_think.build_status(rank=20))}"
    promptManager = llm_kira.creator.engine.PromptEngine(profile=conversation,
                                                         connect_words="\n",
                                                         memory_manger=llm_kira.client.MemoryManager(
                                                             profile=conversation),
                                                         reference_ratio=0.3,
                                                         llm_model=llm_model,
                                                         description=_description,
                                                         )
    for item in _prompt:
        if ContentDfa.exists(item):
            _think.hook(random.choice(["bored", "sad"]))
        item = ContentDfa.filter_all(item)
        if item.startswith("/"):
            _split_prompt = item.split(" ", 1)
            if len(_split_prompt) > 1:
                item = _split_prompt[1]
        start, item = Utils.get_head_foot(prompt=item)
        start = start if start else conversation.start_name
        promptManager.insert_prompt(prompt=PromptItem(start=start, text=str(item)))
    try:
        _client = Reply(user=_user_id, group=_chat_id, api_key=OPENAI_API_KEY_MANAGER.get_key())
        _client_response = await _client.load_response(
            profile=conversation,
            prompt=promptManager,
            method=_prompt_type.data,
            llm_model=llm_model
        )
        if not _client_response.status:
            raise LoadResponseError(_client_response.msg)
        # message_type = "text"
        _info = []
        # 语音消息
        _voice = UserManager(_user_id).read("voice")
        voice_data = None
        if _voice:
            voice_data = await TTSSupportCheck(text=_client_response.reply, user_id=_user_id)
        if _voice and not voice_data:
            _info.append("TTS Unavailable")
        # message_type = "voice" if _voice and voice_data else message_type
        # f"{_req}\n{config.INTRO}\n{''.join(_info)}"
        _log = '\n'.join(_info)
        return PublicReturn(status=True, msg=f"OK", trace="Reply", voice=voice_data,
                            reply=f"{_client_response.reply}\n{_log}")
    except LoadResponseError as e:
        return PublicReturn(status=True, msg=f"{e}", trace="Error")
    except Exception as e:
        logger.error(e)
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply="Error Occur~Check Bot Env/Config~nya")


async def Friends(Message: User_Message, bot_profile: ProfileReturn, config) -> PublicReturn:
    """
    根据文本特征分发决策
    :param bot_profile:
    :param Message:
    :param config:
    :return: True 回复用户
    """
    load_csonfig()
    _prompt = list(reversed(Message.prompt))
    _text = Message.text
    _user_id = Message.from_user.id
    _chat_id = Message.from_chat.id
    _user_name = Message.from_user.name
    _bot_name = bot_profile.bot_name

    # 状态
    if not _csonfig.get("statu"):
        return PublicReturn(status=True, msg="BOT:Under Maintenance", trace="Statu")

    # 白名单检查
    _white_user_check = await WhiteUserCheck(_user_id, config.WHITE)
    _white_user_check: PublicReturn
    if not _white_user_check.status:
        return PublicReturn(status=True, trace="WhiteGroupCheck", msg=_white_user_check.msg)
    # Prompt 创建
    _prompt_type = await PromptType(text=_text, types="private")
    _prompt_type: PublicReturn

    _cid = DefaultData.composing_uid(user_id=_user_id,
                                     chat_id=_chat_id) if _prompt_type.data != "catch" else _chat_id
    start_name = DefaultData.name_split(sentence=_user_name, limit=10)
    restart_name = DefaultData.name_split(sentence=_bot_name, limit=10)

    conversation = llm_kira.client.Conversation(
        start_name=start_name,
        restart_name=restart_name,
        conversation_id=int(_cid),
    )
    _think = ThinkEngine(profile=_chat_id)
    _think.register_hook(Hook(name="happy", trigger="very happy", value=3, last=60, time=int(time.time())))
    _think.register_hook(Hook(name="sad", trigger="very sad", value=4, last=120, time=int(time.time())))
    _think.register_hook(Hook(name="bored", trigger="very bored", value=5, last=30, time=int(time.time())))
    _think.register_hook(
        Hook(name="sleepy", trigger="very sleepy,want sleep", value=2, last=120, time=int(time.time())))
    if _think.is_night:
        _think.hook("sleepy")

    # 线性决策
    if _text.startswith("/remind"):
        _remind_set = await RemindSet(user_id=_user_id, start_name=_user_name, restart_name=_bot_name, text=_text)
        _remind_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Remind",
                            reply=_remind_set.msg)

    if _text.startswith("/style"):
        _style_set = await StyleSet(user_id=_user_id, text=_text)
        _style_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Style",
                            reply=_style_set.msg)

    if _text.startswith("/forgetme"):
        _think.hook("sad")
        await Forget(user_id=_user_id, chat_id=_chat_id)
        return PublicReturn(status=True, reply=f"Down,Miss you", trace="ForgetMe")

    if _text.startswith("/voice"):
        _user_manger = UserManager(_user_id)
        _set = True
        if _user_manger.read("voice"):
            _set = False
        _user_manger.save({"voice": _set})
        return PublicReturn(status=True, reply=f"TTS:{_set}", trace="Voice")

    # 对话层
    if not _prompt_type.status:
        return PublicReturn(status=False, msg=f"No Match Type", trace="PromptPreprocess")
    API_KEY = OPENAI_API_KEY_MANAGER.get_key()
    if not API_KEY and isinstance(LLM_MODEL_PARAM, OpenAiParam):
        return PublicReturn(status=True, msg=f"I finished eating the Api key, I'm so hungry", trace="Error")
    # LLM
    llm_model = LLM_CLIENT(
        profile=conversation,
        api_key=API_KEY,
        call_func=OPENAI_API_KEY_MANAGER.check_api_key,
        token_limit=MODEL_TOKEN_LIMIT,
        auto_penalty=_csonfig["auto_adjust"],
    )
    # 构建
    _description = "📱💬|Now " + str(time.strftime("%Y/%m/%d %H:%M", time.localtime())) + "|"
    _description += f" 🌙" if _think.is_night else random.choice([" 🌻", " 🌤", " 🌦"])
    _description += f"\n{restart_name}-{''.join(_think.build_status(rank=20))}"
    promptManager = llm_kira.creator.engine.PromptEngine(profile=conversation,
                                                         connect_words="\n",
                                                         memory_manger=llm_kira.client.MemoryManager(
                                                             profile=conversation),
                                                         reference_ratio=0.3,
                                                         llm_model=llm_model,
                                                         description=_description,
                                                         )
    # 构建
    for item in _prompt:
        if ContentDfa.exists(item):
            _think.hook("bored")
            _think.hook("sad")
        item = ContentDfa.filter_all(item)
        if item.startswith("/"):
            _split_prompt = item.split(" ", 1)
            if len(_split_prompt) > 1:
                item = _split_prompt[1]
        start, item = Utils.get_head_foot(prompt=item)
        start = start if start else conversation.start_name
        promptManager.insert_prompt(prompt=PromptItem(start=start, text=str(item)))
    try:
        _client = Reply(user=_user_id, group=_chat_id, api_key=OPENAI_API_KEY_MANAGER.get_key())
        _client_response = await _client.load_response(
            profile=conversation,
            prompt=promptManager,
            method=_prompt_type.data,
            llm_model=llm_model
        )
        if not _client_response.status:
            raise LoadResponseError(_client_response.msg)
        # message_type = "text"
        _info = []
        # 语音消息
        _voice = UserManager(_user_id).read("voice")
        voice_data = None
        if _voice:
            voice_data = await TTSSupportCheck(text=_client_response.reply, user_id=_user_id)
        if not voice_data and _voice:
            _info.append("TTS Unavailable")
        # message_type = "voice" if _voice and voice_data else message_type
        # f"{_req}\n{config.INTRO}\n{''.join(_info)}"
        _log = '\n'.join(_info)
        return PublicReturn(status=True, msg=f"OK", trace="Reply", voice=voice_data,
                            reply=f"{_client_response.reply}\n{_log}")
    except LoadResponseError as e:
        return PublicReturn(status=True, msg=f"{e}", trace="Error")
    except Exception as e:
        logger.error(e)
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply="Oh no~ Check Bot Env/Config~ nya")


async def Trigger(Message: User_Message, config) -> PublicReturn:
    """
    :param Message: group id
    :param config:
    :return: TRUE,msg -> 在白名单
    """
    group_id = Message.from_chat.id
    if config.trigger:
        if GroupManager(group_id).read("trigger"):
            return PublicReturn(status=True, trace="TriggerCheck")
    return PublicReturn(status=False, trace="No trigger")


async def Trace(Message: User_Message, config) -> PublicReturn:
    """
    :param Message: group id
    :param config:
    :return: TRUE,msg -> 在白名单
    """
    group_id = Message.from_chat.id
    if GroupManager(group_id).read("trace"):
        return PublicReturn(status=True, trace="TraceCheck")
    return PublicReturn(status=False, trace="No Trace")


async def Silent(Message: User_Message, config) -> PublicReturn:
    """
    :param Message: group id
    :param config:
    :return: TRUE,msg -> 在白名单
    """
    group_id = Message.from_chat.id
    if GroupManager(group_id).read("silent"):
        return PublicReturn(status=True, trace="silentCheck")
    return PublicReturn(status=False, trace="No silent")


async def Cross(Message: User_Message, config) -> PublicReturn:
    """
    :param Message: group id
    :param config:
    :return: TRUE,msg -> 在白名单
    """
    group_id = Message.from_chat.id
    if GroupManager(group_id).read("cross"):
        return PublicReturn(status=True, trace="CrossCheck")
    return PublicReturn(status=False, trace="No Cross")


async def GroupAdminCommand(Message: User_Message, config):
    load_csonfig()
    _reply = []
    group_id = Message.from_chat.id
    try:
        command = Message.text
        if command.startswith("/trigger"):
            _group_manger = GroupManager(int(group_id))
            _set = True
            if _group_manger.read("trigger"):
                _set = False
            _group_manger.save({"trigger": _set})
            _ev = f"Group Admin:GroupTrigger {_set}"
            _reply.append(_ev)
            logger.info(_ev)
        #
        if command.startswith("/trace"):
            _group_manger = GroupManager(int(group_id))
            _set = True
            if _group_manger.read("trace"):
                _set = False
            _group_manger.save({"trace": _set})
            _ev = f"Group Admin:GroupTrace {_set}"
            _reply.append(_ev)
            logger.info(_ev)
        if command.startswith("/cross"):
            _group_manger = GroupManager(int(group_id))
            _set = True
            if _group_manger.read("cross"):
                _set = False
            _group_manger.save({"cross": _set})
            _ev = f"Group Admin:GroupCross {_set}"
            _reply.append(_ev)
            logger.info(_ev)
        if command.startswith("/silent"):
            _group_manger = GroupManager(int(group_id))
            _set = True
            if _group_manger.read("silent"):
                _set = False
            _group_manger.save({"silent": _set})
            _ev = f"Group Admin:GroupSilent {_set}"
            _reply.append(_ev)
            logger.info(_ev)
    except Exception as e:
        logger.error(e)
    return _reply


async def MasterCommand(user_id: int, Message: User_Message, config):
    load_csonfig()
    _reply = []
    if user_id in config.master:
        try:
            command = Message.text
            # SET
            if command.startswith("/set_user_cold"):
                # 用户冷静时间
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["usercold_time"] = int(_len_)
                    _reply.append(f"user cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset user cold time limit to{_len_}")

            if command.startswith("/set_group_cold"):
                # 群组冷静时间
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["groupcold_time"] = int(_len_)
                    _reply.append(f"group cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset group cold time limit to{_len_}")

            if command.startswith("/set_per_user_limit"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["per_user_limit"] = int(_len_)
                    _reply.append(f"set_hour_limit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset per_user_limit to{_len_}")

            if command.startswith("/set_per_hour_limit"):
                # 设定用户小时用量
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["hour_limit"] = int(_len_)
                    _reply.append(f"hour_limit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset hour_limit to{_len_}")

            if command.startswith("/promote_user_limit"):
                # 设定用户小时用量
                _len = Utils.extract_arg(command)
                if len(_len) != 2:
                    return
                __user_id = int("".join(list(filter(str.isdigit, _len[0]))))
                __limit = int("".join(list(filter(str.isdigit, _len[1]))))
                if __user_id > 0 and __limit > 0:
                    UserManager(__user_id).save({"usage": __limit})
                    _reply.append(f"user_limit:{__limit}")
                    logger.info(f"SETTING:promote user_limit to{__limit}")

            if command.startswith("/reset_user_usage"):
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        Usage(uid=_len_).resetTotalUsage()
                        logger.info(f"SETTING:resetTotalUsage {_len_} limit to 0")
                        _reply.append(f"hour_limit:{_len}")

            if command.startswith("/set_token_limit"):
                # 返回多少？
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["token_limit"] = int(_len_)
                    _reply.append(f"tokenlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset tokenlimit limit to{_len_}")

            if command.startswith("/set_input_limit"):
                # 输入字符？
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["input_limit"] = int(_len_)
                    _reply.append(f"input limit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset input limit to{_len_}")

            if "/add_block_group" in command:
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add block group {_len_}"
                        GroupManager(int(_len_)).save({"block": True})
                        _reply.append(_ev)
                        logger.info(_ev)

            if "/del_block_group" in command:
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del block group {_len_}"
                        GroupManager(int(_len_)).save({"block": False})
                        _reply.append(_ev)
                        logger.info(_ev)

            if "/add_block_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_block_userp {_len_}"
                        UserManager(int(_len_)).save({"block": True})
                        _reply.append(_ev)
                        logger.info(_ev)

            if "/del_block_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_block_user {_len_}"
                        UserManager(int(_len_)).save({"block": False})
                        _reply.append(_ev)
                        logger.info(_ev)

            # whiteGroup
            if "/add_white_group" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_white_group {_len_}"
                        GroupManager(int(_len_)).save({"white": True})
                        _reply.append(_ev)
                        logger.info(_ev)

            if "/del_white_group" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_white_group {_len_}"
                        GroupManager(int(_len_)).save({"white": False})
                        _reply.append(_ev)
                        logger.info(_ev)

            # whiteUser
            if "/add_white_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_white_user {_len_}"
                        UserManager(int(_len_)).save({"white": True})
                        _reply.append(_ev)
                        logger.info(_ev)

            if "/del_white_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_white_user {_len_}"
                        UserManager(int(_len_)).save({"white": False})
                        _reply.append(_ev)
                        logger.info(_ev)

            # UPDATE
            if command.startswith("/update_detect"):
                keys, _error = initCensor()
                if _error:
                    error = '\n'.join(_error)
                    errors = f"Error:\n{error}"
                else:
                    # 重载 Danger 库
                    ContentDfa.change_words(path="./Data/Danger.form")
                    errors = "Success"
                _reply.append(f"{'|'.join(keys)}\n\n{errors}")

            # USER White
            if command.startswith("/open_user_white_mode"):
                _csonfig["whiteUserSwitch"] = True
                _reply.append("SETTING:whiteUserSwitch ON")
                save_csonfig()
                logger.info("SETTING:whiteUser ON")

            if command.startswith("/close_user_white_mode"):
                _csonfig["whiteUserSwitch"] = False
                _reply.append("SETTING:whiteUserSwitch OFF")
                save_csonfig()
                logger.info("SETTING:whiteUser OFF")

            # GROUP White
            if command.startswith("/open_group_white_mode"):
                _csonfig["whiteGroupSwitch"] = True
                _reply.append("ON:whiteGroup")
                save_csonfig()
                logger.info("SETTING:whiteGroup ON")

            if command.startswith("/close_group_white_mode"):
                _csonfig["whiteGroupSwitch"] = False
                _reply.append("SETTING:whiteGroup OFF")
                save_csonfig()
                logger.info("SETTING:whiteGroup OFF")

            if command.startswith("/see_api_key"):
                keys = OPENAI_API_KEY_MANAGER.get_key()
                # 脱敏
                _key = []
                for i in keys:
                    _key.append(DefaultData.mask_middle(i, 6))
                _info = '\n'.join(_key)
                _reply.append(f"Now Have \n{_info}")

            if "/add_api_key" in command:
                _parser = Utils.extract_arg(command)
                if _parser:
                    OPENAI_API_KEY_MANAGER.add_key(key=str(_parser[0]).strip())
                logger.info("SETTING:ADD API KEY")
                _reply.append("SETTING:ADD API KEY")

            if "/del_api_key" in command:
                _parser = Utils.extract_arg(command)
                if _parser:
                    OPENAI_API_KEY_MANAGER.pop_key(key=str(_parser[0]).strip())
                logger.info("SETTING:DEL API KEY")
                _reply.append("SETTING:DEL API KEY")

            if "/change_style" in command:
                if _csonfig["allow_change_style"]:
                    _allow_change_style = False
                else:
                    _allow_change_style = True
                _csonfig["allow_change_style"] = _allow_change_style
                _reply.append(f"SETTING:allow_change_style {_allow_change_style}")
                save_csonfig()
                logger.info(f"SETTING:allow_change_style {_allow_change_style}")

            if "/change_head" in command:
                if _csonfig["allow_change_head"]:
                    _allow_change_head = False
                else:
                    _allow_change_head = True
                _csonfig["allow_change_head"] = _allow_change_head
                _reply.append(f"SETTING:allow_change_head {_allow_change_head}")
                save_csonfig()
                logger.info(f"SETTING:allow_change_head {_allow_change_head}")

            if "/auto_adjust" in command:
                if _csonfig["auto_adjust"]:
                    _adjust = False
                else:
                    _adjust = True
                _csonfig["auto_adjust"] = _adjust
                _reply.append(f"SETTING:auto_adjust {_adjust}")
                save_csonfig()
                logger.info(f"SETTING:auto_adjust {_adjust}")

            if command == "/open":
                _csonfig["statu"] = True
                _reply.append("SETTING:BOT ON")
                save_csonfig()
                logger.info("SETTING:BOT ON")

            if command == "/close":
                _csonfig["statu"] = False
                _reply.append("SETTING:BOT OFF")
                save_csonfig()
                logger.info("SETTING:BOT OFF")
        except Exception as e:
            logger.error(e)
        return _reply


async def Start(_):
    return f"Ping，Use /chat start a new chat loop"


async def About(config):
    return f"{config.ABOUT}"


async def Help(_):
    return """
Hi,Here a simple intro.
Use /chat + sentence to Start
Use /write + sentence to Write(once)
Use /remind + sentence to make it remember forever something.(Overwritten, single words will be ignored)
Use /forgetme reset history
Use /voice to start voice chat(if have)
Use /style design probability of occurrence of a character，中文效果较弱，(enhance),[wake]

Admin please check Bot Command Table for more interesting func.
"""
