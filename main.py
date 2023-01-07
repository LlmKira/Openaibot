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
logger.info("新闻：vits 需要 apt install ffmpeg 安装 ffmpeg！")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")


def main():
    ctrlConfig = config.Controller
    pool = multiprocessing.Pool(processes=len(ctrlConfig))   # 进程池
    pLock = multiprocessing.Lock()
    try:
        for starter in ctrlConfig:
            if not Path(f"App/{starter}.py").exists():
                logger.warning(f"Controller {starter} Do Not Exist.")
                continue
            module = importlib.import_module('App.' + starter)
            pool.apply_async(func=module.BotRunner(ctrlConfig.get(starter)).run, args=(pLock,))
            # threads.append(t)
        # for t in threads:
            # t.join()  # 等待所有线程退出
        pool.close()   # 关池，防止新进程插入
    except KeyboardInterrupt:
        logger.info('Exiting.')
        exit(0)

if __name__ == '__main__':  # 兼容Windows multiprocessing
    main()
