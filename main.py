# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys
from pathlib import Path
from App.Controller import BotRunner
from utils.Base import ReadConfig
# 日志
from loguru import logger
import sys

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")

# 日志机器
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="500 MB",
           enqueue=True)
# logger.info("新闻：api key 只能通过 机器人命令配置")
logger.debug("Debug Mode On")

logger.info("新闻: Enhance_Server 升级为配件库，请根据 readme 配置 service json 来使用这个功能")

logger.info("新闻：vits 需要 apt install ffmpeg 安装 ffmpeg！")

logger.info("新闻：app.toml Enhance_Server 配置变动为 dict")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")
App = BotRunner(config)
App.run()
