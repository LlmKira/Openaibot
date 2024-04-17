from pathlib import Path
from typing import Optional

from json_repair import repair_json
from loguru import logger

from llmkira.task.snapshot._base import BaseSnapshotStorage, SnapData

_FILE_STORAGE = Path().cwd().joinpath(".snapshot")
if not _FILE_STORAGE.exists():
    _FILE_STORAGE.mkdir()


def _make_json_file(location: str):
    if not location.endswith(".json"):
        location = f"{location}.json"
    return _FILE_STORAGE.joinpath(location)


class FileSnapshotStorage(BaseSnapshotStorage):
    # TODO:删除过期的快照防止数据过多
    async def read(self, user_id: str) -> Optional[SnapData]:
        location_file = _make_json_file(user_id)
        if not location_file.exists():
            return None
        data = repair_json(
            location_file.read_text(encoding="utf-8"), return_objects=True
        )
        if not data:
            return None
        try:
            return SnapData.model_validate(data)
        except Exception as e:
            logger.debug(e)
            return None

    async def write(self, user_id: str, snapshot: SnapData):
        location_file = _make_json_file(user_id)
        location_file.write_text(snapshot.model_dump_json(indent=2))
        return snapshot
