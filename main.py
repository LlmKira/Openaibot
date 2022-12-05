# -*- coding: utf-8 -*-
# @Time    : 9/22/22 10:07 PM
# @FileName: main.py
# @Software: PyCharm
# @Github    ：sudoskys
from pathlib import Path

import loguru

from utils.Base import ReadConfig
from App.Controller import BotRunner

loguru.logger.info("Config文件更新，请重新覆写 Config")

config = ReadConfig().parseFile(str(Path.cwd()) + "/Config/app.toml")
App = BotRunner(config)
App.run()
