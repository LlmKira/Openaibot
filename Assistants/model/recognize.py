# -*- coding: utf-8 -*-
# @Time    : 12/25/22 3:20 PM
# @FileName: main.py.py
# @Software: PyCharm
# @Github    ：sudoskys

# 负责我们的 唤醒和 STT 服务
import speech_recognition
# rec("record.wav")
import speech_recognition as sr
from .utils import data as data
from loguru import logger

r = sr.Recognizer()


def Wake(lang: str = "zh", method: str = "whisper", api_key: str = None):
    with sr.Microphone() as source:
        audio = r.listen(source, phrase_time_limit=3)
    logger.info("-Think-")
    if method == "whisper":
        return STT(lang=lang).whisper(audio=audio)
    elif method == "azure":
        assert api_key, "Miss Api Key"
        return None


class STT(object):
    # Warp func
    def __init__(self, lang: str = "CN"):
        self.lang = lang

    def whisper(self, audio: speech_recognition.AudioData):
        text = None
        if len(self.lang) == 2:
            language = data.LANGUAGES.get(self.lang.lower())
        else:
            language = self.lang.lower()
        try:
            text = r.recognize_whisper(audio_data=audio, model="base", language=language)
        except sr.UnknownValueError:
            print("Whisper could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Whisper")
        return text
