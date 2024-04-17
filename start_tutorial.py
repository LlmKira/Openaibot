# -*- coding: utf-8 -*-
# @Time    : 2023/10/29 上午10:15
# @Author  : sudoskys
# @File    : start_tutorial.py
# @Software: PyCharm
import os
import sys

try:
    import loguru  # noqa
    import rich  # noqa
except ImportError:
    print("Please run `poetry install --all-extras`")
    sys.exit(1)
from loguru import logger
from app.tutorial import show_tutorial

logger.remove()
logger.add(
    sys.stderr,
    level="INFO" if os.getenv("LLMBOT_LOG_OUTPUT") != "DEBUG" else "DEBUG",
    colorize=True,
    enqueue=True,
)

logger.add(
    sink="run.log",
    format="{time} - {level} - {message}",
    level="INFO",
    rotation="100 MB",
    enqueue=True,
)
head = """
██╗     ██╗     ███╗   ███╗██╗  ██╗██╗██████╗  █████╗
██║     ██║     ████╗ ████║██║ ██╔╝██║██╔══██╗██╔══██╗
██║     ██║     ██╔████╔██║█████╔╝ ██║██████╔╝███████║
██║     ██║     ██║╚██╔╝██║██╔═██╗ ██║██╔══██╗██╔══██║
███████╗███████╗██║ ╚═╝ ██║██║  ██╗██║██║  ██║██║  ██║
╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
"""
logger.opt(record=False, exception=False, capture=False, colors=True).info(
    f"<cyan>{head}</cyan>"
)

show_tutorial(skip_existing=False, pre_step_stop=5, database_key="start_tutorial")
