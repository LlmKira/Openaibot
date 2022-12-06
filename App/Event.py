# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Event.py
# @Software: PyCharm
# @Github    ：sudoskys
import json
import pathlib
import time
from typing import Union

# from App.chatGPT import PrivateChat
from utils.Base import ReadConfig
from utils.Data import DataWorker, DictUpdate, DefaultData
from utils.Detect import DFA, Censor

from utils.Base import Logger

logger = Logger()

# 工具数据类型
DataUtils = DataWorker(prefix="Open_Ai_bot_")
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
global Group_Msg


def init_Msg():
    global Group_Msg
    Group_Msg = {}
    return Group_Msg


init_Msg()


# IO
def load_csonfig():
    global _csonfig
    with open("./Config/config.json", encoding="utf-8") as f:
        _csonfig = json.load(f)
        now_table = DefaultData.defaultConfig()
        DictUpdate.dict_update(now_table, _csonfig)
        return now_table


def save_csonfig():
    with open("./Config/config.json", "w", encoding="utf8") as f:
        json.dump(_csonfig, f, indent=4, ensure_ascii=False)


class rqParser(object):
    @staticmethod
    def get_response_text(response):
        REPLY = []
        Choice = response.get("choices")
        if Choice:
            for item in Choice:
                _text = item.get("text")
                REPLY.append(_text)
        if not REPLY:
            REPLY = ["Nothing to say:response null~"]
        return REPLY

    @staticmethod
    def get_response_usage(response):
        usage = len("机器资源")
        if response.get("usage"):
            usage = response.get("usage").get("total_tokens")
        return usage


class Usage(object):
    @staticmethod
    def isOutUsage(user):
        """
        累计
        :param user:
        :return: bool
        """
        # 时间
        key_time = int(time.strftime("%Y%m%d%H", time.localtime()))
        GET = DataUtils.getKey(f"usage_{user}_{key_time}")
        if GET:
            if GET >= 60000:
                return {"status": True, "use": GET, "uid": key_time}
            else:
                return {"status": False, "use": GET, "uid": key_time}
        else:
            GET = 0
            DataUtils.setKey(f"usage_{user}_{key_time}", GET)
            return {"status": False, "use": GET, "uid": key_time}

    @staticmethod
    def renewUsage(user, usage, father):
        GET = father["use"]
        key_time = father['uid']
        GET = GET + usage
        DataUtils.setKey(f"usage_{user}_{key_time}", GET)
        # double req in 3 seconds
        return True

    @staticmethod
    def upMsg(user, usage, father):
        GET = father["use"]
        key_time = father['uid']
        GET = GET + usage
        DataUtils.setKey(f"usage_{user}_{key_time}", GET)
        # double req in 3 seconds
        return True


class Utils(object):
    @staticmethod
    def forget_me(user_id, group_id):
        from openai_async.utils.data import MsgFlow
        _cid = DefaultData.composing_uid(user_id=user_id, chat_id=group_id)
        return MsgFlow(uid=_cid).forget()

    @staticmethod
    def extract_arg(arg):
        return arg.split()[1:]

    @staticmethod
    def Humanization(strs):
        return strs.lstrip('？?!！：。')

    @staticmethod
    def WaitFlood(user, group, usercold_time: int = None, groupcold_time: int = None):
        if usercold_time is None:
            usercold_time = _csonfig["usercold_time"]
        if groupcold_time is None:
            groupcold_time = _csonfig["groupcold_time"]
        if DataUtils.getKey(f"flood_user_{user}"):
            # double req in 3 seconds
            return True
        else:
            if _csonfig["usercold_time"] > 1:
                DataUtils.setKey(f"flood_user_{user}", "FAST", exN=usercold_time)
        # User
        if DataUtils.getKey(f"flood_group_{group}"):
            # double req in 3 seconds
            return True
        else:
            if _csonfig["groupcold_time"] > 1:
                DataUtils.setKey(f"flood_group_{group}", "FAST", exN=groupcold_time)
        return False

    @staticmethod
    def checkMsg(msg_uid):
        global Group_Msg
        if Group_Msg is None:
            Group_Msg = {}
        if len(Group_Msg) > 5000:
            Group_Msg = Group_Msg[5000:]  # 如果字典中的键数量超过了最大值，则删除一些旧的键
            # print(Group_Msg)
        return Group_Msg.get(str(msg_uid))

    @staticmethod
    def trackMsg(msg_uid, user_id):
        global Group_Msg
        if Group_Msg is None:
            Group_Msg = {}
        if len(Group_Msg) > 5000:
            Group_Msg = Group_Msg[5000:]  # 如果字典中的键数量超过了最大值，则删除一些旧的键
        Group_Msg[str(msg_uid)] = user_id
        # print(Group_Msg)


class GroupChat(object):
    @staticmethod
    async def load_group_response(user, group, key: Union[str, list], prompt: str = "Say this is a test",
                                  userlimit: int = None):
        if not key:
            logger.error("SETTING:API key missing")
            raise Exception("API key missing")
        # 长度限定
        if _csonfig["input_limit"] < len(str(prompt)) / 4:
            return "TOO LONG"

        # 内容审计
        if ContentDfa.exists(str(prompt)):
            return "I am a robot and not fit to answer dangerous content."

        # 洪水防御攻击
        if Utils.WaitFlood(user=user, group=group, usercold_time=userlimit):
            return "TOO FAST"

        # 用量检测
        _Usage = Usage.isOutUsage(user)
        if _Usage["status"]:
            return "OUT OF USAGE"
        # 请求
        try:
            # Openai_python
            # import openai
            # openai.api_key = key
            # response = openai.Completion.create(model="text-davinci-003", prompt=str(prompt), temperature=0,
            #                                     max_tokens=int(_csonfig["token_limit"]))
            # OPENAI
            # await openai_async.Completion(api_key=key).create(model="text-davinci-003", prompt=str(prompt),
            #                                                         temperature=0.2,
            #                                                         frequency_penalty=1,
            #                                                         max_tokens=int(_csonfig["token_limit"]))
            # CHAT
            import openai_async.Chat
            _cid = DefaultData.composing_uid(user_id=user, chat_id=group)
            receiver = openai_async.Chat.Chatbot(api_key=key,
                                                 conversation_id=_cid)
            response = await receiver.get_chat_response(model="text-davinci-003", prompt=str(prompt),
                                                        max_tokens=int(_csonfig["token_limit"]))
            # print(response)
            _deal_rq = rqParser.get_response_text(response)
            # print(_deal_rq)
            _deal = _deal_rq[0]
            _usage = rqParser.get_response_usage(response)
            logger.info(f"RUN:{user}:{group} --prompt: {prompt} --req: {_deal} ")
        except Exception as e:
            logger.error(f"RUN:Api Error:{e}")
            _usage = 0
            _deal = f"Api Outline \n {prompt}"
        # 限额
        Usage.renewUsage(user=user, father=_Usage, usage=_usage)
        _deal = ContentDfa.filter_all(_deal)
        # 人性化处理
        _deal = Utils.Humanization(_deal)
        return _deal


async def WhiteUserCheck(bot, message, WHITE):
    if _csonfig.get("whiteUserSwitch"):
        if not str(abs(message.from_user.id)) in _csonfig.get("whiteUser"):
            try:
                await bot.send_message(message.chat.id,
                                       f"Check the settings to find that you is not whitelisted!...{WHITE}")
            except Exception as e:
                logger.error(e)
            finally:
                return True
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True
    return False


async def WhiteGroupCheck(bot, message, WHITE):
    if str(abs(message.chat.id)) in _csonfig["blockGroup"]:
        await bot.send_message(message.chat.id,
                               f"The group is blocked!...\n\n{WHITE}")
        return True
    if _csonfig.get("whiteGroupSwitch"):
        if not str(abs(message.chat.id)) in _csonfig.get("whiteGroup"):
            try:
                await bot.send_message(message.chat.id,
                                       f"The group is not whitelisted!...\n\n{WHITE}")
            except Exception as e:
                logger.error(e)
            finally:
                logger.info(f"RUN:non-whitelisted groups:{abs(message.chat.id)}")
                return True  # await bot.leave_chat(message.chat.id)
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True
    return False


async def Forget(bot, message, config):
    from openai_async.utils.data import MsgFlow
    _cid = DefaultData.composing_uid(user_id=message.from_user.id, chat_id=message.chat.id)
    return MsgFlow(uid=_cid).forget()


async def private_Chat(bot, message, config):
    load_csonfig()
    # 处理初始化
    _prompt = message.text
    if message.text.startswith("/chat"):
        await Forget(bot, message, config)
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
    # 处理开关
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return
    # 白名单检查
    if await WhiteUserCheck(bot, message, config.WHITE):
        return
    try:
        if len(_prompt) > 1:
            _req = await GroupChat.load_group_response(user=message.from_user.id, group=message.chat.id,
                                                       key=config.OPENAI_API_KEY,
                                                       prompt=_prompt[1])
            await bot.reply_to(message, f"{_req}\n{config.INTRO}")
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Error Occur~Maybe Api request rate limit~nya")


async def Text(bot, message, config, reset: bool = False):
    load_csonfig()
    # 拿到 prompt
    _prompt = message.text
    if message.text.startswith("/chat"):
        await Forget(bot, message, config)
        _prompt_r = message.text.split(" ", 1)
        if len(_prompt_r) < 2:
            return
        _prompt = _prompt_r[1]
    # 处理是否忘记
    if reset:
        await Forget(bot, message, config)
    else:
        # 加判定上文是否为此人的消息
        if not str(Utils.checkMsg(f"{message.chat.id}{message.reply_to_message.id}")) == f"{message.from_user.id}":
            return
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return
    # 群组白名单检查
    await WhiteGroupCheck(bot, message, config.WHITE)

    try:
        _req = await GroupChat.load_group_response(user=message.from_user.id, group=message.chat.id,
                                                   key=config.OPENAI_API_KEY,
                                                   prompt=_prompt)
        msg = await bot.reply_to(message, f"{_req}\n{config.INTRO}")
        Utils.trackMsg(f"{message.chat.id}{msg.id}", user_id=message.from_user.id)
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Error Occur~Maybe Api request rate limit~nya")


async def Master(bot, message, config):
    load_csonfig()
    if message.from_user.id in config.master:
        try:
            command = message.text
            if command.startswith("/usercold"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["usercold_time"] = int(_len_)
                    await bot.reply_to(message, f"user cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset user cold time limit to{_len_}")

            if command.startswith("/groupcold"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["groupcold_time"] = int(_len_)
                    await bot.reply_to(message, f"group cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset group cold time limit to{_len_}")

            if command.startswith("/tokenlimit"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["token_limit"] = int(_len_)
                    await bot.reply_to(message, f"tokenlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset tokenlimit limit to{_len_}")

            if command.startswith("/inputlimit"):
                _len = Utils.extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["input_limit"] = int(_len_)
                    await bot.reply_to(message, f"inputlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset input limit to{_len_}")

            if command == "/onw":
                _csonfig["whiteGroupSwitch"] = True
                await bot.reply_to(message, "ON:whiteGroup")
                save_csonfig()
                logger.info("SETTING:whiteGroup ON")

            if command == "/offw":
                _csonfig["whiteGroupSwitch"] = False
                await bot.reply_to(message, "SETTING:whiteGroup OFF")
                save_csonfig()
                logger.info("SETTING:whiteGroup OFF")

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

            if command == "/config":
                path = str(pathlib.Path().cwd()) + "/" + "Config/config.json"
                if pathlib.Path(path).exists():
                    doc = open(path, 'rb')
                    await bot.send_document(message.chat.id, doc)
                else:
                    await bot.reply_to(message, "没有找到配置文件")

            if "/addw" in command:
                for group in Utils.extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    _csonfig["whiteGroup"].append(str(groupId))
                    await bot.reply_to(message, 'White Group Added' + str(groupId))
                    logger.info(f"SETTING:White Group Added {group}")
                save_csonfig()

            if "/block" in command:
                for group in Utils.extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    _csonfig["blockGroup"].append(str(groupId))
                    await bot.reply_to(message, 'Block Group Added' + str(groupId))
                    logger.info(f"SETTING:Block Group Added {group}")
                save_csonfig()

            if "/delw" in command:
                for group in Utils.extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    if int(groupId) in _csonfig["whiteGroup"]:
                        _csonfig["whiteGroup"].remove(str(groupId))
                        await bot.reply_to(message, 'White Group Removed ' + str(groupId))
                        logger.info(f"SETTING:White Group Removed {group}")
                if isinstance(_csonfig["whiteGroup"], list):
                    _csonfig["whiteGroup"] = list(set(_csonfig["whiteGroup"]))
                save_csonfig()

            if command == "/userwon":
                _csonfig["whiteUserSwitch"] = True
                await bot.reply_to(message, "SETTING:whiteUserSwitch ON")
                save_csonfig()
                logger.info("SETTING:whiteUser ON")

            if command == "/userwoff":
                _csonfig["whiteUserSwitch"] = False
                await bot.reply_to(message, "SETTING:whiteUserSwitch OFF")
                save_csonfig()
                logger.info("SETTING:whiteUser OFF")

            if "/adduser" in command:
                for group in Utils.extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    _csonfig["whiteUser"].append(str(groupId))
                    await bot.reply_to(message, 'White User Added' + str(groupId))
                    logger.info(f"SETTING:White User Added {group}")
                save_csonfig()

            if "/deluser" in command:
                for group in Utils.extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    if int(groupId) in _csonfig["whiteUser"]:
                        _csonfig["whiteUser"].remove(str(groupId))
                        await bot.reply_to(message, 'White User Removed ' + str(groupId))
                        logger.info(f"SETTING:White User Removed {group}")
                if isinstance(_csonfig["whiteUser"], list):
                    _csonfig["whiteUser"] = list(set(_csonfig["whiteUser"]))
                save_csonfig()
            if command == "/updetect":
                keys, _error = InitCensor()
                if _error:
                    error = '\n'.join(_error)
                    errors = f"Error:\n{error}"
                else:
                    # 重载 AntiSpam 主题库
                    ContentDfa.change_words(path="./Data/Danger.form")
                    errors = "Success"
                if message:
                    await bot.reply_to(message, f"{'|'.join(keys)}\n\n{errors}")
            if not command.startswith("/"):
                await private_Chat(bot, message, config)
        except Exception as e:
            logger.error(e)


async def Start(bot, message, config):
    await bot.reply_to(message, f"Ping，Use /chat start a new chat loop")


async def About(bot, message, config):
    await bot.reply_to(message, f"{config.ABOUT}")
