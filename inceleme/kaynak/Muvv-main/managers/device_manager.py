import time
import threading
import hid
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
    
from managers.device_registry import get_driver_class
from managers.device_runner import DeviceRunner
from managers.ipc_server import IPCServer
from managers.validator import CommandValidator
from typing import Dict, List, Optional, Tuple

class DeviceManager:
    """
    The Central Manager (Daemon) for Muvv.
    
    Responsibilities:
    1. Scan for USB devices.
    2. Detect supported devices via DeviceRegistry.
    3. Manage lifecycle of DeviceRunners (Start/Stop).
    4. Handle Hotplugging (Periodic Scan).
    """


    def __init__(self, scan_interval: float = 2.0):
        """
        Initialize the Device Manager.
        
        Args:
            scan_interval: Time in seconds between device scans.
        """
        self.scan_interval = scan_interval
        self._stop_event = threading.Event()
        self._scan_thread: Optional[threading.Thread] = None
        
        # Active Runners
        # Key: device_path (str) -> Value: DeviceRunner instance
        self.runners: Dict[str, DeviceRunner] = {}
        
        # IPC Server for CLI communication
        self.ipc_server = IPCServer(device_manager=self)
        
        self.is_running = False

    def start(self):
        """
        Starts the background scanning thread.
        """
        if self.is_running:
            print("DeviceManager is already running.")
            return

        print("Starting DeviceManager Daemon...")
        self._stop_event.clear()
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()
        
        self.ipc_server.start()
        
        self.is_running = True

    def stop(self):
        """
        Stops the scanning thread and all active device runners.
        """
        print("Stopping DeviceManager...")
        self._stop_event.set()
        
        self.ipc_server.stop()
        
        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=2.0)
            
        # Stop all runners
        for path, runner in list(self.runners.items()):
            print(f"Stopping runner for device at {path}")
            runner.stop()
        
        self.runners.clear()
        self.is_running = False
        print("DeviceManager stopped.")

    def _scan_loop(self):
        """
        Periodically scans for new devices and removes disconnected ones.
        """
        while not self._stop_event.is_set():
            try:
                self._scan_devices()
            except Exception as e:
                print(f"Error in scan loop: {e}")
            
            time.sleep(self.scan_interval)

    def _scan_devices(self):
        """
        Uses hidapi to enumerate current devices and syncs with self.runners.
        """
        current_devices_info = []
        
        try:
            # Enumerate all HID devices
            # We don't filter by VID/PID here because we want to check against our FULL registry
            all_devices = hid.enumerate()
            
            for d in all_devices:
                vid = d['vendor_id']
                pid = d['product_id']
                path = d['path'] # Unique identifier for the OS
                
                # Check if this device is supported
                driver_class = get_driver_class(vid, pid)
                
                if driver_class:
                    if hasattr(driver_class, 'INTERFACE_NUM'):
                        if d.get('interface_number', -1) != driver_class.INTERFACE_NUM:
                            continue

                    current_devices_info.append((path, vid, pid, driver_class))
                    
        except Exception as e:
            print(f"HID Enumeration Error: {e}")
            return

        # 1. Detect New Devices
        for path, vid, pid, driver_cls in current_devices_info:
            # decode path to string if bytes (hidapi returns bytes on some OS)
            if isinstance(path, bytes):
                path_str = path.decode('utf-8', errors='ignore')
            else:
                path_str = path

            if path_str not in self.runners:
                print(f"New Device Detected: VID={hex(vid)}, PID={hex(pid)} at {path_str}")
                
                # Create and Start Runner
                runner = DeviceRunner(driver_cls, device_path=path) 
                
                runner.start()
                self.runners[path_str] = runner

        # 2. Detect Disconnected Devices
        # Convert current paths to a set for O(1) lookup
        current_paths = set()
        for path, _, _, _ in current_devices_info:
             if isinstance(path, bytes):
                current_paths.add(path.decode('utf-8', errors='ignore'))
             else:
                current_paths.add(path)

        for path in list(self.runners.keys()):
            if path not in current_paths:
                print(f"Device Disconnected: {path}")
                self.runners[path].stop()
                del self.runners[path]

    # --- IPC Callbacks ---
    
    def resolve_device_id(self, identifier: Optional[str]) -> Optional[str]:
        """
        Resolves a friendly identifier ('default', '1', '2', partial name, or full ID)
        to an active runner's device_id.
        """
        if not self.runners:
            return None

        active_ids = list(self.runners.keys())
        
        if not identifier or str(identifier).strip().lower() in ("default", "@default", "first"):
            return active_ids[0]

        identifier_str = str(identifier).strip()

        if identifier_str in self.runners:
            return identifier_str

        try:
            idx = int(identifier_str)
            if 1 <= idx <= len(active_ids):
                return active_ids[idx - 1]
            elif idx == 0:
                return active_ids[0]
        except ValueError:
            pass

        for dev_id, runner in self.runners.items():
            dev_name = runner.driver.__class__.__name__.lower() if runner.driver else ""
            if identifier_str.lower() in dev_id.lower() or identifier_str.lower() in dev_name:
                return dev_id

        return None

    def get_active_devices(self) -> List[Dict]:
        """Returns a list of all currently active/connected devices with index numbers."""
        devices = []
        for idx, (path, runner) in enumerate(self.runners.items(), start=1):
            dev_info = {
                "index": idx,
                "id": path,
                "name": runner.driver.__class__.__name__ if runner.driver else "Unknown"
            }
            devices.append(dev_info)
        return devices
        
    def set_device_effect(self, device_id: str, effect_name: str, options: dict = None) -> bool:
        """Sets an effect on a specific device."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False
            
        print(f"Instructing DeviceRunner {resolved_id} to set effect '{effect_name}'")
        return self.runners[resolved_id].set_effect(effect_name, options)
        
    def set_device_color(self, device_id: str, hex_color: str) -> bool:
        """Sets a static color on a specific device."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False
            
        print(f"Instructing DeviceRunner {resolved_id} to set color '{hex_color}'")
        return self.runners[resolved_id].set_color(hex_color)

    def set_device_dpi(self, device_id: str, level: int) -> Tuple[bool, str]:
        """Sets the active DPI level on a specific device after validation."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False, f"Device '{device_id}' not found."

        runner = self.runners[resolved_id]
        caps = runner.get_capabilities()
        is_valid, err_msg = CommandValidator.validate_dpi(caps, level)
        if not is_valid:
            return False, err_msg

        print(f"Instructing DeviceRunner {resolved_id} to set DPI level {level}")
        success = runner.set_dpi(level)
        if success:
            return True, f"Set DPI level {level} on {resolved_id}"
        return False, f"Failed to set DPI on hardware."

    def set_device_polling(self, device_id: str, hz: int) -> Tuple[bool, str]:
        """Sets the polling rate (Hz) on a specific device after validation."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False, f"Device '{device_id}' not found."

        runner = self.runners[resolved_id]
        caps = runner.get_capabilities()
        is_valid, err_msg = CommandValidator.validate_polling(caps, hz)
        if not is_valid:
            return False, err_msg

        print(f"Instructing DeviceRunner {resolved_id} to set polling rate to {hz}Hz")
        success = runner.set_polling(hz)
        if success:
            return True, f"Set polling rate {hz}Hz on {resolved_id}"
        return False, f"Failed to set polling rate on hardware."

    def bind_device_key(self, device_id: str, button: str, key_code: int) -> bool:
        """Binds a keyboard key to a button on a specific device."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False

        print(f"Instructing DeviceRunner {resolved_id} to bind {button} -> key_code {key_code}")
        return self.runners[resolved_id].bind_key(button, key_code)

    def save_device_profile(self, device_id: str) -> bool:
        """Saves current configuration to on-board memory for a specific device."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return False

        print(f"Instructing DeviceRunner {resolved_id} to save profile to on-board memory")
        return self.runners[resolved_id].save_profile()

    def get_device_capabilities(self, device_id: str) -> Optional[dict]:
        """Returns the hardware capabilities dictionary for a specific device."""
        resolved_id = self.resolve_device_id(device_id)
        if not resolved_id:
            return None
        return self.runners[resolved_id].get_capabilities()


if __name__ == "__main__":
    # Simple Test when run directly
    manager = DeviceManager()
    try:
        manager.start()
        print("Manager running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
    finally:
        manager.stop()
