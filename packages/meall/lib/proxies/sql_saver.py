import asyncio
import os
import pickle
from threading import Lock

from typing import Any, TypedDict


from cnoc.extensions.saver import SqlSaverABC

from ..settings.foundation import ExperimentStatus

from ..workers.sqlite import SqlWorker


class SqlSaverProxy:
    def __init__(
        self,
        *,
        status: ExperimentStatus,
        sql_saverT: type[SqlSaverABC],
        kwargs: Any,
    ):
        self._status = status
        # sql_saver instance for consumer of sql_saver
        self._sql_saver = sql_saverT(
            timestamp=self._status.timestamp, save_fn=self._save_fn, **kwargs
        )

        self._frames_lock = Lock()
        self._frames: list[Any] = []

        self._insert_sql = self._sql_saver.getInsertSql()

        self._should_cancel = asyncio.Event()
        self._stopped = asyncio.Event()

        # Create the table
        SqlWorker.putScript(self._sql_saver.getCreateTableSql())

        # Create the task that continuously submit put request for registering frames
        self._task = asyncio.create_task(self._worker())

    """Public Interface"""

    def getConfig(self):
        return self._sql_saver.config.toDict()

    async def cleanup(self):
        # Cancel the task
        if not self._task.done():
            self._should_cancel.set()
            await self._stopped.wait()

    """Private task to continuously submit frames to worker"""

    async def _worker(self):
        while (
            not self._should_cancel.is_set()
            and not self._status.stopped.is_set()
            and not self._status.success.is_set()
        ):
            await asyncio.sleep(2)
            self._flushFrames()

        # flush the frames one last time
        self._flushFrames()

        if self._status.success.is_set():
            # Each dataset -> experiment instance (experiment and equipment params)
            timestamp = self._status.timestamp

            data = self._sql_saver.finalize(
                await SqlWorker.putFetchall(self._sql_saver.getSelectAllSql())
            )

            meta = self._status.params_backup

            filename = f"./data/{self._sql_saver.config.title}.pickle"

            if not os.path.isfile(filename):
                with open(filename, "wb") as f:
                    pickle.dump({timestamp: {"data": data, "meta": meta}}, f)

            else:
                # Read the past data
                class Entry(TypedDict):
                    data: Any
                    meta: dict[str, dict[str, str]]

                with open(filename, "rb") as f:
                    dataset: dict[str, Entry] = pickle.load(f)

                dataset[timestamp] = {"data": data, "meta": meta}

                with open(filename, "wb") as f:
                    pickle.dump(dataset, f)

        self._stopped.set()
        return

    def _flushFrames(self):
        frames = self._toOwnedFrames()
        if frames:
            SqlWorker.putMany(self._insert_sql, frames)

    def _toOwnedFrames(self):
        with self._frames_lock:
            frames = self._frames
            self._frames = []
            return frames

    """_save_fn to be used by underlying saver"""

    def _save_fn(self, frame: Any):
        with self._frames_lock:
            self._frames.append(frame)
