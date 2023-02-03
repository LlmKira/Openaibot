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

logger.info("NEWS Channel:https://t.me/Openaibot_channel")
# logger.info("新闻:命令表有改动")
logger.info("新闻:请使用 `pip install -U llm-kira -i https://pypi.org/simple/` `pip uninstall openai-kira`")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")


def start():
    ctrlConfig = config.Controller
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(ctrlConfig)) as p:
            for starter in ctrlConfig:
                if not Path(f"App/{starter}.py").exists():
                    logger.warning(f"Controller {starter} Do Not Exist.")
                    continue
                module = importlib.import_module('App.' + starter)
                # 使用 ThreadPoolExecutor 的 submit 方法
                p.submit(module.BotRunner(ctrlConfig.get(starter)).run)
    except KeyboardInterrupt:
        logger.info('Caught Ctrl-C, Exiting.')
        exit()


if __name__ == '__main__':  # 兼容Windows multiprocessing
    start()
