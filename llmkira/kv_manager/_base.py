from abc import ABC, abstractmethod
from typing import Union

from llmkira.cache import global_cache_runtime


class KvManager(ABC):
    client = global_cache_runtime.get_client()

    @abstractmethod
    def prefix(self, key: str) -> str:
        return f"kv:{key}"

    async def read_data(self, key: str):
        data_key = self.prefix(key)
        result = await self.client.read_data(data_key)
        return result

    async def save_data(self, key: str, value: Union[str, bytes], timeout: int = None):
        data_key = self.prefix(key)
        await self.client.set_data(key=data_key, value=value, timeout=timeout)
