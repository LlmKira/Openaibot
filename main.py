# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys
from pathlib import Path
from utils.Base import ReadConfig
# 日志
from loguru import logger
import sys
import threading
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
threads = []  # 线程池
ctrlConfig = config.Controller
try:
    for ctrl in ctrlConfig:
        filepath = 'App/' + ctrl + '.py'
        if not Path(filepath).exists():
            logger.warning(f"Controller {filepath} Do Not Exist.")
            continue
        module = importlib.import_module('App.' + ctrl)
        t = threading.Thread(target=module.BotRunner(ctrlConfig.get(ctrl)).run)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()  # 等待所有线程退出
    logger.info('主线程退出')
except KeyboardInterrupt:
    logger.info('主线程退出')
    exit(0)
