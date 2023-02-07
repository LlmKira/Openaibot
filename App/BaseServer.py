# -*- coding: utf-8 -*-
# @Time    : 1/7/23 12:29 PM
# @FileName: run_server.py
# @Software: PyCharm
# @Github    ：sudoskys
import uvicorn
from loguru import logger


class BotRunner:
    def __init__(self, _config):
        self.config = _config

    def run(self, pLock):
        try:
            host = self.config.host
        except Exception as e:
            logger.warning("ApiServer Conf Host Missing")
            host = '127.0.0.1'
        uvicorn.run('App.EventServer:app',
                    host=host,
                    reload_delay=5,
                    port=self.config.port,
                    reload=False,
                    log_level="debug",
                    workers=1
                    )
