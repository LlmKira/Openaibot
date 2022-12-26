# -*- coding: utf-8 -*-
# @Time    : 12/5/22 9:54 PM
# @FileName: __init__.py
# @Software: PyCharm
# @Github    ：sudoskys
from pydantic import BaseModel

from .resouce import Completion
from .Chat import Chatbot


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = None


redis = RedisConfig()
api_key = None
proxy_url = ""
webServerUrlFilter = False
