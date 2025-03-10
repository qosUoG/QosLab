from pydantic import BaseModel
from qoslablib import params as p, exceptions as e, runtime as r
import time
from examplelib.ExampleDriver import ExampleEquipment


class Examplexperiment(r.ExperimentABC):
    class ParamsType(BaseModel):
        strparam: p.StrParam
        floatparam: p.FloatParam
        intparam: p.IntParam
        boolparam: p.BoolParam
        selectstrparam: p.SelectStrParam
        selectintparam: p.SelectIntParam
        selectfloatparam: p.SelectFloatParam
        instanceparam: p.InstanceParam

    params: ParamsType = {
        "strparam": p.str_param(),
        "floatparam": p.float_param(suffix="W"),
        "intparam": p.int_param(),
        "boolparam": p.bool_param(False),
        "selectstrparam": p.select_str_param(["option1", "option2", "option3"]),
        "selectintparam": p.select_int_param([1, 2, 3]),
        "selectfloatparam": p.select_float_param([1.1, 2.2, 3.3]),
        "instanceparam": p.instance_param(),
    }

    def __init__(self, params: ParamsType):
        self.params = params
        # Other initialisation code below
        import pprint

        pprint.pp(self.params)

    def loop(self, index: int):
        if index >= 10:
            raise e.ExperimentEnded
        print(self.params["instanceparam"].square(index))
        time.sleep(1)
