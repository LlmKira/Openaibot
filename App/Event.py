# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Event.py
# @Software: PyCharm
# @Github    ：sudoskys
import json
import pathlib
import random
import time
from typing import Union
from loguru import logger

import openai_async
# from App.chatGPT import PrivateChat
from utils.Base import ReadConfig
from utils.Chat import Utils, Usage, rqParser, GroupManger, UserManger, Header
from utils.Data import DictUpdate, DefaultData, Api_keys, Service_Data
from utils.TTS import TTS_Clint, TTS_REQ
from utils.Detect import DFA, Censor

_service = Service_Data.get_key()
_redis_conf = _service["redis"]
_tts_conf = _service["tts"]
openai_async.redis = openai_async.RedisConfig(**_redis_conf)

urlForm = {
    "Danger.form": [
        "https://raw.githubusercontent.com/fwwdn/sensitive-stop-words/master/%E6%94%BF%E6%B2%BB%E7%B1%BB.txt",
        "https://raw.githubusercontent.com/TelechaBot/AntiSpam/main/Danger.txt"
    ]
}


def InitCensor():
    config = ReadConfig().parseFile(str(pathlib.Path.cwd()) + "/Config/app.toml")
    if config.proxy.status:
        proxies = {
            'all://': config.proxy.url,
        }  # 'http://127.0.0.1:7890'  # url
        return Censor.InitWords(url=urlForm, home_dir="./Data/", proxy=proxies)
    else:
        return Censor.InitWords(url=urlForm, home_dir="./Data/")


if not pathlib.Path("./Data/Danger.form").exists():
    InitCensor()
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
    with open("./Config/config.json", "w+", encoding="utf8") as f:
        json.dump(_csonfig, f, indent=4, ensure_ascii=False)


def TTS_Support_Check(text, user_id):
    """
    处理消息文本并构造请求返回字节流或者空。隶属 Event 文件
    :return:
    """
    if not _tts_conf["status"]:
        return
    if _tts_conf["type"] == "vits":
        from openai_async.utils.Talk import Talk
        if Talk.get_language(text) != "chinese":
            return
        if len(text) > _tts_conf["vits"]["limit"]:
            return
        _new_text = f"[ZH]{text}[ZH]"
        result = TTS_Clint.request_vits_server(url=_tts_conf["vits"]["api"],
                                               params=TTS_REQ(task_id=user_id,
                                                              text=_new_text,
                                                              model_name=_tts_conf["vits"]["model_name"],
                                                              speaker_id=_tts_conf["vits"]["speaker_id"]))
        if not result:
            print("TTS failed")
            return
        try:
            data = TTS_Clint.decode_wav(result["audio"])
        except:
            print("decode tts data failed")
            return
        return data
    return


async def Forget(bot, message, config):
    """
    重置消息流
    :param bot:
    :param message:
    :param config:
    :return:
    """
    from openai_async.utils.data import MsgFlow
    _cid = DefaultData.composing_uid(user_id=message.from_user.id, chat_id=message.chat.id)
    return MsgFlow(uid=_cid).forget()


class Reply(object):
    """
    群组
    """

    @staticmethod
    async def load_response(user, group,
                            key: Union[str, list],
                            prompt: str = "Say this is a test",
                            userlimit: int = None,
                            method: str = "chat",
                            start_name: str = "Ai:",
                            restart_name: str = "Human:",
                            web_enhance_server: list = None
                            ):
        """
        发起请求
        :param web_enhance_server:
        :param start_name: 称呼自己
        :param restart_name: 称呼请求发起人
        :param user:
        :param group:
        :param key:
        :param prompt:
        :param userlimit:
        :param method:
        :return:
        """
        load_csonfig()
        # 载入全局变量
        if not key:
            logger.error("SETTING:API key missing")
            raise Exception("API key missing")
        # 长度限定
        if _csonfig["input_limit"] < len(str(prompt)) / 4:
            return "TOO LONG"
        # 内容审计
        if ContentDfa.exists(str(prompt)):
            _censor_child = ["你说啥呢？", "我不说,", "不懂年轻人,", "6 ", "我不好说，", "害怕，", "这是理所当然的，",
                             "我可以说的是……", "我想说的是……", "我想强调的是……", "我想补充的是……", "我想指出的是……",
                             "我想重申的是……", "我想强调的是……""什么事儿呀，", "是啊，是啊。", "你猜啊，", "就是啊，",
                             "哎呀，真的吗？",
                             "啊哈哈哈。", "你知道的。"]
            _censor = ["有点离谱，不想回答", "累了，歇会儿", "能不能换个话题？", "我不想说话。", "没什么好说的。",
                       "现在不是说话的时候。", "我没有什么可说的。", "我不喜欢说话。",
                       "我不想接受问题。", "我不喜欢被问问题。", "我觉得这个问题并不重要。", "我不想谈论这个话题。",
                       "我不想对这个问题发表意见。"]
            _info = f"{random.choice(_censor_child)} {random.choice(_censor)} --"
            return _info
        # 洪水防御攻击
        if Utils.WaitFlood(user=user, group=group, usercold_time=userlimit):
            return "TOO FAST"
        # 用量检测
        _UsageManger = Usage(uid=user)
        _Usage = _UsageManger.isOutUsage()
        if _Usage["status"]:
            return f"小时额度或者单人总额度用完，请申请重置或等待\n{_Usage['use']}"
        # 请求
        try:
            # import openai_async
            openai_async.api_key = key
            # Openai_python
            # import openai
            # openai.api_key = key
            # response = openai.Completion.create(model="text-davinci-003", prompt=str(prompt), temperature=0,
            #                                     max_tokens=int(_csonfig["token_limit"]))
            if method == "write":
                # OPENAI
                response = await openai_async.Completion(call_func=Api_keys.pop_api_key).create(
                    model="text-davinci-003",
                    prompt=str(prompt),
                    temperature=0.2,
                    frequency_penalty=1,
                    max_tokens=int(_csonfig["token_limit"])
                )
            elif method == "chat":
                # CHAT
                from openai_async import Chat
                _cid = DefaultData.composing_uid(user_id=user, chat_id=group)
                # 启用单人账户桶
                if len(start_name) > 12:
                    start_name = start_name[-10:]
                if len(restart_name) > 12:
                    restart_name = restart_name[-10:]
                receiver = Chat.Chatbot(
                    conversation_id=int(_cid),
                    call_func=Api_keys.pop_api_key,
                    start_sequ=start_name,
                    restart_sequ=restart_name,
                )
                _head = Header(uid=user).get()
                if _head:
                    _head = ContentDfa.filter_all(_head)
                response = await receiver.get_chat_response(model="text-davinci-003",
                                                            prompt=str(prompt),
                                                            max_tokens=int(_csonfig["token_limit"]),
                                                            role=_head,
                                                            web_enhance_server=web_enhance_server
                                                            )
            else:
                return "NO SUPPORT METHOD"
            # print(response)
            _deal_rq = rqParser.get_response_text(response)
            # print(_deal_rq)
            _deal = _deal_rq[0]
            _usage = rqParser.get_response_usage(response)
            _time = int(time.time() * 1000)
            logger.info(f"RUN:{user}:{group} --time: {_time} --prompt: {prompt} --req: {_deal} ")
        except Exception as e:
            logger.error(f"RUN:Api Error:{e}")
            _usage = 0
            _deal = f"Api Outline or too long prompt \n {prompt}"
        # 更新额度
        _AnalysisUsage = _UsageManger.renewUsage(usage=_usage)
        # 统计
        DefaultData().setAnalysis(usage={f"{user}": _AnalysisUsage.total_usage})
        _deal = ContentDfa.filter_all(_deal)
        # 人性化处理
        _deal = Utils.Humanization(_deal)
        return _deal


async def WhiteUserCheck(bot, message, WHITE: str = ""):
    """

    :param bot: 机器人对象
    :param message: 消息流
    :param WHITE: 白名单提示
    :return:
    """
    if UserManger(message.from_user.id).read("block"):
        await bot.send_message(message.chat.id,
                               f"You are blocked!...\n\n{WHITE}")
        return
    if _csonfig.get("whiteUserSwitch"):
        # 没有在白名单里！
        if not UserManger(message.from_user.id).read("white"):
            try:
                await bot.reply_to(message, f"{message.from_user.id}:Check the settings to find that you is not "
                                            f"whitelisted!...{WHITE}")
            except Exception as e:
                logger.error(e)
            finally:
                return True
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True
    return False


async def WhiteGroupCheck(bot, message, WHITE):
    if GroupManger(message.chat.id).read("block"):
        await bot.reply_to(message, f"Group{message.chat.id} is blocked!...\n\n{WHITE}")
        return True
    if _csonfig.get("whiteGroupSwitch"):
        # 没有在白名单里！
        if not GroupManger(message.chat.id).read("white"):
            try:
                await bot.reply_to(message, f"Group {message.chat.id} is not whitelisted!...\n\n{WHITE}")
            except Exception as e:
                logger.error(e)
            finally:
                logger.info(f"RUN:non-whitelisted groups:{abs(message.chat.id)}")
                return True  # await bot.leave_chat(message.chat.id)
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True
    return False


async def Text(bot, message, config, reset: bool = False):
    load_csonfig()
    # 拿到 prompt
    _prompt = message.text
    types = "chat"
    if message.text.startswith("/forgetme"):
        await Forget(bot, message, config)
        return await bot.reply_to(message, f"Down,Miss you")
    if message.text.startswith("/chat"):
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
        types = "chat"
    if message.text.startswith("/write"):
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
        types = "write"
    if message.text.startswith("/remind"):
        _remind_r = message.text.split(" ", 1)
        if len(_remind_r) < 2:
            return
        _remind = _remind_r[1]
        if Utils.tokenizer(_remind) > 333:
            return await bot.reply_to(message, f"过长:{_remind}")
        if _csonfig["allow_change_head"]:
            # _remind = _remind.replace("你是", "ME*扮演")
            _remind = _remind.replace("你", "ME*")
            _remind = _remind.replace("我", "YOU*")
            _remind = _remind.replace("YOU*", "你")
            _remind = _remind.replace("ME*", "我")
            await bot.reply_to(message, f"设定:{_remind}\nNo reply this msg")
            Header(uid=message.from_user.id).set(_remind)
        else:
            await bot.reply_to(message, f"禁止设定")
            Header(uid=message.from_user.id).set({})
        return True
    # 处理是否忘记
    if reset:
        await Forget(bot, message, config)
    else:
        # 加判定上文是否为此人的消息
        if not str(Utils.checkMsg(f"{message.chat.id}{message.reply_to_message.id}")) == f"{message.from_user.id}":
            # 不是，那就傲娇点
            return
    # 启动状态
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return
    # 群组白名单检查
    if await WhiteGroupCheck(bot, message, config.WHITE):
        return
    try:
        # 自动获取名字
        _name = f"{message.from_user.first_name}{message.from_user.last_name}"
        if len(_name) > 12 and len(f"{message.from_user.last_name}") < 6:
            _name = f"{message.from_user.last_name}"
        _req = await Reply.load_response(user=message.from_user.id,
                                         group=message.chat.id,
                                         key=Api_keys.get_key("./Config/api_keys.json")["OPENAI_API_KEY"],
                                         prompt=_prompt,
                                         method=types,
                                         restart_name=_name,
                                         start_name="Girl:",
                                         web_enhance_server=config.Enhance_Server
                                         )
        voice = TTS_Support_Check(text=_req, user_id=message.from_user.id)
        if voice:
            if not message.chat.is_forum:
                msg = await bot.send_audio(chat_id=message.chat.id, audio=voice, title="Voice")
            else:
                detect = await bot.reply_to(message, f"{_req}")
                msg = await bot.send_audio(chat_id=message.chat.id,
                                           message_thread_id=detect.message_thread_id,
                                           audio=voice,
                                           title="Voice")
        else:
            msg = await bot.reply_to(message, f"{_req}\n{config.INTRO}")
        Utils.trackMsg(f"{message.chat.id}{msg.id}", user_id=message.from_user.id)
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Error Occur~Maybe Api request rate limit~nya")


async def private_Chat(bot, message, config):
    load_csonfig()
    # 处理初始化
    types = "chat"
    _prompt = message.text
    if message.text.startswith("/chat"):
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
        types = "chat"
    if message.text.startswith("/write"):
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
        types = "write"
    if message.text.startswith("/forgetme"):
        await Forget(bot, message, config)
        return await bot.reply_to(message, f"Down,Miss you")
    # 处理机器人开关
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return
    # 白名单用户检查
    if await WhiteUserCheck(bot, message, config.WHITE):
        return
    try:
        if len(_prompt) > 1:
            _name = f"{message.from_user.first_name}{message.from_user.last_name}"
            if len(_name) > 12 and len(f"{message.from_user.last_name}") < 6:
                _name = f"{message.from_user.last_name}"
            _req = await Reply.load_response(user=message.from_user.id,
                                             group=message.chat.id,
                                             key=Api_keys.get_key("./Config/api_keys.json")["OPENAI_API_KEY"],
                                             prompt=_prompt,
                                             restart_name=_name,
                                             start_name="Girl:",
                                             method=types,
                                             web_enhance_server=config.Enhance_Server
                                             )
            voice = TTS_Support_Check(text=_req, user_id=message.from_user.id)
            if voice:
                if not message.chat.is_forum:
                    msg = await bot.send_audio(chat_id=message.chat.id, audio=voice, title="Voice")
                else:
                    detect = await bot.reply_to(message, f"{_req}\n{config.INTRO}")
                    msg = await bot.send_audio(chat_id=message.chat.id,
                                               message_thread_id=detect.message_thread_id,
                                               audio=voice,
                                               title="Voice")
            else:
                msg = await bot.reply_to(message, f"{_req}\n{config.INTRO}")
            # await bot.reply_to(message, f"{_req}\n{config.INTRO}")
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Error Occur~Maybe Api request rate limit~nya")


async def Friends(bot, message, config):
    load_csonfig()
    command = message.text
    if command.startswith("/remind"):
        _remind_r = message.text.split(" ", 1)
        if len(_remind_r) < 2:
            return
        _remind = _remind_r[1]
        if Utils.tokenizer(_remind) > 333:
            return await bot.reply_to(message, f"过长:{_remind}")
        _remind = ContentDfa.filter_all(_remind)
        if _csonfig["allow_change_head"]:
            # _remind = _remind.replace("你是", "ME*扮演")
            _remind = _remind.replace("你", "ME*")
            _remind = _remind.replace("我", "YOU*")
            _remind = _remind.replace("YOU*", "你")
            _remind = _remind.replace("ME*", "我")
            await bot.reply_to(message, f"设定:{_remind}\nNo reply this msg")
            Header(uid=message.from_user.id).set(_remind)
        else:
            await bot.reply_to(message, f"禁止设定")
            Header(uid=message.from_user.id).set({})
        return
        # 启动函数
    if command.startswith("/chat") or command.startswith("/forgetme") or command.startswith(
            "/write") or not command.startswith("/"):
        await private_Chat(bot, message, config)


async def Master(bot, message, config):
    load_csonfig()
    if message.from_user.id in config.master:
        try:
            command = message.text
            # SET
            if command.startswith("/set_user_cold"):
                # 用户冷静时间
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["usercold_time"] = int(_len_)
                    await bot.reply_to(message, f"user cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset user cold time limit to{_len_}")

            if command.startswith("/set_group_cold"):
                # 群组冷静时间
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["groupcold_time"] = int(_len_)
                    await bot.reply_to(message, f"group cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset group cold time limit to{_len_}")

            if command.startswith("/set_per_user_limit"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["per_user_limit"] = int(_len_)
                    await bot.reply_to(message, f"set_hour_limit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset per_user_limit to{_len_}")

            if command.startswith("/set_per_hour_limit"):
                # 设定用户小时用量
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["hour_limit"] = int(_len_)
                    await bot.reply_to(message, f"hour_limit:{_len_}")
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
                    UserManger(__user_id).save({"usage": __limit})
                    await bot.reply_to(message, f"user_limit:{__limit}")
                    logger.info(f"SETTING:promote user_limit to{__limit}")

            if command.startswith("/reset_user_usage"):
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        Usage(uid=_len_).resetTotalUsage()
                        logger.info(f"SETTING:resetTotalUsage {_len_} limit to 0")
                        await bot.reply_to(message, f"hour_limit:{_len}")

            if command.startswith("/set_token_limit"):
                # 返回多少？
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["token_limit"] = int(_len_)
                    await bot.reply_to(message, f"tokenlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset tokenlimit limit to{_len_}")

            if command.startswith("/set_input_limit"):
                # 输入字符？
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["input_limit"] = int(_len_)
                    await bot.reply_to(message, f"input limit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset input limit to{_len_}")

            if command == "/config":
                # 配置文件
                save_csonfig()
                path = str(pathlib.Path().cwd()) + "/" + "Config/config.json"
                if pathlib.Path(path).exists():
                    doc = open(path, 'rb')
                    await bot.send_document(message.chat.id, doc)
                else:
                    await bot.reply_to(message, "没有找到配置文件")

            if "/add_block_group" in command:
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add block group {_len_}"
                        GroupManger(int(_len_)).save({"block": True})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            if "/del_block_group" in command:
                # 重置用户的用量总数据
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del block group {_len_}"
                        GroupManger(int(_len_)).save({"block": False})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            if "/add_block_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_block_userp {_len_}"
                        UserManger(int(_len_)).save({"block": True})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            if "/del_block_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_block_user {_len_}"
                        UserManger(int(_len_)).save({"block": False})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            # whiteGroup
            if "/add_white_group" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_white_group {_len_}"
                        GroupManger(int(_len_)).save({"white": True})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            if "/del_white_group" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_white_group {_len_}"
                        GroupManger(int(_len_)).save({"white": False})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            # whiteUser
            if "/add_white_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:add_white_user {_len_}"
                        UserManger(int(_len_)).save({"white": True})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            if "/del_white_user" in command:
                _len = Utils.extract_arg(command)
                for i in _len:
                    _len_ = "".join(list(filter(str.isdigit, i)))
                    if _len_:
                        _ev = f"SETTING:del_white_user {_len_}"
                        UserManger(int(_len_)).save({"white": False})
                        await bot.reply_to(message, _ev)
                        logger.info(_ev)

            # UPDATE
            if command == "/update_detect":
                keys, _error = InitCensor()
                if _error:
                    error = '\n'.join(_error)
                    errors = f"Error:\n{error}"
                else:
                    # 重载 Danger 库
                    ContentDfa.change_words(path="./Data/Danger.form")
                    errors = "Success"
                if message:
                    await bot.reply_to(message, f"{'|'.join(keys)}\n\n{errors}")

            # USER White
            if command == "/open_user_white_mode":
                _csonfig["whiteUserSwitch"] = True
                await bot.reply_to(message, "SETTING:whiteUserSwitch ON")
                save_csonfig()
                logger.info("SETTING:whiteUser ON")

            if command == "/close_user_white_mode":
                _csonfig["whiteUserSwitch"] = False
                await bot.reply_to(message, "SETTING:whiteUserSwitch OFF")
                save_csonfig()
                logger.info("SETTING:whiteUser OFF")

            # GROUP White
            if command == "/open_group_white_mode":
                _csonfig["whiteGroupSwitch"] = True
                await bot.reply_to(message, "ON:whiteGroup")
                save_csonfig()
                logger.info("SETTING:whiteGroup ON")

            if command == "/close_group_white_mode":
                _csonfig["whiteGroupSwitch"] = False
                await bot.reply_to(message, "SETTING:whiteGroup OFF")
                save_csonfig()
                logger.info("SETTING:whiteGroup OFF")

            if command == "/see_api_key":
                keys = Api_keys.get_key("./Config/api_keys.json")
                # 脱敏
                _key = []
                for i in keys["OPENAI_API_KEY"]:
                    _key.append(DefaultData.mask_middle(i, 10))
                _info = '\n'.join(_key)
                await bot.reply_to(message, f"Now Have \n{_info}")

            if "/add_api_key" in command:
                _parser = Utils.extract_arg(command)
                if _parser:
                    Api_keys.add_key(key=str(_parser[0]).strip())
                logger.info("SETTING:ADD API KEY")
                await bot.reply_to(message, "SETTING:ADD API KEY")

            if "/del_api_key" in command:
                _parser = Utils.extract_arg(command)
                if _parser:
                    Api_keys.pop_key(key=str(_parser[0]).strip())
                logger.info("SETTING:DEL API KEY")
                await bot.reply_to(message, "SETTING:DEL API KEY")
            if "/enable_change_head" in command:
                _csonfig["allow_change_head"] = True
                await bot.reply_to(message, "SETTING:allow_change_head ON")
                save_csonfig()
                logger.info("SETTING:BOT ON")

            if "/disable_change_head" in command:
                _csonfig["allow_change_head"] = False
                await bot.reply_to(message, "SETTING:allow_change_head OFF")
                save_csonfig()
                logger.info("SETTING:BOT ON")

            if command == "/open":
                _csonfig["statu"] = True
                await bot.reply_to(message, "SETTING:BOT ON")
                save_csonfig()
                logger.info("SETTING:BOT ON")

            if command == "/close":
                _csonfig["statu"] = False
                await bot.reply_to(message, "SETTING:BOT OFF")
                save_csonfig()
                logger.info("SETTING:BOT OFF")
        except Exception as e:
            logger.error(e)


async def Start(bot, message, config):
    await bot.reply_to(message, f"Ping，Use /chat start a new chat loop")


async def About(bot, message, config):
    await bot.reply_to(message, f"{config.ABOUT}")


async def Help(bot, message, config):
    await bot.reply_to(message, f"""
Use /chat + 句子 启动消息流，只需要回复即可交谈。48小时前的消息不能回复。
Use /write +句子 进行空白的续写。
Use /remind 设置一个场景头，全程不会被裁剪。
Use /forgetme 遗忘过去，res history。
""")
