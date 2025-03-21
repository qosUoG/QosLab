from threading import Lock
import time
from typing import Any

from qoslablib.extensions.saver import SqlSaverABC


class SqlSaverProxy:
    def __init__(
        self,
        *,
        experiment_id: str,
        title: str,
        sql_saverT: type[SqlSaverABC],
        kwargs: Any,
    ):
        # Identifier for the sql saver handler
        self.title = title
        self.experiment_id = experiment_id

        # sql_saver instance for consumer of sql_saver
        self._sql_saver = sql_saverT(save_fn=self._save_fn, **kwargs)

        self._frame_lock = Lock()
        self._frames: list[Any] = []

        self.table_name: str

    def getInsertSql(self):
        return self._sql_saver.getInsertSql(self.table_name)

    def getConfig(self):
        return self._sql_saver.config.toDict()

    # This is in main thread
    def initialize(self):
        from ..workers.sqlite3 import SqlWorker

        # Each sqlsaverhandler shall always call createconnection
        SqlWorker.createSqlConnection()

        # Create table with name and timestamp (ms)
        self._table_name = f"{self.title} timestamp:{int(time.time() * 1000)}"

        SqlWorker.runSql(self._sql_saver.getCreateTableSql(self._table_name))

    # Memory for saving

    def toOwnedFrames(self):
        with self._frame_lock:
            frames = self.frames
            self.frames = []
            return frames

    def appendFrame(self, frame: Any):
        with self._frame_lock:
            self._frames.append(frame)

    # This would be called in the other thread
    def _save_fn(self, frame: Any):
        self.appendFrame(frame)
