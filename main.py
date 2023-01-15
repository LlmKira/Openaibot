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
import multiprocessing
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
logger.info("新闻:命令表有改动")
logger.info("新闻:必须 `pip install -U openai-kira -i https://pypi.org/simple/` 到 0.3.5 版本")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")


def start():
    # pool = multiprocessing.Pool(processes=len(ctrlConfig))   # 进程池
    ctrlConfig = config.Controller
    pLock = multiprocessing.Lock()
    try:
        for starter in ctrlConfig:
            if not Path(f"App/{starter}.py").exists():
                logger.warning(f"Controller {starter} Do Not Exist.")
                continue
            module = importlib.import_module('App.' + starter)
            p = multiprocessing.Process(target=module.BotRunner(ctrlConfig.get(starter)).run, args=(pLock,))
            p.start()
            # threads.append(t)
        # for t in threads:
        # t.join()  # 等待所有线程退出
        # pool.close()
        # pool.join()
    except KeyboardInterrupt:
        logger.info('Exiting.')
        exit(0)


if __name__ == '__main__':  # 兼容Windows multiprocessing
    start()
