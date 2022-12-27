# -*- coding: utf-8 -*-
# @Time    : 12/25/22 3:20 PM
# @FileName: main.py.py
# @Software: PyCharm
# @Github    ：sudoskys

import pyaudio
# rec("record.wav")
import speech_recognition as sr


def rec():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("please say something")
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
    print(1)
    with open("recording.wav", "wb") as f:
        f.write(audio.get_wav_data())


rec()
