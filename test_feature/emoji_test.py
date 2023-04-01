# -*- coding: utf-8 -*-
# @Time    : 1/31/23 2:24 PM
# @FileName: emoji_test.py
# @Software: PyCharm
# @Github    ：sudoskys


# pip install tweetnlp

import tweetnlp

# MODEL
model = tweetnlp.Emoji()
res = model.predict('Beautiful sunset last night from the pontoon @TupperLakeNY')  # Or `model.predict`
print(res)
res = model.predict('溺爱你')  # Or `model.predict`
print(res)
# model.emoji('我爱你 @TupperLakeNY', return_probability=True)

# GET DATASET
# dataset, label2id = tweetnlp.load_dataset('emoji')
import tweetnlp

# MODEL
model = tweetnlp.load_model('offensive')  # Or `model = tweetnlp.Offensive()`
res = model.offensive("sick")
print(res)
