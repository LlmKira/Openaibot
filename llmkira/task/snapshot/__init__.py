# 消息池
from ._base import SnapData  # noqa
from .local import FileSnapshotStorage

global_snapshot_storage: FileSnapshotStorage = FileSnapshotStorage()

__all__ = [
    "SnapData",
    "global_snapshot_storage",
]
