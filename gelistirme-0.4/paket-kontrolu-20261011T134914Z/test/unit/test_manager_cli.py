import io
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

from support import FakeRival

import cli
from managers.device_manager import DeviceManager
from managers.device_runner import DeviceRunner
from managers.errors import AmbiguousDevice, DeviceBusy, TransportError


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.entry = {"vendor_id": 0x1038, "product_id": 0x1870, "interface_number": 3, "path": b"/dev/fake"}
        self.manager = DeviceManager(
            enumerate_devices=lambda: [self.entry],
            runner_factory=lambda _, device_path: DeviceRunner(FakeRival, device_path),
        )

    def tearDown(self):
        self.manager.stop()

    def test_connection_failure_is_not_listed_and_is_retried(self):
        attempts = []

        def factory(driver, device_path):
            runner = DeviceRunner(FakeRival, device_path)
            attempts.append(runner)
            if len(attempts) == 1:
                runner.start = lambda: (_ for _ in ()).throw(TransportError("busy"))
            return runner

        self.manager._runner_factory = factory
        self.manager._scan_devices()
        self.assertEqual(self.manager.get_active_devices(), [])
        self.manager._retry["/dev/fake"]["next_attempt"] = 0
        self.manager._scan_devices()
        self.assertEqual(len(self.manager.get_active_devices()), 1)
        self.assertEqual(len(attempts), 2)

    def test_disconnect_removes_runner_and_closes_worker(self):
        self.manager._scan_devices()
        runner = self.manager.runners["/dev/fake"]
        handle = runner.driver.device
        self.manager._enumerate_devices = lambda: []
        self.manager._scan_devices()
        self.assertEqual(self.manager.get_active_devices(), [])
        self.assertTrue(handle.closed)
        self.assertFalse(runner.driver.status()["worker_alive"])

    def test_enumeration_error_does_not_remove_healthy_device(self):
        self.manager._scan_devices()
        self.manager._enumerate_devices = lambda: (_ for _ in ()).throw(OSError("scan unavailable"))
        with self.assertRaises(OSError):
            self.manager._scan_devices()
        self.assertEqual(len(self.manager.get_active_devices()), 1)

    def test_ambiguous_names_are_rejected_and_indices_are_stable(self):
        self.manager._scan_devices()
        other = DeviceRunner(FakeRival, b"/dev/another")
        other.start()
        self.manager.runners["/dev/another"] = other
        with self.assertRaises(AmbiguousDevice):
            self.manager.resolve_device_id("FakeRival")
        self.assertEqual(self.manager.resolve_device_id("1"), "/dev/another")
        self.assertEqual(self.manager.resolve_device_id("/dev/fake"), "/dev/fake")

    def test_ipc_start_failure_does_not_start_scanning(self):
        with patch.object(self.manager.ipc_server, "start", side_effect=TransportError("socket busy")):
            with self.assertRaises(TransportError):
                self.manager.start()
        self.assertIsNone(self.manager._scan_thread)
        self.assertFalse(self.manager.is_running)
        self.assertEqual(self.manager.runners, {})

    def test_reconnect_cannot_be_replaced_by_a_concurrent_scan(self):
        self.manager._scan_devices()
        runner = self.manager.runners["/dev/fake"]
        entered, release, scanned = threading.Event(), threading.Event(), threading.Event()
        original_start = runner.start

        def delayed_start():
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Reconnect test timed out.")
            return original_start()

        def scan():
            try:
                self.manager._scan_devices()
            finally:
                scanned.set()

        with patch.object(runner, "start", side_effect=delayed_start):
            reconnect = threading.Thread(target=self.manager.reconnect_device, args=("/dev/fake",))
            reconnect.start()
            scan_thread = threading.Thread(target=scan)
            try:
                self.assertTrue(entered.wait(1))
                scan_thread.start()
                self.assertFalse(scanned.wait(0.05))
            finally:
                release.set()
                reconnect.join(2)
                if scan_thread.ident is not None:
                    scan_thread.join(2)
        self.assertTrue(scanned.is_set())
        self.assertIs(self.manager.runners["/dev/fake"], runner)
        self.assertTrue(runner.driver.is_connected)

    def test_reconnect_rejects_busy_scan_before_touching_device(self):
        self.manager._scan_devices()
        runner = self.manager.runners["/dev/fake"]
        with patch.object(runner, "reconnect") as reconnect:
            self.manager._scan_lock.acquire()
            try:
                with self.assertRaises(DeviceBusy):
                    self.manager.reconnect_device("/dev/fake")
            finally:
                self.manager._scan_lock.release()
        reconnect.assert_not_called()

    def test_shutdown_during_connect_tracks_a_blocked_worker(self):
        runner = Mock()
        runner.driver.status.return_value = {"worker_alive": True}
        runner.start.side_effect = lambda: self.manager._stop_event.set() or True
        runner.stop.return_value = False
        self.manager._runner_factory = Mock(return_value=runner)
        self.manager._scan_devices()
        self.assertEqual(self.manager.runners, {})
        self.assertIs(self.manager._retired["/dev/fake"], runner)
        self.manager._stop_event.clear()
        self.manager._scan_devices()
        self.manager._runner_factory.assert_called_once()
        runner.stop.return_value = True


class CLITests(unittest.TestCase):
    def invoke(self, arguments, response):
        output, error = io.StringIO(), io.StringIO()
        with (
            patch("cli.send_command", return_value=response) as send,
            redirect_stdout(output),
            redirect_stderr(error),
        ):
            result = cli.main(arguments)
        return result, output.getvalue(), error.getvalue(), send

    def test_exit_codes_and_json_errors(self):
        result, output, _, _ = self.invoke(
            ["list", "--json"], {"status": "error", "code": "busy", "message": "busy"}
        )
        self.assertEqual(result, 1)
        self.assertIn('"status": "error"', output)
        self.assertEqual(self.invoke(["list"], {"status": "ok", "devices": []})[0], 0)

    def test_dpi_stages_hex_key_and_persistence_flags_are_typed(self):
        _, _, _, send = self.invoke(
            ["set-dpi-stages", "400", "800", "1200", "2400", "3200", "-d", "2", "--active", "3"],
            {"status": "ok"},
        )
        self.assertEqual(
            send.call_args.args[1], {"stages": [400, 800, 1200, 2400, 3200], "active": 3, "device": "2"}
        )
        _, _, _, send = self.invoke(
            ["bind-key", "button4", "0xE1", "--no-persist", "-d", "2"], {"status": "ok"}
        )
        self.assertEqual(send.call_args.args[1]["key_code"], 225)
        self.assertFalse(send.call_args.args[1]["persist"])

    def test_legacy_device_first_effect_and_color_forms(self):
        _, _, _, send = self.invoke(["set-effect", "2", "breathing", "--color", "FF0000"], {"status": "ok"})
        self.assertEqual(send.call_args.args[1]["device"], "2")
        _, _, _, send = self.invoke(["set-color", "2", "FF0000"], {"status": "ok"})
        self.assertEqual(send.call_args.args[1]["color"], [255, 0, 0])

    def test_invalid_effect_options_fail_before_connecting(self):
        result, _, _, send = self.invoke(["set-effect", "wave", "--wave-length", "0"], {"status": "ok"})
        self.assertEqual(result, 1)
        send.assert_not_called()

    def test_canonical_numeric_dpi_order_is_not_rewritten(self):
        _, _, _, send = self.invoke(["set-dpi", "2", "1"], {"status": "ok"})
        self.assertEqual(send.call_args.args[1]["level"], 2)
        self.assertEqual(send.call_args.args[1]["device"], "1")
