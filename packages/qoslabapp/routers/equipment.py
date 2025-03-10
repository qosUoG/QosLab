import importlib
import inspect
import pkgutil
import warnings
from fastapi import APIRouter
from pydantic import BaseModel
import qoslablib

from qoslablib.runtime import EquipmentABC, ExperimentABC

from ..lib.state import AppState
from ..lib.utils import importFromStr
from qoslablib import labtype as l


router = APIRouter()


class AvailableEquipmentsPayload(BaseModel):
    names: list[str]


@router.post("/equipment/available_equipments")
async def available_equipments(payload: AvailableEquipmentsPayload):
    class EquipmentModule(BaseModel):
        modules: list[str]
        cls: str

    equipments: dict[type, EquipmentModule] = {}

    warnings.filterwarnings("ignore")

    def get_equipments(module: str):
        # First check the module is importable
        if importlib.util.find_spec(module) and not module.endswith("__main__"):
            try:
                for [cls, clsT] in inspect.getmembers(
                    importlib.import_module(module), inspect.isclass
                ):
                    if (
                        issubclass(clsT, EquipmentABC)
                        and clsT is not ExperimentABC
                        and clsT is not EquipmentABC
                    ):
                        if clsT not in equipments:
                            equipments[clsT] = {"modules": [module], "cls": cls}
                        else:
                            equipments[clsT]["modules"].append(module)
            except Exception as e:
                print(f"Path {module} produced an exception")
                print(e)

    # Check all possible paths
    for package in pkgutil.walk_packages():
        for n in payload.names:
            if package.name.startswith(n):
                get_equipments(package.name)
                break

    # TODO Check in local directory for project specific equipments

    warnings.filterwarnings("default")

    return list(equipments.values())


class GetParamPayload(BaseModel):
    module: str
    cls: str


@router.post("/equipment/get_params")
async def get_params(payload: GetParamPayload):
    return getattr(
        getattr(importlib.import_module(payload.module), payload.cls),
        "params",
    )
