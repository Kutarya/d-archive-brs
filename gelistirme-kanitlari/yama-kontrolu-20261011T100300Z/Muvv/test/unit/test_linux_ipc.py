import os
import socket
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from cli import send_command
from ipc_protocol import encode_message, receive_message, verify_peer
from managers.device_manager import DeviceManager
from managers.errors import ProtocolError
from managers.ipc_server import IPCServer


@unittest.skipUnless(sys.platform == "linux", "Real Unix socket and POSIX permission tests require Linux.")
class LinuxIPCTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="muvv-")
        self.root = Path(self.temporary.name)
        self.path = self.root / "muvv.sock"
        self.manager = DeviceManager(enumerate_devices=lambda: [])
        self.server = IPCServer(self.manager, socket_path=self.path, client_timeout=0.2)
        self.connections = []

    def tearDown(self):
        for connection in self.connections:
            connection.close()
        self.server.stop()
        self.temporary.cleanup()

    def connect(self):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(1)
        connection.connect(str(self.path))
        self.connections.append(connection)
        return connection

    def test_socket_permissions_and_actual_client_roundtrip(self):
        self.server.start()
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(send_command("list", socket_file=self.path)["status"], "ok")

    def test_second_daemon_cannot_remove_live_socket(self):
        self.server.start()
        identity = self.path.stat().st_ino
        second = IPCServer(self.manager, socket_path=self.path)
        with self.assertRaises(ProtocolError):
            second.start()
        self.assertEqual(self.path.stat().st_ino, identity)
        self.assertEqual(send_command("list", socket_file=self.path)["status"], "ok")

    def test_start_refuses_regular_file_symlink_and_public_directory(self):
        self.path.write_bytes(b"keep")
        with self.assertRaises(ProtocolError):
            self.server.start()
        self.assertEqual(self.path.read_bytes(), b"keep")
        self.path.unlink()
        self.path.symlink_to(self.root / "target")
        with self.assertRaises(ProtocolError):
            self.server.start()
        self.assertTrue(self.path.is_symlink())
        self.path.unlink()
        self.root.chmod(0o755)
        try:
            with self.assertRaises(ProtocolError):
                self.server.start()
        finally:
            self.root.chmod(0o700)

    def test_stale_owned_socket_can_be_replaced(self):
        old = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        old.bind(str(self.path))
        old.close()
        self.server.start()
        self.assertEqual(send_command("list", socket_file=self.path)["status"], "ok")

    def test_idle_clients_are_bounded_and_closed_at_shutdown(self):
        self.server.client_timeout = 2
        self.server.start()
        for _ in range(self.server.MAX_CLIENTS):
            self.connect()
        deadline = time.monotonic() + 1
        while len(self.server._clients) < self.server.MAX_CLIENTS and time.monotonic() < deadline:
            time.sleep(0.005)
        excess = self.connect()
        self.assertEqual(receive_message(excess, timeout=1)["code"], "busy")
        self.assertEqual(len(self.server._clients), self.server.MAX_CLIENTS)
        self.server.stop()
        self.assertEqual(self.server._clients, {})
        self.assertFalse(self.path.exists())

    def test_malformed_frame_gets_error_and_daemon_remains_available(self):
        self.server.start()
        connection = self.connect()
        connection.sendall(b"\x00\x00\x00\x02[]")
        response = receive_message(connection)
        self.assertEqual(response["status"], "error")
        self.assertEqual(send_command("list", socket_file=self.path)["status"], "ok")

    def test_stop_does_not_unlink_a_replaced_path(self):
        self.server.start()
        self.path.unlink()
        self.path.write_bytes(b"replacement")
        self.server.stop()
        self.assertEqual(self.path.read_bytes(), b"replacement")

    def test_socket_peer_must_belong_to_current_uid(self):
        self.server.start()
        connection = self.connect()
        with patch("ipc_protocol.peer_uid", return_value=os.getuid() + 1):
            with self.assertRaises(ProtocolError):
                verify_peer(connection)

    def test_slow_partial_request_times_out_with_error(self):
        self.server.start()
        connection = self.connect()
        frame = encode_message({"command": "list"})
        connection.sendall(frame[:5])
        response = receive_message(connection, timeout=1)
        self.assertEqual(response["status"], "error")
        self.assertIn("timed out", response["message"])

    def test_profile_symlinks_and_hardlinks_are_rejected(self):
        from managers.errors import ValidationError
        from managers.profile_store import ProfileStore

        store = ProfileStore(self.root / "profiles")
        path, _ = store._path("Work")
        target = self.root / "target"
        target.write_text("{}")
        path.symlink_to(target)
        with self.assertRaises(ValidationError):
            store.load("Work")
        path.unlink()
        os.link(target, path)
        with self.assertRaises(ValidationError):
            store.load("Work")
