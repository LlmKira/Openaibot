# -*- coding: utf-8 -*-
# @Time    : 12/27/22 6:12 PM
# @FileName: web.py
# @Software: PyCharm
# @Github    ：sudoskys
import os

__all__ = [f.strip(".py") for f in os.listdir(os.path.abspath(os.path.dirname(__file__))) if
           f.endswith('.py') and "_" not in f]

# print(__all__)

if __name__ == '__main__':
    re = ''
    # from openai_async.Chat.plugin import search
    # re = search.Search().process(server=["https://www.baidu.com/s?ie=utf-8&rsv_bp=1&tn=baidu&wd={}"],prompt="孤独摇滚")
    print(re)

if __name__ == '__main__':
    s = [f.strip(".py") for f in os.listdir('.') if f.endswith('.py') and "_" not in f]
    print(s)
