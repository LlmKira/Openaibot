# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys,ElvinStarry
import pathlib
# 日志
from pathlib import Path
from loguru import logger
import sys
import importlib

from utils.Base import TOMLConfig

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")

# 日志机器
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True)

logger.debug("Debug Mode On")
logger.info("NEWS Channel:https://t.me/Openaibot_channel")

CONFIG_FILE = str(Path.cwd()) + "/Config/app.toml"
if not pathlib.Path(CONFIG_FILE).exists():
    raise FileNotFoundError("Cant find Config/app.toml")

config = TOMLConfig().parse_file(CONFIG_FILE)


def start():
    ctrl_config = config.Controller
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(ctrl_config)) as p:
            for starter in ctrl_config:
                if not Path(f"App/{starter}.py").exists():
                    logger.warning(f"Skip Controller {starter} ,Do Not Exist.")
                    continue
                else:
                    logger.success(f"Set Controller {starter}.")
                module = importlib.import_module('App.' + starter)
                # 使用 ThreadPoolExecutor 的 submit 方法
                task = p.submit(module.BotRunner(ctrl_config.get(starter)).run)
                logger.info(task.exception())
    except KeyboardInterrupt:
        logger.info('Caught Ctrl-C, Exiting.')
        exit()


if __name__ == '__main__':  # 兼容Windows multiprocessing
    start()
