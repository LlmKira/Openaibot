# -*- coding: utf-8 -*-
# @Time    : 2023/10/22 下午11:53
# @Author  : sudoskys
# @File    : emoji_.py
# @Software: PyCharm

import pathlib
from typing import Literal

import emoji


def get_sticker_table(sticker_dir: pathlib.Path) -> dict:
    if not sticker_dir.exists() or not sticker_dir.is_dir():
        raise Exception('sticker dir not exists')
    sticker_list = list(sticker_dir.glob('*.png'))
    _emoji = {}
    for sticker in sticker_list:
        if len(emoji.emojize(sticker.stem)) == 1:
            _emoji[emoji.emojize(sticker.stem)] = sticker.absolute()
    return _emoji


table = get_sticker_table(pathlib.Path('sticker'))
_emoji_list = ",".join(table.keys())
print(f"Literal[{_emoji_list}]")

import re

emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
print(emoji_pattern.findall("👍 sdasda"))

print(emoji.emojize("👍"))

MODEL = Literal["👍", "👍🏻", "👍🏼", "👍🏽", "👍🏾", "👍🏿"]
print(MODEL.__args__[2])
