# -*- coding: utf-8 -*-
# @Time    : 1/16/23 5:14 PM
# @FileName: spark.py
# @Software: PyCharm
# @Github    ：sudoskys
import pathlib
import struct

import keyboard
import pvporcupine
import pyaudio
from loguru import logger
from playsound import playsound

if pathlib.Path("./Hi-Coco_en_linux_v2_1_0.ppn").exists():
    logger.success("Load -Hi COCO-")


def trigger(access_key,
            callback_func,
            **kwargs
            ):
    porcupine = None
    pa = None
    audio_stream = None
    try:
        if pathlib.Path("./Hi-Coco_en_linux_v2_1_0.ppn").exists():
            logger.success("Load -Hi COCO-")
            porcupine = pvporcupine.create(access_key=access_key,
                                           keyword_paths=['./Hi-Coco_en_linux_v2_1_0.ppn'])
        else:
            porcupine = pvporcupine.create(access_key=access_key,
                                           keywords=["picovoice", "hey siri", "blueberry"])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length)
        clicked = []
        while True:
            _path = "start.c"
            if pathlib.Path(_path).exists():
                clicked.append(1)
                pathlib.Path(_path).unlink(missing_ok=True)
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0 or clicked:
                clicked.clear()
                logger.info("-Wake-")
                if pathlib.Path("wake.mp3").exists():
                    playsound("wake.mp3")
                callback_func(**kwargs)
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
