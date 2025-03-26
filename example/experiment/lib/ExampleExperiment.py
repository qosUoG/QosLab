from dataclasses import dataclass
import math
import random
from typing import TypedDict, override

from click import ParamType
import numpy
from qoslablib import params as p, exceptions as e, runtime as r
import time

from qoslablib.extensions.chart import XYPlot
from qoslablib.extensions.saver import XYFloatSqlSaver
from examplelib.ExampleDriver import ExampleEquipment


@dataclass
class ExampleExperiment(r.ExperimentABC):
    class ParamsType(TypedDict):
        strparam: p.StrParam
        floatparam: p.FloatParam
        intparam: p.IntParam
        boolparam: p.BoolParam
        selectstrparam: p.SelectStrParam
        selectintparam: p.SelectIntParam
        selectfloatparam: p.SelectFloatParam
        instance_equipment_param: p.InstanceEquipmentParam[ExampleEquipment]

    params: ParamType

    def __init__(self):
        # The name of the experiment assigned during runtime would be made accessible.
        # You would need it to pass to the createChart and createSqlSaver methods

        self.params: ExampleExperiment.ParamsType = {
            "strparam": p.StrParam(),
            "floatparam": p.FloatParam(suffix="W"),
            "intparam": p.IntParam(),
            "boolparam": p.BoolParam(False),
            "select_strparam": p.SelectStrParam(["option1", "option2", "option3"]),
            "select_intparam": p.SelectIntParam([1, 2, 3]),
            "select_floatparam": p.SelectFloatParam([1.1, 2.2, 3.3]),
            "instance_equipmentparam": p.InstanceEquipmentParam[ExampleEquipment](),
        }

        # This should be all of the __init__ code. For instantiation of params from the final params list, or turning on equipment, initializing equipment etc, define in the initialization method

    @override
    def initialize(self, manager: r.ManagerABC) -> int:
        # import pprint

        # pprint.pprint(self.params)

        # # You may interact with the equipment here to do initialization
        # self.params["instance_equipment_param"].instance.echo("hellow world")
        # self.params["instance_equipment_param"].instance.power = 10

        # # You would instantiate ranges, or other derived values for use in loop from params here as well
        # self.inputs = numpy.arange(self.params["intparam"].value)

        # # # After the params, instantiate charts and sql savers as needed
        self.xyplot: XYPlot = manager.createChart(
            XYPlot,
            XYPlot.kwargs(
                title="Example XY Plot",
                x_axis="index",
                y_axis="C",
                y_names=["temperature"],
                mode="append",
            ),
        )

        # self.xyplot2: XYPlot = manager.createChart(
        #     XYPlot,
        #     XYPlot.kwargs(
        #         title="Another XY Plot",
        #         x_name="indexxxx",
        #         y_names=["temperature"],
        #     ),
        # )

        self.saver: XYFloatSqlSaver = manager.createSqlSaver(
            XYFloatSqlSaver,
            XYFloatSqlSaver.kwargs(title="ExampleSqlSaver", ynames=["temperature"]),
        )

        print("initialized experiment")

        manager.suggestTotalIterations(10)

    @override
    def loop(self, index: int):
        # # In each loop, perform measurements

        # # set the power of the equipment
        # self.params["instance_equipment_param"].instance.power = self.inputs[index]
        # # Measure the "temp"
        # temp = self.params["instance_equipment_param"].instance.measureTemp()

        # # Then plot and save the data
        # # Since python's typing capability is limited, you would need to make sure you did write the correct keys yourself
        # self.xyplot.plot({"index": index, "temperature": temp})
        # self.saver.save({"index": index, "temperature": temp})

        # # This is here just to not make everything happening too quickly
        time.sleep(0.1)

        # Raise an exception such that qoslapapp knows experiment is ended
        print(f"loop: {index}")
        value = random.random()
        self.xyplot.plot(
            {
                "x": index,
                "temperature": value,
            }
        )
        print("plotted")

        self.saver.save({"x": index, "temperature": value})
        print("saved")

        if index >= 9:
            raise e.ExperimentEnded

    def stop(self):
        # define code here for clean up, for example switching off some equipment etc
        print("stopped!")
