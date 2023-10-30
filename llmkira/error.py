# -*- coding: utf-8 -*-
# @Time    : 2023/10/30 下午3:42
# @Author  : sudoskys
# @File    : error.py
# @Software: PyCharm

# 更安全的 format
import random


class MappingDefault(dict):
    def __missing__(self, key):
        return key


# (ﾉ>ω<)ﾉ 贴心的错误提示
REQUEST_ERROR_MESSAGE_TEMPLATE = [
    "Seems like you're having a bit of a problem with {error}",
    "just cant {error} 💍",
    "不想回答你的问题\n\n\n{error}",
    "没听清，刚刚有人在说话\n\n\n{error}",
    "你再问一遍呗。\n\n `{error}`",
    "A man hold a gun to my head, and ask me to say:\n`{error}`",
    "Just look at what you've done? A error!\n `{error}`",
    "Damn, A error hits me!\n`{error}`",
    "(ﾉ>ω<)ﾉ︵ERROR！ \n`{error}`",
    "(・∀・)つ︵ERROR！ \n`{error}`",
    "我不是故意的，但是 ———— {error}",
    "你说的对，但是 {error}",
    "（╯－＿－）╯︵ERROR！ \n`{error}`",
    "(／‵Д′)／~ ︵ ︵ ERROR！ \n`{error}`",
    "Chocolate!( ・∀・)っ■ERROR■ \n`{error}`",
    "（╯°Д°）╯︵/(.□ .|) ERROR！ \n`{error}`",
    "╮(﹀_﹀”)╭ ERROR！ \n`{error}`",
    "（；￣д￣）ERROR！ \n`{error}`",
    "（╯' - ')╯ ERROR！ \n`{error}`",
    "（╯°□°）╯︵( .o.) ERROR！ \n`{error}`",
    "您的网络不给力啊，再试一次吧\n`{error}`",
    "上网小心，别被坏人骗了\n`{error}`",
    "我不知道你在说什么，但是我知道你在说什么\n`{error}`",
    "贴心的我，不会让你看到错误的\n`{error}`",
    "上网小贴士：\n`{error}`",
    "听说偶尔看看错误，可以让你更加的快乐\n`{error}`",
    "你也许在期待我会回答你的问题，但是我不会\n`{error}`",
    "你不会用错命令了吧？\n`{error}`",
    "这么小声，还想当海军部长？\n`{error}`",
    "你说话太抽象了，我听不懂\n`{error}`",
]


def get_request_error_message(error: str):
    _txt: str = random.choice(REQUEST_ERROR_MESSAGE_TEMPLATE)
    return _txt.format_map(
        MappingDefault(error=error)
    )


# 同样贴心的上传错误提示 (ﾉ>ω<)ﾉ
UPLOAD_ERROR_MESSAGE_TEMPLATE = [
    "I cant upload file {filename} to server {error}",
    "we cant upload {filename}:( , because {error}...",
    "Seems like you're having a bit of a problem uploading {filename}\n`{error}`",
    "just cant upload {filename} to server {error} 💍",
    "I dont know why, but I cant upload {filename} to server {error}",
    ":( I dont want to upload {filename} to server\n `{error}`",
    "{error}, {filename} 404",
    "OMG, {filename} ,ERROR UPLOAD, `{error}`",
    "WTF, I CANT UPLOAD {filename} BECAUSE `{error}`",
    "MY PHONE IS BROKEN, I CANT UPLOAD {filename} BECAUSE `{error}`",
    "As a human, I can't upload {filename} for you :( \n `{error}`"
]


def get_upload_error_message(filename: str, error: str):
    _txt: str = random.choice(REQUEST_ERROR_MESSAGE_TEMPLATE)
    return _txt.format_map(
        MappingDefault(filename=filename, error=error)
    )
