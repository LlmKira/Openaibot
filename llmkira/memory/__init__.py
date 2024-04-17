# -*- coding: utf-8 -*-
# @Author  : sudoskys
# @File    : __init__.py

from loguru import logger

from llmkira.memory._base import BaseMessageStorage
from llmkira.memory.local_storage import LocalStorage
from llmkira.memory.redis_storage import RedisChatMessageHistory, RedisSettings

try:
    global_message_runtime: BaseMessageStorage = RedisChatMessageHistory(
        session_id="global", ttl=60 * 60 * 24, redis_config=RedisSettings()
    )
except Exception as e:
    logger.debug(f"Use local storage instead of redis storage: {type(e).__name__}")
    global_message_runtime: BaseMessageStorage = LocalStorage(session_id="global")
