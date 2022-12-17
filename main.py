# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys
from pathlib import Path
from App.Controller import BotRunner
from utils.Base import ReadConfig
from loguru import logger

# 日志机器
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="500 MB",
           enqueue=True)

# logger.info("新闻：api key 只能通过 机器人命令配置")
logger.info("新闻：app.toml Enhance_Server 配置变动为 dict")

logger.info("新闻：app.toml 新增 Enhance_Server 支持即时查询，请按照 readme 添加 `Enhance_Server={}` 在 `bot` 下面")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")
App = BotRunner(config)
App.run()
