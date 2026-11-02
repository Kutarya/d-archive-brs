import io
import threading
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from support import FakeHID, FakeRival, connected_mouse

from managers.device_runner import DeviceRunner
from managers.errors import DeviceBusy
from tools.hardware_check import main as hardware_main


class SchedulingTests(unittest.TestCase):
    def test_old_rgb_frame_cannot_follow_an_explicit_new_color(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        try:
            first = mouse.submit(((bytes([0x2B]) + bytes(63), 0),))
            self.assertTrue(handle.entered.wait(1))
            old = bytes([0x21, 255]) + bytes(62)
            mouse.submit_frame(old)
            new = bytes([0x21, 127]) + bytes(62)
            replacement = mouse.submit(((new, 0),), replace_frame=True)
            handle.release.set()
            first.result(1)
            replacement.result(1)
            mouse.transact(((bytes([0x2B]) + bytes(63), 0),))
            self.assertNotIn(old, handle.packets)
            self.assertIn(new, handle.packets)
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_busy_device_rejects_competing_command_before_any_write(self):
        runner = DeviceRunner(FakeRival)
        runner.start()
        entered, release = threading.Event(), threading.Event()

        def hold():
            with runner._command_lock:
                entered.set()
                release.wait(3)

        thread = threading.Thread(target=hold)
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            with self.assertRaises(DeviceBusy):
                runner.set_polling(500)
            self.assertEqual(runner.driver.device.packets, [])
        finally:
            release.set()
            thread.join(1)
            runner.stop()

    def test_hardware_checks_reject_missing_write_authorization(self):
        with patch("tools.hardware_check.DeviceRunner") as factory, redirect_stderr(io.StringIO()) as errors:
            with self.assertRaises(SystemExit) as result:
                hardware_main(["--mode", "color", "--device", "/dev/fake", "--color", "FF0000"])
            self.assertEqual(result.exception.code, 2)
            factory.assert_not_called()
            self.assertIn("--allow-write", errors.getvalue())
