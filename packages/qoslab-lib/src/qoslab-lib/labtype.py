from pydantic import BaseModel

from qoslabpy.params import AllParamTypes


class Experiment(BaseModel):
    name: str
    path: str
    params: dict[str, AllParamTypes]


class Equipment(BaseModel):
    name: str
    path: str
    params: dict[str, AllParamTypes]
