import sys
import unittest
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.device_runner import DeviceRunner
from managers.device_manager import DeviceManager
from managers.ipc_server import IPCServer

class TestCapabilitiesAndInfo(unittest.TestCase):

    def test_driver_capabilities(self):
        caps = Rival3Gen2Mouse.CAPABILITIES
        self.assertIn("dpi", caps)
        self.assertIn("polling_rates", caps)
        self.assertIn("rgb", caps)
        self.assertEqual(caps["polling_rates"], [1000, 500, 250, 125])

    def test_ipc_info_command(self):
        manager = DeviceManager()
        # Mock runner
        class MockDriver:
            vendor_id = 0x1038
            product_id = 0x1870
            is_connected = True
            def get_capabilities(self):
                return Rival3Gen2Mouse.CAPABILITIES
        
        class MockRunner:
            def __init__(self):
                self.driver = MockDriver()
            def get_capabilities(self):
                return self.driver.get_capabilities()

        manager.runners["test-device-1"] = MockRunner()
        
        ipc = IPCServer(device_manager=manager)
        response = ipc._process_command({"command": "info", "args": {"device": "test-device-1"}})
        
        self.assertEqual(response["status"], "ok")
        self.assertIn("capabilities", response)
        self.assertEqual(response["capabilities"]["polling_rates"], [1000, 500, 250, 125])
        
        # Test unknown device
        err_response = ipc._process_command({"command": "info", "args": {"device": "non-existent"}})
        self.assertEqual(err_response["status"], "error")

if __name__ == "__main__":
    unittest.main()
