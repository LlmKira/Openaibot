# -*- coding: utf-8 -*-
# @Time    : 9/10/22 7:46 PM
# @FileName: Logging.py
# @Software: PyCharm
# @Github    ：sudoskys
from rich.console import Console


class logCreate(object):
    def __init__(self):
        self.console = Console(color_system='256', style=None)

    def info(self, info_):
        self.console.log(info_, sep="BiliMonitor - ")


def rlogCreate():
    import logging

    # 创建Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # 创建Handler

    # 终端Handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)

    # 文件Handler
    fileHandler = logging.FileHandler('log.log', mode='w', encoding='UTF-8')
    fileHandler.setLevel(logging.NOTSET)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    # 添加到Logger中
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)
    return logger
