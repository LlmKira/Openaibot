# -*- coding: utf-8 -*-
# @Time    : 9/22/22 11:04 PM
# @FileName: Event.py
# @Software: PyCharm
# @Github    ：sudoskys
import json
import pathlib
import time

from loguru import logger
from utils.Data import DataWorker, DictUpdate
from utils.Detect import DFA

logger.add(sink='run.log', format="{time} - {level} - {message}", level="INFO", rotation="500 MB", enqueue=True)

DataUtils = DataWorker(prefix="Open_Ai_bot_")

ContentDfa = DFA(path="./Data/Danger.form")

default_table = {
    "statu": True,
    "input_limit": 200,
    "token_limit": 100,
    "usercold_time": 5,
    "groupcold_time": 1,
    "whiteUserSwitch": True,
    "whiteGroupSwitch": False,
    "whiteGroup": [
        "-1001662266151",
    ],
    "whiteUser": [
    ],
    "Model": {
        "-1001561314417": ""
    }
}


# IO
def load_csonfig():
    global _csonfig
    with open("./Config/config.json", encoding="utf-8") as f:
        _csonfig = json.load(f)
        DictUpdate.dict_update(_csonfig, default_table)
        return _csonfig


def save_csonfig():
    with open("./Config/config.json", "w", encoding="utf8") as f:
        json.dump(_csonfig, f, indent=4, ensure_ascii=False)


def extract_arg(arg):
    return arg.split()[1:]


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
        key_time = int(time.strftime("%Y%m%d%H%M", time.localtime()))
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
            DataUtils.setKey(f"flood_{user}", "FAST", exN=usercold_time)
    # User
    if DataUtils.getKey(f"flood_group_{group}"):
        # double req in 3 seconds
        return True
    else:
        if _csonfig["groupcold_time"] > 1:
            DataUtils.setKey(f"flood_{group}", "FAST", exN=groupcold_time)
    return False


async def load_response(user, group, key: str = "", prompt: str = "Say this is a test", userlimit: int = None):
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
    if WaitFlood(user=user, group=group, usercold_time=userlimit):
        return "TOO FAST"

    # 用量检测
    _Usage = Usage.isOutUsage(user)
    if _Usage["status"]:
        return "OUT OF USAGE"
    # 请求
    try:
        # import openai
        # openai.api_key = key
        # response = openai.Completion.create(model="text-davinci-003", prompt=str(prompt), temperature=0,
        #                                     max_tokens=int(_csonfig["token_limit"]))
        import openai_sync
        response = await openai_sync.Completion(api_key=key).create(model="text-davinci-003", prompt=str(prompt),
                                                                    temperature=0,
                                                                    max_tokens=int(_csonfig["token_limit"]))
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
    return _deal


async def WhiteUserCheck(bot, message):
    if _csonfig.get("whiteUserSwitch"):
        if not str(abs(message.from_user.id)) in _csonfig.get("whiteUser"):
            try:
                await bot.send_message(message.chat.id,
                                       "Check the settings to find that you is not whitelisted!...")
            except Exception as e:
                logger.error(e)
            finally:
                return True
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True


async def WhiteGroupCheck(bot, message, config):
    if _csonfig.get("whiteGroupSwitch"):
        if not str(abs(message.chat.id)) in _csonfig.get("whiteGroup"):
            try:
                await bot.send_message(message.chat.id,
                                       f"The group is not whitelisted!...\n{config.WHITE}")
            except Exception as e:
                logger.error(e)
            finally:
                logger.info(f"RUN:non-whitelisted groups:{abs(message.chat.id)}")
                return True  # await bot.leave_chat(message.chat.id)
    else:
        if _csonfig.get("whiteUserSwitch") is None:
            return True


async def Text(bot, message, config):
    load_csonfig()
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return

    # 群组白名单检查
    await WhiteGroupCheck(bot, message, config=config)
    _prompt = message.text.split(" ", 1)
    try:
        if len(_prompt) > 1:
            _req = await load_response(user=message.from_user.id, group=message.chat.id, key=config.OPENAI_API_KEY,
                                       prompt=_prompt[1])
            await bot.reply_to(message, f"{_req}\n{config.INTRO}")
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Wait！:Trigger Api request rate limit")


async def Chat_P(bot, message, config):
    load_csonfig()
    if not _csonfig.get("statu"):
        await bot.reply_to(message, "BOT:Under Maintenance")
        return
    # 白名单检查
    if await WhiteUserCheck(bot, message):
        return
    # 处理
    _prompt = message.text
    try:
        if len(_prompt) > 1:
            _req = await load_response(user=message.from_user.id, group=message.chat.id, key=config.OPENAI_API_KEY,
                                       prompt=_prompt[1])
            await bot.reply_to(message, f"{_req}\n{config.INTRO}")
    except Exception as e:
        logger.error(e)
        await bot.reply_to(message, f"Wait:Trigger Api request rate limit")


async def Start(bot, message, config):
    await bot.reply_to(message, f"Ping，Use Chat")


async def About(bot, message, config):
    await bot.reply_to(message, f"{config.ABOUT}")


async def Master(bot, message, config):
    load_csonfig()
    if message.from_user.id in config.master:
        try:
            command = message.text
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
                path = str(pathlib.Path().cwd()) + "/" + "Data/config.json"
                if pathlib.Path(path).exists():
                    doc = open(path, 'rb')
                    await bot.send_document(message.chat.id, doc)
                else:
                    await bot.reply_to(message, "没有找到配置文件")

            if command.startswith("/usercold"):
                _len = extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["usercold_time"] = int(_len_)
                    await bot.reply_to(message, f"user cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset user cold time limit to{_len_}")

            if command.startswith("/groupcold"):
                _len = extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["groupcold_time"] = int(_len_)
                    await bot.reply_to(message, f"group cooltime:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset group cold time limit to{_len_}")

            if command.startswith("/tokenlimit"):
                _len = extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["token_limit"] = int(_len_)
                    await bot.reply_to(message, f"tokenlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset tokenlimit limit to{_len_}")

            if command.startswith("/inputlimit"):
                _len = extract_arg(command)[0]
                _len_ = "".join(list(filter(str.isdigit, _len)))
                if _len_:
                    _csonfig["input_limit"] = int(_len_)
                    await bot.reply_to(message, f"inputlimit:{_len_}")
                    save_csonfig()
                    logger.info(f"SETTING:reset input limit to{_len_}")

            if "/addw" in command:
                for group in extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    _csonfig["whiteGroup"].append(str(groupId))
                    await bot.reply_to(message, 'White Group Added' + str(groupId))
                    logger.info(f"SETTING:White Group Added {group}")
                save_csonfig()

            if "/delw" in command:
                for group in extract_arg(command):
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
                for group in extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    _csonfig["whiteUser"].append(str(groupId))
                    await bot.reply_to(message, 'White User Added' + str(groupId))
                    logger.info(f"SETTING:White User Added {group}")
                save_csonfig()

            if "/deluser" in command:
                for group in extract_arg(command):
                    groupId = "".join(list(filter(str.isdigit, group)))
                    if int(groupId) in _csonfig["whiteUser"]:
                        _csonfig["whiteUser"].remove(str(groupId))
                        await bot.reply_to(message, 'White User Removed ' + str(groupId))
                        logger.info(f"SETTING:White User Removed {group}")
                if isinstance(_csonfig["whiteUser"], list):
                    _csonfig["whiteUser"] = list(set(_csonfig["whiteUser"]))
                save_csonfig()
            if not command.startswith("/"):
                await Chat_P(bot, message, config)
        except Exception as e:
            logger.error(e)
