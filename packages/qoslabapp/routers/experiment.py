import importlib
from fastapi import APIRouter
from pydantic import BaseModel


from qoslablib.params import AllParamTypes
from qoslablib.runtime import ExperimentABC, Params

from .eeshared import getAvailableEEs, populateParam


from ..lib.state import AppState


router = APIRouter()


class AvailableExperimentsPayload(BaseModel):
    names: list[str]


@router.post("/experiment/available_experiments")
async def available_experiments(payload: AvailableExperimentsPayload):
    return getAvailableEEs(ExperimentABC, payload.names)


class GetParamsPayload(BaseModel):
    module: str
    cls: str


@router.post("/experiment/get_params")
async def get_params(payload: GetParamsPayload):
    return getattr(
        getattr(importlib.import_module(payload.module), payload.cls),
        "params",
    )


class SetParamPayload(BaseModel):
    params: Params
    # Experiment name
    experiment_name: str
    # param name


@router.post("/experiment/set_params")
async def set_params(payload: SetParamPayload):
    for [param_name, param] in payload.params.items():
        AppState.experiments[payload.experiment_name].params[param_name] = (
            populateParam(param)
        )


class StartExperimentPayload(BaseModel):
    experiment_name: str


@router.post("/experiment/start_experiment")
async def start_experiment(payload: StartExperimentPayload):
    # Run the experiments
    AppState.run_experiment(payload.experiment_name)
