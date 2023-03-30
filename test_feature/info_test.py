# -*- coding: utf-8 -*-
# @Time    : 3/4/23 4:39 PM
# @FileName: info_test.py
# @Software: PyCharm
# @Github    ：sudoskys

from PIL import Image

from Handler.Reader import FileReader

text_info, _r = FileReader().get_ai_image_info(Image.open("001.png"))
print(type(text_info))
print(text_info)
