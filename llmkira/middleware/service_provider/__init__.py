# -*- coding: utf-8 -*-
# @Time    : 2023/10/26 下午11:32
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm


# 这里是分发授权的地方。

__provider__ = {}

import os
from functools import wraps
from typing import Type

from dotenv import load_dotenv
from loguru import logger

from .schema import BaseProvider, ProviderSettingObj

load_dotenv()

pkg_path = os.path.dirname(__file__)
pkg_name = os.path.basename(pkg_path)

import os

__all__ = [
    f.strip(".py")
    for f in os.listdir(os.path.abspath(os.path.dirname(__file__)))
    if f.endswith('.py') and "_" not in f
]


def resign_provider():
    """
    装饰器
    """

    def decorator(func: Type[BaseProvider]):
        if issubclass(func, BaseProvider):
            logger.success(f"📦 Plugin:resign Provider {func}")
            __provider__[func.name.__str__().upper()] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(*args, **kwargs)

        return wrapper

    return decorator


from .public import PublicProvider
from .private import PrivateProvider


def setup():
    _provider_name = ProviderSettingObj.provider
    if __provider__.get(_provider_name, None):
        logger.success(f"\n️🥕 ️Use Service Provider Named:{_provider_name}")
        return __provider__.get(_provider_name)
    else:
        logger.warning(f"\n⚠ No Select Service Provider Named:{_provider_name},Use Public Provider")
        return PublicProvider


loaded_provider: Type[BaseProvider] = setup()
