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
            reload = self.config.reload
        except Exception as e:
            logger.warning("ApiServer Conf Host/Reload Missing")
            host = '127.0.0.1'
            reload = False
        uvicorn.run('App.EventServer:app', host=host, port=self.config.port, reload=reload, log_level="debug",
                    workers=1)
