# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午6:04
# @Author  : sudoskys
# @File    : __init__.py
# @Software: PyCharm
import os
import pkgutil

from loguru import logger

pkg_path = os.path.dirname(__file__)
pkg_name = os.path.basename(pkg_path)

"""
import os
__all__ = [f.strip(".py") for f in os.listdir(os.path.abspath(os.path.dirname(__file__))) if
           f.endswith('.py') and "_" not in f]
"""


def setup():
    logger.info("====== Plugin: setup start ======")
    for _, file, _ in pkgutil.iter_modules([pkg_path]):
        if not f"{file}" == "public":
            __import__(pkg_name + '.' + file)
            logger.debug(f"Plugin: loaded success:{file}")
    logger.info("====== Plugin: setup finish ======")
