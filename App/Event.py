# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Event.py
# @Software: PyCharm
# @Github    ：sudoskys

import json
import random
import pathlib
import asyncio
import re
import time
import llm_kira
# from io import BytesIO
from typing import Union
from loguru import logger

# import llm_kira
from llm_kira.utils.chat import Cut
from llm_kira.client import Optimizer, PromptManager, Conversation
from llm_kira.client.types import PromptItem
from llm_kira.client.llms.openai import OpenAiParam

# from App.chatGPT import PrivateChat
from utils.Chat import Utils, Usage, rqParser, GroupManager, UserManager, Header, Style
from utils.Data import DictUpdate, DefaultData, Openai_Api_Key, Service_Data, User_Message, PublicReturn, ProxyConfig
from utils.Setting import ProfileReturn
from utils.TTS import TTS_Clint, TTS_REQ
from utils.Detect import DFA, Censor, get_start_name
from utils.Logging import LoadResponseError
from utils.Lock import pLock

OPENAI_API_KEY_MANAGER = Openai_Api_Key(filePath="./Config/api_keys.json")

# fast text langdetect

_service = Service_Data.get_key()
REDIS_CONF = _service["redis"]
TTS_CONF = _service["tts"]
PLUGIN_TABLE = _service["plugin"]
BACKEND_CONF = _service["backend"]
PROXY_CONF = ProxyConfig(**_service["proxy"])
HARM_TYPE = _service["moderation_type"]
HARM_TYPE = list(set(HARM_TYPE))

# Model
MODEL_NAME = BACKEND_CONF.get("model")
MODEL_TOKEN_LIMIT = BACKEND_CONF.get("token_limit")
MODEL_TOKEN_LIMIT = MODEL_TOKEN_LIMIT if MODEL_TOKEN_LIMIT else 3500
if not MODEL_NAME:
    logger.warning("Model Conf Not Found")

# Proxy

if PROXY_CONF.status:
    llm_kira.setting.proxyUrl = PROXY_CONF.url

llm_kira.setting.redisSetting = llm_kira.setting.RedisConfig(**REDIS_CONF)

urlForm = {
    "Danger.form": [
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2Z3d2RuL3NlbnNpdGl2ZS1zdG9wLXdvcmRzL21hc3Rlci8lRTYlOTQlQkYlRTYlQjIlQkIlRTclQjElQkIudHh0",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL1RlbGVjaGFCb3QvQW50aVNwYW0vbWFpbi9EYW5nZXIudHh0",
        # 国家 + 政党 + 人种
        # "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL1RlbGVjaGFCb3QvQW50aVNwYW0vbWFpbi9BaS50eHQ=",
        # "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FkbGVyZWQvRGFuZ2Vyb3VzU3BhbVdvcmRzL21hc3Rlci9EYW5nZXJvdXNTcGFtV29yZHMvR2VuZXJhbF9TcGFtV29yZHNfVjEuMC4xX0NOLm1pbi50eHQ=",
        # NSFW "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0phaW1pbjEzMDQvc2Vuc2l0aXZlLXdvcmQtZGV0ZWN0b3IvbWFpbi9zYW1wbGVfZmlsZXMvc2FtcGxlX2Jhbm5lZF93b3Jkcy50eHQ=",
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
    if pathlib.Path("./Config/config.json").exists():
        with open("./Config/config.json", encoding="utf-8") as f:
            _csonfig = json.load(f)
    else:
        _csonfig = {}
    DictUpdate.dict_update(now_table, _csonfig)
    _csonfig = now_table
    return _csonfig


def save_csonfig():
    pLock.getInstance().acquire()
    with open("./Config/config.json", "w+", encoding="utf8") as f:
        json.dump(_csonfig, f, indent=4, ensure_ascii=False)
    pLock.getInstance().release()


async def TTSSupportCheck(text, user_id, limit: bool = True):
    global TTS_CONF
    """
    处理消息文本并构造请求返回字节流或者空。隶属 Event 文件
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
        from langdetect import detect
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
        result, e = await TTS_Clint.request_vits_server(url=_vits_config["api"],
                                                        params=TTS_REQ(task_id=user_id,
                                                                       text=_new_text,
                                                                       model_name=_vits_config["model_name"],
                                                                       speaker_id=_vits_config["speaker_id"],
                                                                       audio_type="ogg"
                                                                       ))

        if not result:
            logger.error(f"TTS:{user_id} --type:vits --content: {text}:{len(text)} --{e}")
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
        result, e = await TTS_Clint.request_azure_server(key=_azure_config["key"],
                                                         location=_azure_config["location"],
                                                         text=_new_text,
                                                         speaker=_speaker
                                                         )
        if not result:
            logger.error(f"TTS:{user_id} --type:azure --content: {text}:{len(text)} --{e}")
            return

        logger.info(f"TTS:{user_id} --type:azure --content: {text}:{len(text)}")
        # 返回字节流
        return result
    else:
        # 啥也没有
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
    mem = receiver.MemoryManager(profile=conversation)
    return mem.reset_chat()


class Reply(object):
    def __init__(self, user, group, api_key: Union[list, str]):
        # 用量检测
        self.user = user
        self.group = group
        self._UsageManager = Usage(uid=self.user)
        self.api_key = api_key

    async def openai_moderation(self, prompt: str):
        # 内容审计
        try:
            _harm = False
            if HARM_TYPE:
                _Moderation_rep = await llm_kira.openai.Moderations(api_key=self.api_key).create(input=str(prompt))
                _moderation_result = _Moderation_rep["results"][0]
                _harm_result = [key for key, value in _moderation_result["categories"].items() if value == True]
                for item in _harm_result:
                    if item in HARM_TYPE:
                        _harm = item
        except Exception as e:
            logger.error(f"Moderation：{prompt}:{e}")
            _harm = False
        return _harm

    def pre_check(self):
        # Flood
        if Utils.WaitFlood(user=self.user, group=self.group):
            return False, "TOO FAST"
        _Usage = self._UsageManager.isOutUsage()
        if _Usage["status"]:
            return False, f"小时额度或者单人总额度用完，请申请重置或等待\n{_Usage['use']}"
        return True, ""

    async def load_response(self,
                            conversation: Conversation = None,
                            prompt: PromptManager = None,
                            method: str = "chat") -> str:
        """
        发起请求
        :param conversation:
        :param prompt:
        :param method:
        :return:
        """
        load_csonfig()
        # 关键检查
        status, log = self.pre_check()
        if not status:
            return log

        receiver = llm_kira.client
        if not self.api_key:
            logger.error("Api Check:Api Key pool empty")
            raise LoadResponseError("Found:Api Key pool empty")

        prompt_text = prompt.run()
        prompt_raw = prompt.run(raw_list=True) if prompt.run(raw_list=True) else [""]
        prompt_index = prompt_raw[-1]

        # 长度限定
        # if Utils.tokenizer(str(prompt_text)) > _csonfig['input_limit']:
        #     return "TOO LONG"

        # 内容安全策略
        _harm = await self.openai_moderation(prompt=prompt_text)
        if _harm:
            _info = DefaultData.getRefuseAnswer()
            await asyncio.sleep(random.randint(3, 6))
            return f"{_info}\nI think you talk too {_harm}."

        # 初始化记忆管理器
        Mem = receiver.MemoryManager(profile=conversation)
        llm = llm_kira.client.llms.OpenAi(
            profile=conversation,
            api_key=self.api_key,
            call_func=OPENAI_API_KEY_MANAGER.check_api_key,
            token_limit=MODEL_TOKEN_LIMIT,
            auto_penalty=not _csonfig["auto_adjust"],
        )

        try:
            # 分发类型
            if method == "write":
                _head, _body = Utils.get_head_foot(prompt_index)
                # OPENAI
                response = await llm_kira.openai.Completion(api_key=self.api_key,
                                                            call_func=OPENAI_API_KEY_MANAGER.check_api_key).create(
                    model=MODEL_NAME,
                    prompt=str(_body),
                    temperature=0.2,
                    frequency_penalty=1,
                    max_tokens=int(_csonfig["token_limit"])
                )
                _deal = rqParser.get_response_text(response)[0]
                _usage = rqParser.get_response_usage(response)
                logger.success(
                    f"Write:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {_body} --req: {_deal}"
                )
            elif method == "catch":
                llm.token_limit = 1000
                llm.auto_penalty = False
                chat_client = receiver.ChatBot(profile=conversation,
                                               memory_manger=Mem,
                                               optimizer=Optimizer.MatrixPoint,
                                               llm_model=llm
                                               )
                response = await chat_client.predict(
                    llm_param=OpenAiParam(model_name=MODEL_NAME),
                    prompt=prompt,
                    predict_tokens=150
                )
                prompt.clean()
                _deal = response.reply
                _usage = response.llm.usage
                logger.success(
                    f"CHAT:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {prompt_text} --req: {_deal} ")

            elif method == "chat":
                _head = None
                if _csonfig.get("allow_change_head"):
                    _head = Header(uid=self.user).get()
                    _head = ContentDfa.filter_all(_head)
                    if len(_head) < 6:
                        _head = None
                _style = None
                if _csonfig.get("allow_change_style"):
                    _style = Style(uid=self.user).get()
                    if len(_style) < 10:
                        _style = None

                chat_client = receiver.ChatBot(profile=conversation,
                                               memory_manger=Mem,
                                               optimizer=Optimizer.SinglePoint,
                                               llm_model=llm)
                prompt: PromptManager
                prompt.template = _head
                webSupport = ""
                if 4 < len(prompt_text) < 35:
                    _head, _body = Utils.get_head_foot(prompt_index)
                    webSupport = await receiver.enhance.PluginSystem(plugin_table=PLUGIN_TABLE,
                                                                     prompt=_body).run()
                    webSupport = webSupport[:900]
                response = await chat_client.predict(
                    llm_param=OpenAiParam(model_name=MODEL_NAME, logit_bias=_style,
                                          # presence_penalty=0.3,
                                          # frequency_penalty=0.3
                                          ),
                    prompt=prompt,
                    predict_tokens=int(_csonfig["token_limit"]),
                    increase=webSupport
                )
                prompt.clean()
                # print(response)
                _deal = response.reply
                _usage = response.llm.usage
                logger.success(
                    f"CHAT:{self.user}:{self.group} --time: {int(time.time() * 1000)} --prompt: {prompt_text} --req: {_deal} ")
            else:
                return "NO SUPPORT METHOD"
        except Exception as e:
            logger.error(f"RUN:Api Error:{e}")
            _usage = 0
            e = str(e)
            _error_type = "Api Error"
            if "overload" in e:
                _error_type = "Api Overload Now"
            if "had an error while processing" in e:
                _error_type = "Server Error While Processing Your Prompt"
            _deal = f"{DefaultData.getWaitAnswer()}\nDetails:{_error_type}"
        # 更新额度
        _AnalysisUsage = self._UsageManager.renewUsage(usage=_usage)
        # 更新统计
        DefaultData().setAnalysis(usage={f"{self.user}": _AnalysisUsage.total_usage})
        # 人性化处理
        _deal = ContentDfa.filter_all(_deal)
        _deal = Utils.Humanization(_deal)
        return _deal


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


async def RemindSet(user_id, text) -> PublicReturn:
    """
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
        _remind = _remind.replace("你", "ME*")
        _remind = _remind.replace("我", "YOU*")
        _remind = _remind.replace("YOU*", "你")
        _remind = _remind.replace("ME*", "我")
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
        return PublicReturn(status=True,
                            trace="WhiteGroupCheck",
                            msg=_white_user_check.msg)

    # 线性决策
    if _text.startswith("/remind"):
        _remind_set = await RemindSet(user_id=_user_id, text=_text)
        _remind_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Remind",
                            msg=_remind_set.msg)

    if _text.startswith("/style"):
        _style_set = await StyleSet(user_id=_user_id, text=_text)
        _style_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Style",
                            msg=_style_set.msg)

    if _text.startswith("/forgetme"):
        await Forget(user_id=_user_id, chat_id=_chat_id)
        return PublicReturn(status=True, msg=f"Down,Miss you", trace="ForgetMe")

    if _text.startswith("/voice"):
        _user_manger = UserManager(_user_id)
        _set = True
        if _user_manger.read("voice"):
            _set = False
        _user_manger.save({"voice": _set})
        return PublicReturn(status=True, msg=f"TTS:{_set}", trace="VoiceSet")

    # Prompt 创建
    _prompt_type = await PromptType(text=_text, types="group")
    _prompt_type: PublicReturn
    if not _prompt_type.status:
        # 预处理失败，不符合任何触发条件，不回复捏
        return PublicReturn(status=False, msg=f"No Match Type", trace="PromptPreprocess")
    _cid = DefaultData.composing_uid(user_id=_user_id,
                                     chat_id=_chat_id) if _prompt_type.data != "catch" else _chat_id
    start_name = DefaultData.name_split(sentence=_user_name, limit=10)
    restart_name = DefaultData.name_split(sentence=_bot_name, limit=10)
    conversation = llm_kira.client.Conversation(
        start_name=start_name,
        restart_name=restart_name,
        conversation_id=int(_cid),
    )
    promptManager = llm_kira.client.PromptManager(profile=conversation, connect_words="\n")

    # 构建
    for item in _prompt:
        item = str(item)
        start = conversation.start_name
        if ":" in item:
            start = ""
        if item.startswith("/"):
            _split_prompt = item.split(" ", 1)
            if len(_split_prompt) > 1:
                item = _split_prompt[1]
        # 内容过滤
        item = ContentDfa.filter_all(item)
        promptManager.insert(item=PromptItem(start=start, text=str(item)))
    try:
        _client = Reply(user=_user_id,
                        group=_chat_id,
                        api_key=OPENAI_API_KEY_MANAGER.get_key())
        _req = await _client.load_response(
            conversation=conversation,
            prompt=promptManager,
            method=_prompt_type.data
        )
        # message_type = "text"
        _info = []
        # 语音消息
        _voice = UserManager(_user_id).read("voice")
        voice_data = None
        if _voice:
            voice_data = await TTSSupportCheck(text=_req, user_id=_user_id)
        if _voice and not voice_data:
            _info.append("TTS Unavailable")
        # message_type = "voice" if _voice and voice_data else message_type
        # f"{_req}\n{config.INTRO}\n{''.join(_info)}"
        _log = '\n'.join(_info)
        return PublicReturn(status=True, msg=f"OK", trace="Reply", voice=voice_data, reply=f"{_req}\n{_log}")
    except LoadResponseError as e:
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply=f"Error Occur --{e}")
    except Exception as e:
        logger.error(e)
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply="Error Occur~Maybe Api request rate limit~nya")


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
        return PublicReturn(status=True,
                            trace="WhiteGroupCheck",
                            msg=_white_user_check.msg)

    # 线性决策
    if _text.startswith("/remind"):
        _remind_set = await RemindSet(user_id=_user_id, text=_text)
        _remind_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Remind",
                            msg=_remind_set.msg)

    if _text.startswith("/style"):
        _style_set = await StyleSet(user_id=_user_id, text=_text)
        _style_set: PublicReturn
        return PublicReturn(status=True,
                            trace="Style",
                            msg=_style_set.msg)

    if _text.startswith("/forgetme"):
        await Forget(user_id=_user_id, chat_id=_chat_id)
        return PublicReturn(status=True, msg=f"Down,Miss you", trace="ForgetMe")

    if _text.startswith("/voice"):
        _user_manger = UserManager(_user_id)
        _set = True
        if _user_manger.read("voice"):
            _set = False
        _user_manger.save({"voice": _set})
        return PublicReturn(status=True, msg=f"TTS:{_set}", trace="Voice")

    # logger.info(_prompt)
    # Prompt 创建
    _prompt_type = await PromptType(text=_text, types="private")
    _prompt_type: PublicReturn
    if not _prompt_type.status:
        # 预处理失败，不符合任何触发条件，不回复捏
        return PublicReturn(status=False, msg=f"No Match Type", trace="PromptPreprocess")
    _cid = DefaultData.composing_uid(user_id=_user_id,
                                     chat_id=_chat_id) if _prompt_type.data != "catch" else _chat_id
    start_name = DefaultData.name_split(sentence=_user_name, limit=10)
    restart_name = DefaultData.name_split(sentence=_bot_name, limit=10)
    conversation = llm_kira.client.Conversation(
        start_name=start_name,
        restart_name=restart_name,
        conversation_id=int(_cid),
    )
    # 构建
    promptManager = llm_kira.client.PromptManager(profile=conversation, connect_words="\n")
    # 构建
    for item in _prompt:
        item = str(item)
        start = conversation.start_name
        if ":" in item:
            start = ""
        if item.startswith("/"):
            _split_prompt = item.split(" ", 1)
            if len(_split_prompt) > 1:
                item = _split_prompt[1]
        # 内容过滤
        item = ContentDfa.filter_all(item)
        promptManager.insert(item=PromptItem(start=start, text=str(item)))

    try:
        _client = Reply(user=_user_id,
                        group=_chat_id,
                        api_key=OPENAI_API_KEY_MANAGER.get_key())
        _req = await _client.load_response(
            conversation=conversation,
            prompt=promptManager,
            method=_prompt_type.data
        )
        # message_type = "text"
        _info = []
        # 语音消息
        _voice = UserManager(_user_id).read("voice")
        voice_data = None
        if _voice:
            voice_data = await TTSSupportCheck(text=_req, user_id=_user_id)
        if not voice_data and _voice:
            _info.append("TTS Unavailable")
        # message_type = "voice" if _voice and voice_data else message_type
        # f"{_req}\n{config.INTRO}\n{''.join(_info)}"
        _log = '\n'.join(_info)
        return PublicReturn(status=True, msg=f"OK", trace="Reply", voice=voice_data, reply=f"{_req}\n{_log}")
    except LoadResponseError as e:
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply=f"Error Occur --{e}")
    except Exception as e:
        logger.error(e)
        return PublicReturn(status=True, msg=f"OK", trace="Error", reply="Error Occur~Maybe Api request rate limit~nya")


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
Use /chat + 句子 启动消息流，只需要回复即可交谈。48小时前的消息不能回复。
Use /write +句子 进行空白的续写。
Use /remind 设置一个场景头，全程不会被裁剪。
Use /forgetme 遗忘过去，res history。
Use /voice 开启可能的 tts 支持。
Use /trigger Admin 可以开启主动回复模式。
Use /style 定制词汇风格，中文效果较弱，(增强),[减弱]。
"""
