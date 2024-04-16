# 消息池
from .local import FileSnapshotStorage

global_snapshot_storage: FileSnapshotStorage = FileSnapshotStorage()
