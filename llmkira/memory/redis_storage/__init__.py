# -*- coding: utf-8 -*-
# Source: https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/utilities/redis.py
from __future__ import annotations

from typing import List

import redis
from loguru import logger
from pydantic import BaseModel
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from llmkira.memory._base import BaseMessageStorage
from llmkira.memory.redis_storage.utils import get_client


class RedisSettings(BaseSettings):
    redis_url: str = Field("redis://localhost:6379/0", validation_alias="REDIS_DSN")
    redis_key_prefix: str = "llm_message_store:"
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def redis_is_connected(self):
        redis_url = self.redis_url
        try:
            redis_client = get_client(redis_url=redis_url)
            redis_client.ping()
        except redis.exceptions.ConnectionError as error:
            logger.warning(f"Could not connect to Redis: {error}")
            raise ValueError("Could not connect to Redis")
        else:
            logger.debug("Core: Connect to Redis")
        return self


class RedisChatMessageHistory(BaseMessageStorage):
    def __init__(self, session_id: str, ttl: int, redis_config: RedisSettings = None):
        if redis_config is None:
            redis_config = RedisSettings()
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Could not import redis python package. Please install it with `pip install redis`."
            )
        try:
            self.redis_client = get_client(redis_url=redis_config.redis_url)
        except redis.exceptions.ConnectionError as error:
            logger.error(error)
        self.session_id = session_id
        self.key_prefix = redis_config.redis_key_prefix
        self.ttl = ttl

    def update_session(self, session_id: str):
        self.session_id = session_id
        return self

    @property
    def key(self) -> str:
        return self.key_prefix + self.session_id

    async def read(self, lines: int) -> List[str]:
        _items = self.redis_client.lrange(self.key, 0, lines - 1)
        items = [m.decode("utf-8") for m in _items[::-1]]
        return items

    async def append(self, messages: List[BaseModel]):
        for m in messages:
            message_json = m.model_dump_json()
            self.redis_client.lpush(self.key, message_json)
            if self.ttl:
                self.redis_client.expire(self.key, self.ttl)

    async def write(self, messages: List[BaseModel]):
        self.clear()
        self.append(messages)

    async def clear(self) -> None:
        self.redis_client.delete(self.key)
