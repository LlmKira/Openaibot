from abc import abstractmethod
from typing import Optional, List

from pydantic import BaseModel

from llmkira.task.schema import Snapshot


class SnapData(BaseModel):
    data: List[Snapshot]


class BaseSnapshotStorage(object):
    @abstractmethod
    async def read(self, user_id: str) -> Optional["SnapData"]:
        ...

    @abstractmethod
    async def write(self, user_id: str, snapshot: "SnapData"):
        ...
