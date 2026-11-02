import os
import importlib
import inspect
from typing import Dict, Type, Tuple, Optional
import sys
from pathlib import Path

# Added for type hints later
from drivers.base_mouse import BaseMouse

DeviceRegistryType = Dict[Tuple[int, int], Type[BaseMouse]]

_SUPPORTED_DEVICES: DeviceRegistryType = {}

def load_drivers():
    """
    Dynamically loads all driver subclasses of BaseMouse from Muvv/drivers.
    """
    global _SUPPORTED_DEVICES
    _SUPPORTED_DEVICES.clear()
    
    current_dir = Path(__file__).resolve().parent
    drivers_dir = current_dir.parent / 'drivers'

    project_root_name = current_dir.parent.name
    
    if not os.path.exists(drivers_dir):
        print(f"Warning: Drivers directory not found at {drivers_dir}")
        return

    for root, _, files in os.walk(drivers_dir):
        for filename in files:
            if filename.endswith('.py') and not filename.startswith('__'):
                rel_path = os.path.relpath(root, drivers_dir)
                
                module_path_parts = ["drivers"]
                if rel_path != ".":
                    module_path_parts.extend(rel_path.split(os.sep))
                
                module_name = filename[:-3]
                module_path_parts.append(module_name)
                
                full_module_name = ".".join(module_path_parts)
                
                try:
                    module = importlib.import_module(full_module_name)
                    
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseMouse) and obj is not BaseMouse:
                            if hasattr(obj, 'VENDOR_ID') and hasattr(obj, 'PRODUCT_ID'):
                                _SUPPORTED_DEVICES[(obj.VENDOR_ID, obj.PRODUCT_ID)] = obj
                                
                except Exception as e:
                    # Catch and report driver loading errors, but continue
                    print(f"Error loading driver module {full_module_name}: {e}")

def get_driver_class(vid: int, pid: int) -> Optional[Type[BaseMouse]]:
    """
    Returns the driver class for a given Vendor ID and Product ID.
    Returns None if the device is not supported.
    
    Args:
        vid: Vendor ID (e.g. 0x1038)
        pid: Product ID (e.g. 0x1870)
        
    Returns:
        The driver class if found, otherwise None.
    """
    if not _SUPPORTED_DEVICES:
        load_drivers()
        
    return _SUPPORTED_DEVICES.get((vid, pid))

# Auto-load on import
load_drivers()
