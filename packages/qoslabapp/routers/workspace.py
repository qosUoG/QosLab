from ast import Import
from functools import reduce
import importlib.util
import pkgutil
from unittest.mock import Base
from xml.etree.ElementInclude import include
from fastapi import APIRouter
import os
import sys
import importlib
import inspect
from pydantic import BaseModel
from qoslablib import labtype as l
from lib.state import AppState
from lib.utils import importFromStr


router = APIRouter()


class Path(BaseModel):
    path: str


class StartExperimentsPayload(BaseModel):
    equipments: list[l.Equipment]
    experiments: list[l.Experiment]


@router.post("/workspace/start_experiments")
async def start_experiments(body: StartExperimentsPayload):
    AppState.reset_dicts()

    # Instantiate equipments
    for equipment in body.equipments:
        with open(equipment.path, mode="r", encoding="utf-8") as raw:
            # Read the definition code from the source file
            [module, classname] = importFromStr(raw.read())
            _class = getattr(module, classname)
            # Initilize the equipment and assign to equipments dict
            AppState.equipments[equipment.name] = _class(equipment.params)

    # Assign instance params to each param
    for equipment in AppState.equipments.values():
        for p in equipment.params.values():
            if p.type == "instance":
                p.instance = AppState.equipments[p.instance_name]

    # Instantiate experiments
    for experiment in body.experiments:
        with open(experiment.path, mode="r", encoding="utf-8") as raw:
            # Read the definition code from the source file
            [module, classname] = importFromStr(raw.read())
            _class = getattr(module, classname)
            # put in equipment instances into params

            for [_, p] in experiment.params.items():
                if p.type == "instance":
                    p.instance = AppState.equipments[p.instance_name]

            # Initilize the experiment and assign to experiments dict
            AppState.register_experiment(experiment.name, experiment.params, _class)

    # Start all the threads
    AppState.start_experiments()


class AvailableEquipmentsPayload(BaseModel):
    names: list[str]


@router.post("/workspace/available_equipments")
async def available_equipments(payload: AvailableEquipmentsPayload):
    class EquipmentModule(BaseModel):
        module_name: str
        equipment_name: str

    equipments: list[EquipmentModule] = []

    def get_equipments(name: str):
        # First check the name is importable
        if spec := importlib.util.find_spec(name) and not name.endswith("__main__"):
            if name.endswith("__"):
                print(name)
            try:
                for [p, module] in inspect.getmembers(importlib.import_module(name)):
                    if hasattr(module, "equipment_params"):
                        equipments.append({"module_name": p, "equipment_name": p})
            except (ImportError, ValueError):
                pass
            except Exception as e:
                print(e)
                print("name", name)
                print("spec", spec)

    # Check all possible paths
    for package in pkgutil.walk_packages():
        for n in payload.names:
            if package.name.startswith(n):
                get_equipments(package.name)
                break

        # if (spec := importlib.util.find_spec(d)) is not None:
        #     module = importlib.util.module_from_spec(spec)
        #     sys.modules[d] = module
        #     spec.loader.exec_module(module)
        #     print(f"d : {d} success")

        #     # get all the symbols and see if there is any Equipment
        #     for [s_name, s_type] in inspect.getmembers(module):
        #         print(f"s: {s_name}")
        #         for [a_name, _] in inspect.getmembers(s_type):
        #             # print(f"{s_name}.{a_name}")
        #             if a_name == "equipment_params":
        #                 equipments.append({"module_name": d, "equipment_name": s_name})
    # TODO Check in local directory for project specific equipments
    print("equipments", equipments)
    return equipments
