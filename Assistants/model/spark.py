# -*- coding: utf-8 -*-
# @Time    : 1/16/23 5:14 PM
# @FileName: spark.py
# @Software: PyCharm
# @Github    ：sudoskys
import pathlib
import struct

import pvporcupine
import pyaudio
from loguru import logger

if pathlib.Path("./Hi-Coco_en_linux_v2_1_0.ppn").exists():
    logger.success("-Hi COCO-")


def trigger(access_key,
            callback_func,
            **kwargs
            ):
    porcupine = None
    pa = None
    audio_stream = None
    try:
        if pathlib.Path("./Hi-Coco_en_linux_v2_1_0.ppn").exists():
            logger.success("-Hi COCO-")
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
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                logger.info("-Wake-")
                callback_func(**kwargs)
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
