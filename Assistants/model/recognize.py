# -*- coding: utf-8 -*-
# @Time    : 12/25/22 3:20 PM
# @FileName: main.py.py
# @Software: PyCharm
# @Github    ：sudoskys
import pathlib

# 负责我们的 唤醒和 STT 服务
import speech_recognition
# rec("record.wav")
import speech_recognition as sr
from playsound import playsound

from .utils import data as data
from loguru import logger

r = sr.Recognizer()


def Wake(lang: str = "zh", method: str = "whisper", config: dict = None):
    if len(lang) == 2:
        lang = data.LANGUAGES.get(lang.lower())
    else:
        lang = lang.lower()
    ##
    with sr.Microphone() as source:
        audio = r.listen(source, phrase_time_limit=5)
    logger.info("-Think-")
    if pathlib.Path("think.mp3").exists():
        playsound("think.mp3")
    if method == "whisper":
        return STT(lang=lang).whisper(audio=audio)
    elif method == "azure":
        api_key = config["key"][0]
        _lang = config["lang"].get(lang)
        if not _lang:
            _lang = "zh-CN"
        location = config["location"]
        assert api_key, "Miss Api Key"
        return STT(lang=_lang).azure(api_key=api_key,
                                     audio=audio,
                                     location=location,
                                     language=_lang
                                     )


class STT(object):
    # Warp func
    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def whisper(self, audio: speech_recognition.AudioData):
        text = ""
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

    def azure(self, audio: speech_recognition.AudioData, api_key: str, location: str = None, language: str = "en-US"):
        text = ""
        try:
            text = r.recognize_azure(audio, language=language, location=location, key=api_key)
        except sr.UnknownValueError:
            print("Microsoft Azure Speech could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Microsoft Azure Speech service; {0}".format(e))
        return text
