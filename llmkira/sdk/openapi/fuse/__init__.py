# -*- coding: utf-8 -*-
# @Time    : 2023/10/23 下午7:44
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm

####
# 此包包含错误计数器，用于统计错误次数，标记错误次数过多的插件。
# 在构造阶段读取用户数据库，合并至 ignore 中。
# 注意，注意回调的实现。
####
from typing import Dict

import wrapt
from loguru import logger

from llmkira.sdk.schema import Function

__error_table__: Dict[str, int] = {}


def get_error_plugin(error_times: int = 10):
    """
    获取错误次数过多的插件
    :param error_times: 错误次数
    :return:
    """
    return [k for k, v in __error_table__.items() if v > error_times]


def recover_error_plugin(function_name: str):
    """
    恢复错误插件
    :param function_name:
    :return:
    """
    __error_table__[function_name] = 0


def resign_plugin_executor(function: Function):
    """
    装饰器
    """
    logger.success(f"📦 Plugin:resign plugin error hook: {function.name}")

    @wrapt.decorator  # 保留被装饰函数的元信息
    def wrapper(wrapped, instance, args, kwargs):
        """
        :param wrapped: 被装饰的函数
        :param instance: https://wrapt.readthedocs.io/en/latest/
        :param args: 被装饰函数的参数
        :param kwargs: 被装饰函数的关键字参数
        :return:
        """
        try:
            res = wrapped(*args, **kwargs)
        except Exception:
            __error_table__[function.name] = __error_table__.get(function.name, 0) + 1
        else:
            return res
        return {}

    return wrapper
