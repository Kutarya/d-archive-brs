import sys
import unittest
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.device_manager import DeviceManager
from managers.ipc_server import IPCServer
from managers.validator import CommandValidator


class TestCommandValidator(unittest.TestCase):
    def setUp(self):
        self.caps = Rival3Gen2Mouse.CAPABILITIES

    def test_dpi_validation(self):
        # Valid levels (0 to 4)
        is_valid, msg = CommandValidator.validate_dpi(self.caps, 0)
        self.assertTrue(is_valid)
        self.assertIsNone(msg)

        is_valid, msg = CommandValidator.validate_dpi(self.caps, 4)
        self.assertTrue(is_valid)

        # Invalid levels (e.g. -1, 5, 10)
        is_valid, msg = CommandValidator.validate_dpi(self.caps, 5)
        self.assertFalse(is_valid)
        self.assertIn("Invalid DPI stage index 5", msg)

        is_valid, msg = CommandValidator.validate_dpi(self.caps, -1)
        self.assertFalse(is_valid)

    def test_polling_validation(self):
        # Valid rates (1000, 500, 250, 125)
        is_valid, msg = CommandValidator.validate_polling(self.caps, 1000)
        self.assertTrue(is_valid)

        is_valid, msg = CommandValidator.validate_polling(self.caps, 500)
        self.assertTrue(is_valid)

        # Invalid rates (e.g. 750, 2000)
        is_valid, msg = CommandValidator.validate_polling(self.caps, 750)
        self.assertFalse(is_valid)
        self.assertIn("Unsupported polling rate 750Hz", msg)

    def test_ipc_validation_rejection(self):
        manager = DeviceManager()

        class MockDriver:
            vendor_id = 0x1038
            product_id = 0x1870
            is_connected = True

            def get_capabilities(self):
                return Rival3Gen2Mouse.CAPABILITIES

            def set_dpi(self, level):
                pass

            def set_polling_rate(self, hz):
                pass

        class MockRunner:
            def __init__(self):
                self.driver = MockDriver()

            def get_capabilities(self):
                return self.driver.get_capabilities()

            def set_dpi(self, level):
                return True

            def set_polling(self, hz):
                return True

        manager.runners["test-dev"] = MockRunner()
        ipc = IPCServer(device_manager=manager)

        # Valid DPI request
        res = ipc._process_command({"command": "set-dpi", "args": {"device": "test-dev", "level": 2}})
        self.assertEqual(res["status"], "ok")

        # Invalid DPI request (level 8)
        res_invalid = ipc._process_command({"command": "set-dpi", "args": {"device": "test-dev", "level": 8}})
        self.assertEqual(res_invalid["status"], "error")
        self.assertIn("Invalid DPI stage index 8", res_invalid["message"])

        # Invalid Polling request (750Hz)
        res_polling = ipc._process_command(
            {"command": "set-polling", "args": {"device": "test-dev", "hz": 750}}
        )
        self.assertEqual(res_polling["status"], "error")
        self.assertIn("Unsupported polling rate 750Hz", res_polling["message"])


if __name__ == "__main__":
    unittest.main()
