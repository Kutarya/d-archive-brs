import threading

from drivers.base_mouse import BaseMouse
from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

_SUPPORTED_DEVICES = {}
_LOCK = threading.RLock()


def register_driver(driver_class):
    if not isinstance(driver_class, type) or not issubclass(driver_class, BaseMouse):
        raise TypeError("Drivers must inherit BaseMouse.")
    identity = (driver_class.VENDOR_ID, driver_class.PRODUCT_ID)
    with _LOCK:
        if identity in _SUPPORTED_DEVICES and _SUPPORTED_DEVICES[identity] is not driver_class:
            raise ValueError(f"Duplicate driver identity: {identity}")
        _SUPPORTED_DEVICES[identity] = driver_class


def load_drivers():
    with _LOCK:
        _SUPPORTED_DEVICES.clear()
        register_driver(Rival3Gen2Mouse)


def get_driver_class(vid, pid):
    with _LOCK:
        return _SUPPORTED_DEVICES.get((vid, pid))


load_drivers()
