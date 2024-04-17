from abc import abstractmethod
from typing import List

from pydantic import BaseModel


class BaseMessageStorage(object):
    session_id: str

    @abstractmethod
    def update_session(self, session_id: str):
        self.session_id = session_id
        return self

    @abstractmethod
    async def read(self, lines: int) -> List[str]:
        ...

    @abstractmethod
    async def append(self, message: List[BaseModel]):
        _json_lines = [m.model_dump_json(indent=None) for m in message]
        ...

    @abstractmethod
    async def write(self, message: List[BaseModel]):
        _json_lines = [m.model_dump_json(indent=None) for m in message]
        ...

    @abstractmethod
    async def clear(self):
        ...
