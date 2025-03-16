from threading import Lock


from typing import Any, override


from qoslablib.extensions.chart import ChartABC, ChartManagerABC
from qoslablib.extensions.saver import SqlSaverABC, SqlSaverManagerABC
from qoslablib.params import Params
from qoslablib.runtime import EquipmentABC, ExperimentABC

from .proxies.equipment import EquipmentProxy

from .proxies.experiment import ExperimentProxy

from .proxies.chart import ChartProxy
from .proxies.sql_saver import SqlSaverProxy


class AppState(ChartManagerABC, SqlSaverManagerABC):
    """
    Runtime management of Equipments
    """

    _equipments_proxies: dict[str, EquipmentProxy] = {}

    @classmethod
    def createEquipment(cls, id: str, eCls: type[EquipmentABC]):
        cls._equipments_proxies[id] = EquipmentProxy(eCls)

    @classmethod
    def getEquipmentParams(cls, id: str):
        return cls._equipments_proxies[id].params

    @classmethod
    def setEquipmentParams(cls, id: str, params: Params):
        cls._equipments_proxies[id].params = params

    @classmethod
    def removeEquipment(cls, id: str):
        del cls._equipments_proxies[id]

    """
    Runtime management of Experiments
    """
    _experiment_proxies: dict[str, ExperimentProxy] = {}

    @classmethod
    def createExperiment(cls, id: str, experimentCls: type[ExperimentABC]):
        with cls.handler_experiment_id_lock:
            cls.handler_experiment_id = id
            cls._experiment_proxies[id] = ExperimentProxy(
                id=id, experimentCls=experimentCls, holder=cls
            )

    @classmethod
    def getExperimentParams(cls, id: str):
        return cls._experiment_proxies[id].params

    @classmethod
    def getExperimentLoopCount(cls):
        return cls._experiment_proxies[id].loop_count

    @classmethod
    def setExperimentParams(cls, id: str, params: Params):
        cls._experiment_proxies[id].params = params

    @classmethod
    def removeExperiment(cls, id: str):
        if id not in cls._experiment_proxies:
            return

        # experiment should already be stopped
        if not cls._experiment_proxies[id].stopped():
            return

        del cls._experiment_proxies[id]

        # TODO run clean up of extensions

        if id in cls._chart_proxies:
            del cls._chart_proxies[id]

        if id in cls._sql_saver_proxies:
            del cls._sql_saver_proxies[id]

    @classmethod
    def startExperiment(cls, id: str):
        cls._experiment_proxies[id].start()

    @classmethod
    def getStreamingLoopCount(cls, id: str):
        return cls._experiment_proxies[id].getStreamingLoopCount()

    @classmethod
    def pauseExperiment(cls, id: str):
        cls._experiment_proxies[id].pause()

    @classmethod
    def continueExperiment(cls, id: str):
        cls._experiment_proxies[id].unpause()

    @classmethod
    def stopExperiment(cls, id: str):
        cls._experiment_proxies[id].stop()

    """
    Extension Management
    """
    handler_experiment_id_lock: Lock = Lock()
    handler_experiment_id: str

    """
    Chart management
    """

    # Manages charts by experiment id and chart name
    _chart_proxies: dict[str, dict[str, ChartProxy]] = {}

    # These creation method shall only be called in __init__ of experiments
    @classmethod
    @override
    def createChart(cls, chartT: ChartABC, kwargs: Any = {}):
        # The title should be unique
        title = kwargs["title"]

        if cls.handler_experiment_id not in cls._chart_proxies:
            cls._chart_proxies[cls.handler_experiment_id] = {}

        cls._chart_proxies[cls.handler_experiment_id][title] = ChartProxy(
            experiment_id=cls.handler_experiment_id,
            title=title,
            chartT=chartT,
            kwargs=kwargs,
        )
        return cls._chart_proxies[cls.handler_experiment_id][title].chart

    """
    Sqlsaver management
    """

    # Manages sql savers by experiment id and sql_saver name
    _sql_saver_proxies: dict[str, dict[str, SqlSaverProxy]] = {}

    @classmethod
    @override
    def createSqlSaver(cls, sql_saverT: type[SqlSaverABC], kwargs: Any = {}):
        title = kwargs["title"]

        if cls.handler_experiment_id not in cls._sql_saver_proxies:
            cls._sql_saver_proxies[cls.handler_experiment_id] = {}

        cls._sql_saver_proxies[cls.handler_experiment_id][title] = SqlSaverProxy(
            experiment_id=cls.handler_experiment_id,
            title=title,
            sql_saverT=sql_saverT,
            kwargs=kwargs,
        )

        return cls._sql_saver_proxies[cls.handler_experiment_id][title].sql_saver
