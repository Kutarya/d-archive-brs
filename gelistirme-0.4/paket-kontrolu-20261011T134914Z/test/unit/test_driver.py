import threading
import time
import unittest

from support import FakeHID, connected_mouse

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.errors import OperationTimeout, TransportError, UnknownDeviceState, ValidationError


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.mouse = connected_mouse()
        self.handle = self.mouse.device

    def tearDown(self):
        self.handle.release.set()
        self.mouse.disconnect()

    def test_all_reports_keep_the_original_64_byte_protocol(self):
        self.mouse.set_dpi_stages([400, 800, 1200, 2400, 3200], active=2)
        self.mouse.set_polling_rate(500)
        self.mouse.set_colors({zone: (255, 0, 128) for zone in self.mouse.ZONE_MAP})
        self.mouse.restore_buttons()
        self.mouse.save_profile()
        self.assertEqual(
            [packet[0] for packet in self.handle.packets], [0x34, 0x2B, 0x21, 0x2A, 0x11, 0x21, 0x11]
        )
        self.assertTrue(all(len(packet) == 64 for packet in self.handle.packets))
        self.assertEqual(
            self.handle.packets[0][:13],
            bytes([0x34, 5, 2, 8, 8, 0x12, 0x12, 0x1B, 0x1B, 0x37, 0x37, 0x49, 0x49]),
        )
        self.assertEqual(self.handle.packets[2][1:11], bytes([7, 255, 0, 128, 255, 0, 128, 255, 0, 128]))
        self.assertEqual(self.handle.packets[4], bytes([0x11]) + bytes(63))

    def test_unknown_dpi_slots_are_not_silently_overwritten(self):
        with self.assertRaises(UnknownDeviceState):
            self.mouse.set_dpi(2)
        self.assertEqual(self.handle.packets, [])
        self.mouse.set_dpi(2, initialize=True)
        self.assertEqual(self.mouse.get_profile()["settings"]["dpi"]["active"], 2)

    def test_unknown_button_mapping_requires_explicit_initialization(self):
        with self.assertRaises(UnknownDeviceState):
            self.mouse.bind_key("button4", 4)
        self.assertEqual(self.handle.packets, [])

    def test_rejected_left_click_remap_keeps_state_and_allows_next_command(self):
        self.mouse.restore_buttons(persist=False)
        before = self.mouse.button_config.copy()
        count = len(self.handle.packets)
        with self.assertRaises(ValidationError):
            self.mouse.bind_key("button1", 4)
        self.assertEqual(self.mouse.button_config, before)
        self.assertEqual(len(self.handle.packets), count)
        self.mouse.bind_key("button4", 4)
        self.assertEqual(self.mouse.button_config["button4"], (0x51, 4))

    def test_invalid_button_or_usage_never_poison_state(self):
        self.mouse.restore_buttons(persist=False)
        before = self.mouse.button_config.copy()
        for button, usage in (("missing", 4), ("button4", 999), ("button4", True), ("button4", 0xFF)):
            with self.subTest(button=button, usage=usage), self.assertRaises(ValidationError):
                self.mouse.bind_key(button, usage)
            self.assertEqual(self.mouse.button_config, before)
        self.mouse.bind_key("button5", 0xE1, persist=False)

    def test_input_dpi_list_and_capabilities_are_copied(self):
        stages = [400, 800, 1200, 2400, 3200]
        self.mouse.set_dpi_stages(stages)
        stages[0] = 999
        self.assertEqual(self.mouse.dpi_levels[0], 400)
        capabilities = self.mouse.get_capabilities()
        capabilities["rgb"]["zones"].clear()
        self.assertEqual(len(self.mouse.get_capabilities()["rgb"]["zones"]), 3)

    def test_invalid_full_profile_is_rejected_before_any_write(self):
        with self.assertRaises(ValidationError):
            self.mouse.apply_settings({"polling_rate": 500, "buttons": {"button1": 1}})
        self.assertEqual(self.handle.packets, [])
        self.assertNotIn("polling_rate", self.mouse.get_profile()["settings"])

    def test_zero_and_short_writes_are_errors(self):
        for result in (0, 63, True):
            with self.subTest(result=result):
                mouse = connected_mouse(FakeHID(result=result))
                handle = mouse.device
                try:
                    with self.assertRaises(TransportError):
                        mouse.set_polling_rate(500)
                    self.assertNotIn("polling_rate", mouse.get_profile()["settings"])
                    self.assertTrue(mouse.status()["state_uncertain"])
                finally:
                    mouse.disconnect()
                    self.assertTrue(handle.closed)

    def test_partial_batch_failure_does_not_commit_ram_state(self):
        mouse = connected_mouse(FakeHID(fail_on=1))
        try:
            with self.assertRaises(TransportError):
                mouse.restore_buttons(persist=True)
            self.assertNotIn("buttons", mouse.get_profile()["settings"])
            self.assertTrue(mouse.status()["state_uncertain"])
        finally:
            mouse.disconnect()

    def test_button_config_and_save_cannot_be_interleaved(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        failures = []
        worker = threading.Thread(target=lambda: self._capture(failures, mouse.restore_buttons))
        try:
            worker.start()
            self.assertTrue(handle.entered.wait(1))
            mouse.submit_frame(bytes([0x21]) + bytes(63))
            handle.release.set()
            worker.join(2)
            self.assertEqual(failures, [])
            mouse.transact(((bytes([0x2B]) + bytes(63), 0),))
            self.assertEqual([packet[0] for packet in handle.packets][:2], [0x2A, 0x11])
        finally:
            handle.release.set()
            worker.join(2)
            mouse.disconnect()

    @staticmethod
    def _capture(failures, operation):
        try:
            operation()
        except Exception as error:
            failures.append(error)

    def test_animation_backpressure_retains_only_the_latest_frame(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        try:
            future = mouse.submit(((bytes([0x2B]) + bytes(63), 0),))
            self.assertTrue(handle.entered.wait(1))
            for value in range(100):
                mouse.submit_frame(bytes([0x21, value]) + bytes(62))
            self.assertEqual(mouse.command_queue.qsize(), 0)
            self.assertTrue(mouse.status()["pending_frame"])
            self.assertEqual(mouse.status()["frames_replaced"], 99)
            handle.release.set()
            future.result(1)
            deadline = time.monotonic() + 1
            while len(handle.packets) < 2 and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertEqual(handle.packets[-1][1], 99)
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_blocked_backend_has_bounded_shutdown_and_no_second_worker(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        mouse.WRITE_TIMEOUT = 0.03
        try:
            with self.assertRaises(OperationTimeout):
                mouse.set_polling_rate(500)
            started = time.monotonic()
            self.assertFalse(mouse.disconnect(timeout=0.03))
            self.assertLess(time.monotonic() - started, 0.3)
            with self.assertRaises(TransportError):
                mouse.reconnect()
        finally:
            handle.release.set()
            self.assertTrue(mouse.disconnect(timeout=1))
            self.assertTrue(handle.closed)

    def test_queue_is_bounded_and_rejects_excess_commands(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        try:
            mouse.submit(((bytes(64), 0),))
            self.assertTrue(handle.entered.wait(1))
            for _ in range(mouse.QUEUE_LIMIT):
                mouse.submit(((bytes(64), 0),))
            with self.assertRaises(TransportError):
                mouse.submit(((bytes(64), 0),))
            self.assertEqual(mouse.command_queue.qsize(), mouse.QUEUE_LIMIT)
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_constructing_driver_does_not_start_a_thread(self):
        mouse = Rival3Gen2Mouse()
        self.assertIsNone(mouse._worker_thread)
