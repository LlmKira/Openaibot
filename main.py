# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys,ElvinStarry

from pathlib import Path
from utils.Base import ReadConfig
# 日志
from loguru import logger
import sys
import asyncio
import importlib

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
logger.info("新闻：vits 需要 apt install ffmpeg 安装 ffmpeg！")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")

# 配置分发
client_tasks = set()
# asyncio任务池，保持对所有协程任务的强引用，避免被回收
# https://www.bilibili.com/read/cv17261955/
ctrlConfig = config.Controller
try:
    for starter in ctrlConfig:
        if not Path(f"App/{starter}.py").exists():
            logger.warning(f"Controller {starter} Do Not Exist.")
            continue
        module = importlib.import_module('App.' + starter)
        task = asyncio.create_task(module.BotRunner(ctrlConfig.get(starter)).run())
        client_tasks.add(task)
        task.add_done_callback(client_tasks.discard)
except KeyboardInterrupt:
    logger.info('Main thread exiting')
    exit(0)
