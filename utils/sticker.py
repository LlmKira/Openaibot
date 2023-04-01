# -*- coding: utf-8 -*-
# @Time    : 2/1/23 11:01 AM
# @FileName: sticker.py
# @Software: PyCharm
# @Github    ：sudoskys
import os
import pathlib
import random
from loguru import logger


# TODO 修复情感评分
class Classifiers(object):
    def __init__(self, prompt):
        self.prompt = prompt

    def run(self):
        _score = random.randint(-2, 2)  # Utils.sentiment(self.prompt).get("score")
        _type = ""
        if _score > 1.5:
            _type = "positive"
        if _score < -1.5:
            _type = "negative"
        return _type


class StickerPredict(object):
    def __init__(self):
        # self.model = tweetnlp.Emotion()
        print("Loading Sticker Manger")

    @staticmethod
    def convert_folder(filepath: str) -> dict:
        if not pathlib.Path(filepath).exists():
            return {}

        def get_folder_pictures(filename):
            import os
            all_pictures = []
            for file in os.listdir(filename):
                if file.endswith('.webp'):
                    all_pictures.append(os.path.abspath(os.path.join(filename, file)))
            return all_pictures

        result = {'default': get_folder_pictures(filepath)}

        for root, dirs, files in os.walk(filepath, topdown=True):
            for d in dirs:
                result[d] = get_folder_pictures(os.path.join(root, d))
        return result

    def predict(self, prompt: str, emoji_folder_dict: dict = None, penalty_probab: float = 0):
        if penalty_probab < 1:
            random_int = random.randint(1, 100)
            if 0 < random_int < penalty_probab * 100:
                return None
        # Think
        if not emoji_folder_dict:
            emoji_folder_dict = self.convert_folder("./Data/sticker")
        if not emoji_folder_dict:
            return None
        _type = Classifiers(prompt=prompt).run()
        if emoji_folder_dict.get(_type):
            sticker = random.choice(emoji_folder_dict[_type])
        elif emoji_folder_dict.get("default"):
            sticker = random.choice(emoji_folder_dict["default"])
        else:
            sticker = None
        return sticker

# StickerPredict().predict(prompt="傻")
