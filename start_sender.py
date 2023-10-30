# -*- coding: utf-8 -*-
import getopt
import os
import sys

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.remove()
logger.add(sys.stderr,
           level="INFO" if os.getenv("LLMBOT_LOG_OUTPUT") != "DEBUG" else "DEBUG",
           colorize=True,
           enqueue=True
           )

logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True
           )
head = """
██╗     ██╗     ███╗   ███╗██╗  ██╗██╗██████╗  █████╗ 
██║     ██║     ████╗ ████║██║ ██╔╝██║██╔══██╗██╔══██╗
██║     ██║     ██╔████╔██║█████╔╝ ██║██████╔╝███████║
██║     ██║     ██║╚██╔╝██║██╔═██╗ ██║██╔══██╗██╔══██║
███████╗███████╗██║ ╚═╝ ██║██║  ██╗██║██║  ██║██║  ██║
╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
"""
logger.opt(record=False, exception=False, capture=False, colors=True).info(f"<cyan>{head}</cyan>")
from llmkira.tutorial import show_tutorial

SKIP_TUTORIAL = False
SKIP_EXISTING = True
# 获取命令行参数的 --no_tutorial
opts, args = getopt.getopt(sys.argv[1:], "h", ["no_tutorial", "tutorial"])
for op, value in opts:
    if op == "--no_tutorial":
        SKIP_TUTORIAL = True
    if op == "-h":
        print("Usage: python start_receiver.py [--no_tutorial] [--tutorial]")
        sys.exit()
    if op == "--tutorial":
        SKIP_EXISTING = False
if not SKIP_TUTORIAL:
    show_tutorial(skip_existing=SKIP_EXISTING, pre_step_stop=4, database_key="01")

# 运行主程序
from llmkira.sender import app

app.run()
