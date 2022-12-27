# -*- coding: utf-8 -*-
# @Time    : 12/27/22 9:48 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys
from .platform import ChatPlugin, PluginParam


def get_reply(prompt, table):
    processor = ChatPlugin()
    processed = processor.process(param=PluginParam(text=prompt, server=table))  # , plugins=('search'))
    reply = "\n".join(processed) if processed else ""
    return reply
