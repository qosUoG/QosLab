import asyncio
from contextlib import redirect_stderr, redirect_stdout
import importlib
from io import StringIO
import sys
from types import CoroutineType, ModuleType
from typing import Any
from fastapi import WebSocket
from cnoc.params import Params

from ..proxies.saver import SqlWorker

from ..proxies.experiment import ExperimentProxy
from cnoc.equipment import EquipmentABC
from ..proxies.equipment import EquipmentProxy


class AppState:
    """Equipments Experiments shared code"""

    @classmethod
    def importModule(
        cls,
        list: list[ModuleType],
        module_str: str,
    ):
        module = importlib.import_module(module_str)
        if module in list:
            list.remove(module)
            module = importlib.reload(module)
        list.append(module)
        return module

    """
    Equipments 
    """

    _equipment_proxies: dict[str, EquipmentProxy[EquipmentABC]] = {}
    _equipment_imported_modules: list[ModuleType] = []

    @classmethod
    def createEquipment(cls, id: str, module_str: str, ecls_str: str):
        module = cls.importModule(cls._equipment_imported_modules, module_str)
        cls._equipment_proxies[id] = EquipmentProxy(getattr(module, ecls_str))

    @classmethod
    def getEquipment(cls, id: str):
        return cls._equipment_proxies[id]

    @classmethod
    def getEquipmentParams(cls, id: str):
        with cls._equipment_proxies[id].lock() as equipment:
            return equipment.params

    @classmethod
    def setEquipmentParams(cls, id: str, params: Params):
        with cls._equipment_proxies[id].lock() as equipment:
            equipment.params = params

    @classmethod
    def removeEquipment(cls, id: str):
        if id in cls._equipment_proxies:
            del cls._equipment_proxies[id]

    """
    Experiments 
    """
    _experiment_proxies: dict[str, ExperimentProxy] = {}
    _experiment_imported_modules: list[ModuleType] = []

    @classmethod
    def createExperiment(cls, id: str, module_str: str, ecls_str: str):
        module = cls.importModule(cls._experiment_imported_modules, module_str)

        cls._experiment_proxies[id] = ExperimentProxy(
            id=id,
            experimentCls=getattr(module, ecls_str),
        )

    @classmethod
    def setExperimentParams(cls, id: str, params: Params):
        cls._experiment_proxies[id].params = params

    @classmethod
    def getExperimentParams(cls, id: str):
        return cls._experiment_proxies[id].params

    @classmethod
    def removeExperiment(cls, id: str):
        if id not in cls._experiment_proxies:
            return

        if not cls._experiment_proxies[id].removable():
            raise Exception("Experiment that is running cannot be removed")

        del cls._experiment_proxies[id]

    @classmethod
    def startExperiment(cls, id: str):
        cls._experiment_proxies[id].start()

    @classmethod
    def pauseExperiment_sync(cls, id: str):
        cls._experiment_proxies[id].pause_sync()

    @classmethod
    def continueExperiment(cls, id: str):
        cls._experiment_proxies[id].unpause()

    @classmethod
    def stopExperiment_async(cls, id: str):
        cls._experiment_proxies[id].stop_async()

    @classmethod
    def subscribeExperimentMessage(cls, id: str, ws: WebSocket):
        return cls._experiment_proxies[id].subscribeMessage(ws)

    """Experiment Extensions"""

    @classmethod
    def subscribeChart(cls, id: str, title: str, ws: WebSocket):
        return cls._experiment_proxies[id].subscribeChart(title, ws)

    """App Life cycle"""

    @classmethod
    def start(cls):
        # Start the worker
        SqlWorker.start()

    @classmethod
    async def kill(cls):
        """This function is meant to be stopping gracefully. Timeout should be handled outside of this function"""

        # First stop async for each function
        coros: list[CoroutineType[Any, Any, Any]] = []
        for experiment_proxy in cls._experiment_proxies.values():
            coros.append(experiment_proxy.kill())

        for equipment_proxy in cls._equipment_proxies.values():
            equipment_proxy.cleanup()

        await asyncio.gather(*coros, SqlWorker.stop())

    """CLI"""

    @classmethod
    def interpret(cls, code: str):
        try:
            return {
                "type": "eval",
                "result": f"{eval(code, globals=globals())}",
            }

        except SyntaxError:
            pass
        except Exception as e:
            return {
                "type": "error",
                "result": f"code: {code}, error:{e}",
            }

        try:
            f = StringIO()

            with redirect_stdout(f):
                with redirect_stderr(sys.stdout):
                    exec(code, globals=globals())

            return {
                "type": "exec",
                "result": f.getvalue(),
            }

        except Exception as e:
            return {
                "type": "error",
                "result": f"code: {code}, error:{e}",
            }

    @classmethod
    def eqiupment_interpret(cls, *, id: str, name: str, code: str, type: str):
        return cls._equipment_proxies[id].interpret(code, name)
