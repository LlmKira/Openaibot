# -*- coding: utf-8 -*-
# @Time    : 1/7/23 12:29 PM
# @FileName: run_server.py
# @Software: PyCharm
# @Github    ：sudoskys
import uvicorn


class BotRunner:
    def __init__(self, _config):
        self.config = _config

    def run(self, pLock):
        uvicorn.run('App.EventServer:app', host='127.0.0.1', port=self.config.port, reload=True, log_level="debug", workers=1)
