import threading
import time
import unittest
from unittest.mock import Mock

from support import FakeHID, FakeRival, connected_mouse

from drivers.base_mouse import BaseMouse
from managers.device_manager import DeviceManager
from managers.device_runner import DeviceRunner
from managers.errors import DeviceBusy, ProtocolError, TransportError, ValidationError
from managers.ipc_server import IPCServer


class LifecycleTests(unittest.TestCase):
    def test_queue_timeout_cancels_only_unstarted_operation(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        first_packet, cancelled_packet = bytes([0x2B]) + bytes(63), bytes([0x34]) + bytes(63)
        try:
            first = mouse.submit(((first_packet, 0),))
            self.assertTrue(handle.entered.wait(1))
            mouse.WRITE_TIMEOUT = 0.03
            with self.assertRaises(DeviceBusy):
                mouse.transact(((cancelled_packet, 0),))
            self.assertFalse(mouse.status()["state_uncertain"])
            self.assertTrue(mouse.is_connected)
            handle.release.set()
            first.result(1)
            mouse.WRITE_TIMEOUT = 1
            mouse.transact(((bytes([0x21]) + bytes(63), 0),))
            self.assertNotIn(cancelled_packet, handle.packets)
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_failure_closes_worker_and_rejects_remaining_queue(self):
        mouse = connected_mouse(FakeHID(block=True, fail_on=0))
        handle = mouse.device
        try:
            first = mouse.submit(((bytes(64), 0),))
            self.assertTrue(handle.entered.wait(1))
            pending = mouse.submit(((bytes([1]) + bytes(63), 0),))
            mouse.submit_frame(bytes([2]) + bytes(63))
            handle.release.set()
            for future in (first, pending):
                with self.assertRaises(TransportError):
                    future.result(1)
            self.assertTrue(mouse.disconnect())
            self.assertEqual(handle.packets, [])
            self.assertTrue(handle.closed)
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_report_iterator_and_delays_have_bounded_validation(self):
        examined = []

        def reports():
            for index in range(10000):
                examined.append(index)
                yield bytes(64), 0

        with self.assertRaises(ValidationError):
            BaseMouse._validate_packets(reports())
        self.assertEqual(len(examined), 17)
        for delay in (True, float("nan"), float("inf"), -1, 2):
            with self.subTest(delay=delay), self.assertRaises(ValidationError):
                BaseMouse._validate_packets(((bytes(64), delay),))

    def test_stop_does_not_wait_indefinitely_for_command_lock(self):
        runner = DeviceRunner(FakeRival)
        runner.start()
        entered, release = threading.Event(), threading.Event()

        def hold():
            with runner._command_lock:
                entered.set()
                release.wait(3)

        worker = threading.Thread(target=hold)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            started = time.monotonic()
            self.assertFalse(runner.stop(timeout=0.03))
            self.assertLess(time.monotonic() - started, 0.3)
        finally:
            release.set()
            worker.join(1)
            self.assertTrue(runner.stop())

    def test_connect_completing_after_stop_cannot_restart_rendering(self):
        entered, release = threading.Event(), threading.Event()
        failures = []

        class DelayedRival(FakeRival):
            def connect(self):
                entered.set()
                release.wait(3)
                super().connect()

        runner = DeviceRunner(DelayedRival)

        def start():
            try:
                runner.start()
            except TransportError as error:
                failures.append(error)

        worker = threading.Thread(target=start)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertFalse(runner.stop(timeout=0.03))
            release.set()
            worker.join(1)
            self.assertEqual(len(failures), 1)
            self.assertFalse(runner.is_running)
            self.assertFalse(runner.driver.status()["worker_alive"])
            self.assertIsNone(runner._thread)
        finally:
            release.set()
            worker.join(1)
            runner.stop()

    def test_retired_runner_requires_full_stop_even_without_usb_worker(self):
        manager = DeviceManager(enumerate_devices=lambda: [])
        runner = Mock()
        runner.driver.status.return_value = {"worker_alive": False}
        runner.stop.return_value = False
        manager._retired["blocked-open"] = runner
        manager._scan_devices()
        self.assertIn("blocked-open", manager._retired)
        runner.stop.assert_called_once_with(timeout=0)
        runner.stop.return_value = True
        manager._scan_devices()
        self.assertNotIn("blocked-open", manager._retired)

    def test_ipc_cannot_restart_with_previous_live_handlers(self):
        server = IPCServer(None)
        server._clients[object()] = Mock()
        with self.assertRaisesRegex(ProtocolError, "previous IPC workers"):
            server.start()

    def test_reconnect_resets_all_known_configuration(self):
        runner = DeviceRunner(FakeRival)
        runner.start()
        try:
            runner.set_dpi_stages([600, 900, 1200, 1500, 1800], active=2)
            runner.set_polling(500)
            runner.restore_buttons(persist=False)
            runner.set_color("112233")
            runner.reconnect()
            state = runner.get_state()
            self.assertEqual(state["settings"], {})
            self.assertIsNone(state["effect"])
            self.assertEqual(set(state["unknown_fields"]), {"dpi", "polling_rate", "buttons", "colors"})
            self.assertEqual(runner.driver.device.packets, [])
        finally:
            runner.stop()
