# -*- coding: utf-8 -*-
# @Time    : 2/1/23 11:01 AM
# @FileName: Sticker.py
# @Software: PyCharm
# @Github    ：sudoskys
import os
import pathlib
import random

import loguru
import tweetnlp
import torch
from loguru import logger

EMOJI_NAME = {
    '❤': 'heart',
    '😍': 'heart_eyes',
    '😂': 'joy',
    '💕': 'two_hearts',
    '🔥': 'fire',
    '😊': 'blush',
    '😎': 'sunglasses',
    '✨': 'sparkles',
    '💙': 'blue_heart',
    '😘': 'kissing_heart',
    '📷': 'camera',
    '🇺🇸': 'us',
    '☀': 'sunny',
    '💜': 'purple_heart',
    '😉': 'wink',
    '💯': '100',
    '😁': 'grin',
    '🎄': 'christmas_tree',
    '📸': 'camera_flash',
    '😜': 'stuck_out_tongue_winking_eye'
}


class StickerPredict(object):
    def __init__(self):
        # self.model = tweetnlp.Emotion()
        print("Loading Sticker Manger")
        self.model = tweetnlp.Emoji()
        self.model.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.EMOJI_NAME = {
            '❤': 'heart',
            '😍': 'heart_eyes',
            '😂': 'joy',
            '💕': 'heart',
            '🔥': 'anger',
            '😊': 'heart',
            '😎': 'optimism',
            '✨': 'sparkles',
            '💙': 'heart',
            '😘': 'heart',
            '📷': 'optimism',
            '🇺🇸': 'optimism',
            '☀': 'optimism',
            '💜': 'heart',
            '😉': 'wink',
            '💯': '100',
            '😁': 'grin',
            '🎄': 'christmas_tree',
            '📸': 'camera_flash',
            '😜': 'stuck_out_tongue_winking_eye'
        }

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
        predict_result = self.model.predict(text=prompt, return_probability=True)
        _type = predict_result["label"]
        _type = self.EMOJI_NAME.get(_type)
        print(_type)
        if emoji_folder_dict.get(_type):
            sticker = random.choice(emoji_folder_dict[_type])
        elif emoji_folder_dict.get("default"):
            sticker = random.choice(emoji_folder_dict["default"])
        else:
            sticker = None
        return sticker

# StickerPredict().predict(prompt="傻")
