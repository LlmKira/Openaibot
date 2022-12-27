# -*- coding: utf-8 -*-
# @Time    : 12/26/22 3:39 PM
# @FileName: record.py
# @Software: PyCharm
# @Github    ：sudoskys
import pyaudio

p = pyaudio.PyAudio()
print(p)
# Device info print
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))
