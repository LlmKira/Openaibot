# -*- coding: utf-8 -*-
# @Time    : 2023/3/30 下午4:21
# @Author  : sudoskys
# @File    : proxy.py
# @Software: PyCharm
from typing import Set, List, Dict, Optional, Any, Union, Literal
from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    RedisDsn,
    Field, validator,
)


class ProxySetting(BaseModel):
    """
    代理设置
    """
    # 限定代理类型
    proxy_type: Literal['http', 'https', 'socks4', 'socks5', "all"] = 'http'
    # 代理地址
    proxy_address: str = None

    @validator('proxy_type')
    def check_proxy_type(cls, v):
        if v not in ['http', 'https', 'socks4', 'socks5', "all"]:
            raise ValueError("代理类型不正确")
        return v

    @property
    def proxy(self):
        if self.proxy_address:
            return f"{self.proxy_type}://{self.proxy_address}"
        else:
            return None
