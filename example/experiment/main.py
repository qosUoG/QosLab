import importlib
import inspect
import pkgutil


def main():
    print("Hello from experiment!")


if __name__ == "__main__":
    import qoslablib
    import examplelib

    for [cls, clsT] in inspect.getmembers(
        importlib.import_module("examplelib.ExampleDriver"), inspect.isclass
    ):
        print(cls)

    print("fastapi.__main__".endswith("__main__"))

    # def inside():
    #     warnings.filterwarnings("error")

    # try:
    #     inside()
    #     warnings.warn("This is a warning")
    # except Warning:
    #     print("This is a exception")

    # print(getattr(examplelib.ExampleDriver.ExampleEquipment, "equipment_params"))
    # for [p, module] in inspect.getmembers(
    #     importlib.import_module("examplelib.ExampleDriver")
    # ):
    #     if not p.startswith("__"):
    #         print(p, module)
