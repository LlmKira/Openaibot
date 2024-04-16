import asyncio
from pathlib import Path
from typing import List

from aiofile import AIOFile, Writer
from file_read_backwards import FileReadBackwards
from pydantic import BaseModel

from llmkira.memory._base import BaseMessageStorage

# 获取主机目录下的.llm_core_storage文件夹
_FILE_STORAGE = Path().home().joinpath(".llm_bot_storage")
_FILE_STORAGE.mkdir(exist_ok=True)


def _make_json_file(location: str):
    if not location.endswith(".jsonl"):
        location = f"{location}.jsonl"
    return _FILE_STORAGE.joinpath(location)


class LocalStorage(BaseMessageStorage):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.lock = asyncio.Lock()

    def update_session(self, session_id: str):
        self.session_id = session_id
        return self

    @property
    def path(self) -> Path:
        return _make_json_file(self.session_id)

    async def append(self, message: List[BaseModel]):
        async with self.lock:
            async with AIOFile(str(self.path), "a") as afp:
                writer = Writer(afp)
                for m in message:
                    _json_line = m.model_dump_json(indent=None)
                    await writer(_json_line + "\n")
            await afp.fsync()

    async def read(self, lines: int) -> List[str]:
        async with self.lock:
            result = []
            with FileReadBackwards(str(self.path), encoding="utf-8") as frb:
                for i, line in enumerate(frb):
                    if i >= lines:
                        break
                    result.append(line)
            return result

    async def write(self, message: List[BaseModel]):
        async with self.lock:
            async with AIOFile(str(self.path), "w") as afp:
                writer = Writer(afp)
                for m in message:
                    _json_line = m.model_dump_json(indent=None)
                    await writer(_json_line + "\n")
            await afp.fsync()

    async def clear(self):
        async with self.lock:
            with open(self.path, "w") as f:
                f.truncate()