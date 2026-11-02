"""An isolated GUI demonstration; this transport never opens a HID device."""

import tempfile
from pathlib import Path

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.device_manager import DeviceManager
from managers.device_runner import DeviceRunner


class MemoryHID:
    def write(self, packet):
        return len(packet)

    def close(self):
        pass


class DemoMouse(Rival3Gen2Mouse):
    def connect(self):
        self.device = MemoryHID()
        self.is_connected = True
        self._start_worker()


class DemoClient:
    def __init__(self):
        self._temporary = tempfile.TemporaryDirectory(prefix="muvv-demo-")
        self.manager = DeviceManager(profile_directory=Path(self._temporary.name) / "profiles")
        self.runner = DeviceRunner(DemoMouse, device_path=b"demo")
        self.runner.start()
        self.manager.runners["demo-rival-3"] = self.runner
        self.runner.set_dpi_stages([400, 800, 1200, 2400, 3200], active=1)
        self.runner.restore_buttons(persist=False)
        self.runner.set_polling(1000)
        self.runner.set_effect("wave", {"color": [74, 210, 177], "speed": 0.5})
        self.manager.save_host_profile("demo-rival-3", "Çalışma")

    def __call__(self, command, args=None):
        return self.manager.ipc_server._process_command({"command": command, "args": args or {}})

    def close(self):
        self.manager.stop()
        self._temporary.cleanup()
