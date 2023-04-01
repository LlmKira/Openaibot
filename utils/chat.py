# -*- coding: utf-8 -*-
# @Time    : 12/9/22 8:15 AM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys
import random
import re
import time
from typing import Optional, Union
from pydantic import BaseModel


class FromChat(BaseModel):
    id: int
    name: str = "猫娘群"


class FromUser(BaseModel):
    id: int
    name = "猫娘"
    admin: bool = False


class UserMessage(BaseModel):
    id: int = 0
    from_user: FromUser
    from_chat: FromChat
    text: str
    prompt: list
    date: int = int(time.time() * 1000)
    reply_user_id: Optional[int]
    reply_chat_id: Optional[int]


class MessageToolBox(object):

    @staticmethod
    def get_error_answer():
        _wait_child = ["6 ", "? ", "别 ", "呃呃 ", "我不好说，", "害怕，",
                       "？？？？", "....", "666 ", "勿Cue，", "忙着呢 ", "等我打个电话...",
                       "等我查查字典...", "亲，", "别急", "", "", "", "", "",
                       "啊哈哈哈。", "尴尬。", "Oppose..", "你知道的。", "停停...", "手机信号不好，", "手机信号不好，",
                       '到底说啥呐？', '我不懂', '笑死，', '不明白了，', "哇！", "牛的"
                       ]
        _wait = ["稍等，土豆炸了", "服务器真的炸了",
                 "有点小问题", "发生了啥",
                 "Crash了", "ServerBoom",
                 "服务器进水了", "服务器飞走了",
                 "服务器稍微有点问题...", "服务器被我吃掉了...",
                 "....", "那个", "", "", "", "？"
                 ]
        _compose_list1 = [random.choice(_wait_child), random.choice(_wait)]
        _compose_list2 = [random.choice(_wait_child), random.choice(_wait_child), " ", random.choice(_wait)]
        _compose_list = random.choice([_compose_list2, _compose_list1])
        _info = f"\n{' '.join(_compose_list)}"
        return _info

    @staticmethod
    def get_refuse_answer():
        _censor_child = ["你说啥呢？", "我不说,", "不懂年轻人,", "6 ", "? ", "别 ", "呃呃 ", "我不好说，", "害怕，",
                         "我想说的是", "我想强调的是...", "没意思", "无聊...", "你以为我会回你？", "",
                         "我想指出的是，", "我想重申的是，", "[叛逆]", "[傲娇]", "？？？？", "....", "666 ",
                         "什么事儿呀，", "是啊，是啊。", "你猜啊，", "就是啊，", "勿Cue，", "忙着呢 ", "等我打个电话...",
                         "等我查查字典...", "亲，", "别急", "", "", "", "", "", "[不屑]", "[微笑]", "[微笑]", "[微笑]",
                         "哎呀，真的吗？", "啊哈哈哈。", "你知道的。", "停停...", "手机信号不好，", "手机信号不好，",
                         '到底说啥呐？', '我不懂', '笑死，', '不明白了，', '你能解释一下吗，', '太复杂了，都不懂,', "哇！"
                         ]
        _censor = ["有点离谱，不想回答。", "别为难我。",
                   "累了，歇会儿。", "能不能换个话题？",
                   "我不想说话。", "没什么好说的。", "你觉得我会回复你？", "别急。", "别急！", "别急..",
                   "这里不适合说这个。", "我没有什么可说的。",
                   "我不喜欢说话。", "反正我拒绝回答。",
                   "我不喜欢被问这个。", "我觉得这个问题并不重要。",
                   "我不想谈论这个话题。", "我不想对这个问题发表意见！",
                   '你觉得该换个话题了吗？', '我们能不能换个话题聊聊？',
                   '让我们换个话题聊聊？', '谈点别的话题吧！',
                   '要不要换个话题？', '说这个多没意思。',
                   '换个话题呗...', '你想换个话题吗？', '我们换个话题谈啊！',
                   '你觉得该换个话题了吗？', '别谈这个话题了！', '我们能不能换个话题聊聊？',
                   '换个新鲜的话题吧！', '谈点别的话题吧！',
                   '要不要换个话题？', '换个话题来聊聊吧！', '换个新题目聊聊吧！',
                   '别管我了。', '你走开。', '我不理你了。', '算了吧。', '算了吧。',
                   '算了吧。', '算了吧。', '算了吧。', '再见了。',
                   '你听不懂我了。', '何不换个话题？', '我们换个话题谈啊！',
                   '你觉得该换个话题了吗？', '别谈这个话题了！',
                   '我们能不能换个话题聊聊？', '换个新鲜的话题吧！',
                   '谈点别的话题吧！', '要不要换个话题？', '这一切都结束了。', '我不在乎你。', '再也不跟你说话了。',
                   '别再烦我了。', '别搭理我。', '闭嘴', '别找我了',
                   '这个话题太旧了，来谈谈其他的吧！', '低情商。',
                   '换个话题来聊聊吧！', '换个新题目聊聊吧！']
        _compose_list1 = [random.choice(_censor_child), random.choice(_censor)]
        _compose_list2 = [random.choice(_censor_child), random.choice(_censor_child), random.choice(_censor)]
        _compose_list = random.choice([_compose_list2, _compose_list1])
        _info = f"\n{' '.join(_compose_list)}"
        return _info

    @staticmethod
    def name_split(sentence: str, limit: int, safe_replace: bool = True) -> str:
        """
        This function splits a string based on specific delimiters and returns the longest sub-string that is shorter than
        the provided limit. If no sub-strings are shorter than the limit, it returns the first `limit` characters of the original string.

        Args:
            sentence (str): The input string to be split and truncated.
            limit (int): The maximum length of the output string.
            safe_replace (bool, optional): Whether to replace certain delimiters with safe alternatives before splitting.
                                            Defaults to True.

        Returns:
            str: The output string which is either the longest sub-string that is shorter than the limit or the first `limit`
                 characters of the original string.
        """
        if safe_replace:
            # Replace potentially problematic delimiters with safer alternatives
            sentence = sentence.replace(":", "：")
        if len(sentence) <= limit:
            # If the input string is already shorter than the limit, return it as-is
            return sentence
        # Split the input string into sub-strings using multiple delimiters
        str_list = re.split("[, !]#《》:：【】", sentence)
        # Sort the sub-strings by decreasing length
        str_list.sort(key=len, reverse=True)
        for item in str_list:
            if len(item) < limit:
                # Return the longest sub-string that is shorter than the limit
                return item
        # If no sub-strings are shorter than the limit, return the first `limit` characters of the input string
        return sentence[:limit]

    @staticmethod
    def mask_middle(s: str, num_keep: int) -> str:
        """
        This function replaces the middle characters of a given string with asterisks.
        The number of characters to be replaced is calculated as `len(s) - 2*num_keep`.
        If this value is less than or equal to zero, the original string is returned unmodified.

        Args:
            s (str): The input string to be masked.
            num_keep (int): The number of characters to keep at the beginning and end of the string.

        Returns:
            str: The masked string, with the middle characters replaced by asterisks.
        """

        # Calculate the number of characters to be replaced
        num_replace = len(s) - 2 * num_keep

        if num_replace <= 0:
            # If there are no characters to replace, return the original string
            return s

        # Construct the replacement string
        replace_str = "*" * num_replace

        # Insert the replacement string into the original string at the specified location
        return s[:num_keep] + replace_str + s[num_keep + num_replace:]


def create_message(
        user_id: int,
        user_name,
        group_id: int,
        group_name,
        text: str,
        state: int,
        reply_chat_id: Optional[int] = None,
        reply_user_id: Optional[int] = None,
        prompt: Union[str, list] = None,
        date=time.time()):
    state = abs(state)
    if state != 0:
        group_id = int(f"{group_id}{state}")
        user_id = int(f"{user_id}{state}")
    if prompt is None:
        prompt = [text]
    if isinstance(prompt, str):
        prompt = [prompt]
    message = {
        "text": text,
        "prompt": prompt,
        "from_user": FromUser(id=user_id, name=user_name),
        "from_chat": FromChat(id=group_id, name=group_name),
        "reply_user_id": reply_user_id,
        "reply_chat_id": reply_chat_id,
        "date": date
    }
    return UserMessage(**message)
