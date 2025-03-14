from asyncio import Task
import asyncio
from dataclasses import dataclass
from sqlite3 import Connection, Cursor
import sqlite3
from threading import Event, Lock
import time

from typing import Any, TypedDict, override
from fastapi import WebSocket
from qoslablib import (
    exceptions as e,
    runtime as r,
)
from qoslablib.extensions import chart as c, saver as s


class AppState(c.ChartHolderABC, s.SqlSaverHolderABC):
    """
    Runtime management of Equipments and Experiments
    """

    equipments: dict[str, r.EquipmentABC] = {}

    @dataclass
    class ExperimentHandler:
        id: str
        experiment: r.ExperimentABC
        
        stop_event = Event()
        pause_event = Event()
        
        total_loop: int = 0
        index: int = 0
        
        
        running = False
        paused = False
        completed = False

        class Message(TypedDict):
            key: str
            value: str

        _message_queue = list[Message]

        def appendMessage(self, message):
            self._message_queue.append(message)

        def startExperiment(self):
               # Run initialization of sql savers of the experiment if needed
            if self.id in AppState.sql_saver_handlers:
                for sql_saver_handler in AppState.sql_saver_handlers[self.id].values():
                    sql_saver_handler.sql_saver.initialize()

            AppState.experiment_stop_events[self.id] = Event()
            AppState.experiment_pause_events[self.id] = Event()
            AppState.experiment_tasks[self.id] = asyncio.create_task(
                asyncio.to_thread(
                    self._experiment_runner,
                    args=( 
                        self.id,
                        self.experiment,
                        self.stop_event,
                        self.pause_event
                    )
                )
            )
            pass

        @classmethod
        def _experiment_runner(
            id: str, experiment: r.ExperimentABC, stop_event: Event, pause_event: Event
        ):
            # First run the inialize method
            experiment.initialize()

            # Initialize the charts of the experiment
            if id in AppState.chart_handlers:
                for chart_handler in AppState.chart_handlers[id].values():
                    chart_handler.chart.initialize()

            # Initialize the sql_savers of the experiment
            if id in AppState.sql_saver_handlers:
                for sql_saver_handler in AppState.sql_saver_handlers[id].values():
                    sql_saver_handler.sql_saver.initialize()

            index = 0
            while True:
                if stop_event.is_set():
                    print("experiment stopped")
                    experiment.stop()
                    return

                if not pause_event.is_set():
                    try:
                        experiment.loop(index)
                        index += 1

                    except e.ExperimentEnded:
                        print("experiment ended")
                        return

    experiments: dict[str, r.ExperimentABC] = {}

    @classmethod
    def createEquipment(cls, id: str, equipmentCls: type[r.EquipmentABC]):
        AppState.equipments[id] = equipmentCls()

    @classmethod
    def createExperiment(cls, id: str, experimentCls: type[r.ExperimentABC]):
        with AppState.handler_experiment_id_lock:
            AppState.handler_experiment_id = id
            AppState.experiments[id] = experimentCls(AppState)

    @classmethod
    def removeEquipment(cls, id: str):
        del AppState.equipments[id]

    @classmethod
    def removeExperiment(cls, id: str):
        del AppState.experiments[id]

        if id in AppState.chart_handlers:
            del AppState.chart_handlers[id]

        if id in AppState.sql_saver_handlers:
            del AppState.sql_saver_handlers[id]

    @classmethod
    def startExperiment(cls, id: str):
     

    @classmethod
    def pauseExperiment(cls, id: str):
        cls.experiment_pause_events[id].set()

    @classmethod
    def continueExperiment(cls, id: str):
        cls.experiment_pause_events[id].clear()

    @classmethod
    def stopExperiment(cls, id: str):
        cls.experiment_stop_events[id].set()

    # utilities related experiments
    experiment_tasks: dict[str, Task] = {}
    experiment_stop_events: dict[str, Event] = {}
    experiment_pause_events: dict[str, Event] = {}
    """
    Extension Management
    """
    handler_experiment_id_lock: Lock = Lock()
    handler_experiment_id: str

    """
    Chart management
    """

    class _ChartHandler[FrameT]:
        def __init__(
            self, experiment_id: str, title: str, chartT: type[c.ChartABC], kwargs: Any
        ):
            self.title = title
            self.frames: list[FrameT] = []

            self.experiment_id = experiment_id

            self._lock = Lock()

            self.rate = 1
            self.connections: list[WebSocket] = []

            self.has_listener = Event()

            def _initialize_fn():
                pass

            def _plot_fn(frame: FrameT):
                if not AppState.chart_handlers[experiment_id][
                    title
                ].has_listener.is_set():
                    with AppState.chart_handlers[experiment_id][title]._lock:
                        AppState.chart_handlers[experiment_id][title].frames.append(
                            frame
                        )

            self.chart = chartT(
                initialize_fn=_initialize_fn, plot_fn=_plot_fn, **kwargs
            )

    # Manages charts by experiment id and chart name
    chart_handlers: dict[str, dict[str, _ChartHandler]] = {}

    @classmethod
    @override
    def createChart[T: c.ChartABC, KW](cls, chartT: T, kwargs: KW = {}):
        print(kwargs)
        # The title should be unique
        title = kwargs["title"]

        if cls.handler_experiment_id not in cls.chart_handlers:
            cls.chart_handlers[cls.handler_experiment_id] = {}

        cls.chart_handlers[cls.handler_experiment_id][title] = cls._ChartHandler(
            cls.handler_experiment_id, title, chartT, kwargs
        )
        return cls.chart_handlers[cls.handler_experiment_id][title].chart

    """
    Sqlsaver management
    """

    class _SqlSaverHandler[FrameT]:
        def __init__(
            self,
            experiment_id: str,
            title: str,
            sql_saverT: type[s.SqlSaverABC],
            kwargs: Any,
        ):
            self.title = title
            self.frames: list[FrameT] = []

            self._lock = Lock()
            self.experiment_id = experiment_id

            self.table_name = ""

            def _save_fn(frame: FrameT):
                with AppState.sql_saver_handlers[experiment_id][title]._lock:
                    AppState.sql_saver_handlers[experiment_id][title].frames.append(
                        frame
                    )

            def _initialize_fn():
                # Create table with name and timestamp (ms)
                table_name = f"{title} timestamp:{int(time.time() * 1000)}"
                sql = AppState.sql_saver_handlers[experiment_id][
                    title
                ].sql_saver.getCreateTableSql(table_name)
                print(sql)

                AppState.SqlWorker.sqlite3_cursor.executescript(sql)

            self.sql_saver = sql_saverT(
                initialize_fn=_initialize_fn, save_fn=_save_fn, **kwargs
            )

    # Manages sql savers by experiment id and sql saver name
    sql_saver_handlers: dict[str, dict[str, _SqlSaverHandler]] = {}

    @classmethod
    @override
    def createSqlSaver(cls, sql_saverT: type[s.SqlSaverABC], kwargs: Any = {}):
        # Create database connection if not yet created
        cls._startSqlWorker()

        title = kwargs["title"]

        if AppState.handler_experiment_id not in AppState.sql_saver_handlers:
            AppState.sql_saver_handlers[AppState.handler_experiment_id] = {}

        cls.sql_saver_handlers[AppState.handler_experiment_id][title] = (
            cls._SqlSaverHandler(
                AppState.handler_experiment_id, title, sql_saverT, kwargs
            )
        )
        return cls.sql_saver_handlers[AppState.handler_experiment_id][title].sql_saver

    """
    Sql worker
    """

    # Task for running sql_worker indefinetly
    sql_worker_task: Task
    sql_worker_task_created = False

    class SqlWorker:
        sqlite3_connection: Connection
        sqlite3_cursor: Cursor
        sqlite3_continuous_insert: Event

        @classmethod
        def createSqlConnection(cls):
            cls.sqlite3_connection = sqlite3.connect("data.db")
            cls.sqlite3_cursor = cls.sqlite3_connection.cursor()

        @classmethod
        def continuousSqlInsertWorker(cls):
            time.sleep(5)
            for sql_saver_handlers in AppState.sql_saver_handlers.values():
                for sql_saver_handler in sql_saver_handlers.values():
                    with sql_saver_handler._lock:
                        cls.sqlite3_cursor.executemany(
                            sql_saver_handler.sql_saver.getInsertSql(
                                sql_saver_handler.table_name
                            ),
                            sql_saver_handler.frames,
                        )
                        sql_saver_handler.frames.clear()

            cls.sqlite3_connection.commit()

    @classmethod
    def _startSqlWorker(cls):
        if cls.sql_worker_task_created:
            return

        def sqlWorker():
            sqlWorker = AppState.SqlWorker()
            sqlWorker.createSqlConnection()
            while True:
                sqlWorker.continuousSqlInsertWorker()

        # Start the thread that continuously check for data to commit
        cls.sql_worker_task = asyncio.create_task(asyncio.to_thread(sqlWorker))

        cls.sql_worker_task_created = True
