import sys
import unittest
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.device_manager import DeviceManager
from managers.ipc_server import IPCServer


class TestEffectOptions(unittest.TestCase):
    def test_ipc_effect_options_forwarding(self):
        manager = DeviceManager()

        received_options = {}

        class MockRunner:
            def set_effect(self, effect_name, options=None):
                nonlocal received_options
                received_options = {"effect_name": effect_name, "options": options}
                return True

        manager.runners["test-dev"] = MockRunner()
        ipc = IPCServer(device_manager=manager)

        # Dispatch set-effect with color, speed and direction
        payload = {
            "command": "set-effect",
            "args": {
                "device": "test-dev",
                "effect": "wave",
                "color": [255, 0, 0],
                "speed": 2.5,
                "direction": "vertical",
            },
        }
        res = ipc._process_command(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(received_options["effect_name"], "wave")
        self.assertEqual(received_options["options"]["color"], (255, 0, 0))
        self.assertEqual(received_options["options"]["speed"], 2.5)
        self.assertEqual(received_options["options"]["direction"], "vertical")


if __name__ == "__main__":
    unittest.main()
