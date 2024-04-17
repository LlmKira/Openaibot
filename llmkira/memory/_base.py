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
    async def append(self, messages: List[BaseModel]):
        _json_lines = [m.model_dump_json(indent=None) for m in messages]
        ...

    @abstractmethod
    async def write(self, messages: List[BaseModel]):
        _json_lines = [m.model_dump_json(indent=None) for m in messages]
        ...

    @abstractmethod
    async def clear(self):
        ...
