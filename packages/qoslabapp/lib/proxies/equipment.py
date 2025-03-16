from dataclasses import dataclass
from threading import Lock

from typing import Any

from qoslablib.params import Params
from qoslablib.runtime import EquipmentABC


@dataclass
class EquipmentProxy:
    # Threading.Lock for thread safety access of Equipment

    def __init__(self, eCls: type[EquipmentABC]):
        self._equipment = eCls()
        self._lock = Lock()

    # For Type safety
    @property
    def params(self) -> Params:
        with self._lock:
            return self._equipment.params

    @params.setter
    def params(self, params: Params):
        with self._lock:
            self._equipment.params = params

    # Proxy to all underlying parameters
    def __getattr__(self, key: str):
        with self._lock:
            attr = getattr(self._equipment, key)
            if callable(attr):

                def wrap(*args, **kwargs):
                    with self._lock:
                        return attr(*args, **kwargs)

                return wrap

            return attr

    def __setattr__(self, key: str, value: Any):
        with self._lock:
            setattr(self._equipment, key, value)
