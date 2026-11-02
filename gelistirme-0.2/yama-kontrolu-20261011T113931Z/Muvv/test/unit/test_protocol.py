import socket
import struct
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from support import FakeRival

from ipc_protocol import decode_json, encode_message, receive_message, send_message
from managers.device_manager import DeviceManager
from managers.device_runner import DeviceRunner
from managers.errors import ProtocolError
from managers.ipc_server import IPCServer


class FramingTests(unittest.TestCase):
    def setUp(self):
        self.left, self.right = socket.socketpair()

    def tearDown(self):
        self.left.close()
        self.right.close()

    def test_fragmented_header_and_body_are_reassembled(self):
        expected = {"command": "set-color", "args": {"color": "123456"}}
        frame = encode_message(expected)
        worker = threading.Thread(target=lambda: [self.left.sendall(bytes([byte])) for byte in frame])
        worker.start()
        try:
            self.assertEqual(receive_message(self.right), expected)
        finally:
            worker.join(1)

    def test_large_response_and_unicode_surrogate_path(self):
        expected = {"status": "ok", "value": "İş" * 3000, "path": "hid\udcff"}
        worker = threading.Thread(target=lambda: send_message(self.left, expected))
        worker.start()
        try:
            self.assertEqual(receive_message(self.right, limit=65536), expected)
        finally:
            worker.join(1)

    def test_oversized_header_is_rejected_without_reading_body(self):
        self.left.sendall(struct.pack("!I", 16385))
        with self.assertRaises(ProtocolError):
            receive_message(self.right)

    def test_truncated_body_and_idle_client_do_not_hang(self):
        self.left.sendall(struct.pack("!I", 100) + b"{}")
        self.left.shutdown(socket.SHUT_WR)
        with self.assertRaises(ProtocolError):
            receive_message(self.right, timeout=0.1)
        left, right = socket.socketpair()
        try:
            with self.assertRaises(ProtocolError):
                receive_message(right, timeout=0.03)
        finally:
            left.close()
            right.close()

    def test_invalid_json_forms_are_rejected(self):
        for data in (
            b"[]",
            b"null",
            b"\xff",
            b'{"a":1,"a":2}',
            b'{"a":NaN}',
            b'{"a":Infinity}',
            b'{"a":' + b"[" * 20 + b"0" + b"]" * 20 + b"}",
        ):
            with self.subTest(data=data), self.assertRaises(ProtocolError):
                decode_json(data)

    def test_nonfinite_output_and_zero_size_frames_are_rejected(self):
        with self.assertRaises(ProtocolError):
            encode_message({"speed": float("nan")})
        self.left.sendall(bytes(4))
        with self.assertRaises(ProtocolError):
            receive_message(self.right)


class ShutdownTests(unittest.TestCase):
    def test_socket_cleanup_failure_still_releases_daemon_lock(self):
        server = IPCServer(None, socket_path=Path("private-socket"))
        server._socket_identity = (1, 2)
        server._lock_fd = 999
        server.is_running = True
        with (
            patch.object(Path, "lstat", side_effect=PermissionError("directory unavailable")),
            patch("managers.ipc_server.os.close") as close,
            self.assertLogs("managers.ipc_server", level="WARNING"),
        ):
            server.stop()
        close.assert_called_once_with(999)
        self.assertIsNone(server._lock_fd)
        self.assertIsNone(server._socket_identity)
        self.assertFalse(server.is_running)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.manager = DeviceManager()
        self.runner = DeviceRunner(FakeRival, device_path=b"fake")
        self.runner.start()
        self.manager.runners["fake"] = self.runner
        self.ipc = IPCServer(self.manager)

    def tearDown(self):
        self.runner.stop()

    def call(self, command, **args):
        return self.ipc._process_command({"command": command, "args": {"device": "fake", **args}})

    def test_invalid_shapes_receive_structured_errors(self):
        for payload in (
            [],
            None,
            {"command": []},
            {"command": "list", "args": []},
            {"command": "list", "version": True},
            {"command": "list", "unknown": 1},
        ):
            with self.subTest(payload=payload):
                response = self.ipc._process_command(payload)
                self.assertEqual(response["status"], "error")
                self.assertEqual(response["code"], "invalid_request")

    def test_unknown_keys_and_boolean_integers_are_rejected(self):
        for command, args in (
            ("set-dpi", {"level": True}),
            ("set-dpi", {"level": 1.5}),
            ("set-polling", {"hz": "500"}),
            ("set-dpi", {"level": 1, "initialize": "yes"}),
            ("set-effect", {"effect": "wave", "apply": "bad"}),
            ("set-color", {"hex": "FFFFF"}),
            ("set-color", {"hex": "123456", "color": "000000"}),
        ):
            with self.subTest(command=command, args=args):
                self.assertEqual(self.call(command, **args)["status"], "error")
        self.assertEqual(self.runner.driver.device.packets, [])

    def test_legacy_hex_field_and_static_effect_work(self):
        self.assertEqual(self.call("set-color", hex="ff0080")["status"], "ok")
        self.assertEqual(self.call("set-effect", effect="static")["status"], "ok")

    def test_usb_failure_is_returned_to_client(self):
        self.runner.driver.device.result = 0
        result = self.call("set-polling", hz=500)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], "transport_error")

    def test_valid_slot_configuration_and_unknown_state_error(self):
        result = self.call("set-dpi", level=2)
        self.assertEqual(result["code"], "unknown_device_state")
        result = self.call("set-dpi-stages", stages=[400, 800, 1200, 2400, 3200], active=2)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["reports"], 1)
        self.assertEqual(self.call("set-dpi", level=1)["status"], "ok")
