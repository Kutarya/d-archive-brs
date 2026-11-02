import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from support import FakeHID, FakeRival, connected_mouse

import cli
from demo import DemoClient
from managers.device_manager import DeviceManager
from managers.device_runner import DeviceRunner
from managers.errors import ProtocolError, TransportError, ValidationError
from ui_client import fetch_snapshot


class RobustnessTests(unittest.TestCase):
    def test_hotplug_during_snapshot_keeps_selection_in_captured_list(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DeviceManager(
                enumerate_devices=lambda: [], profile_directory=Path(directory) / "profiles"
            )
            old, new = DeviceRunner(FakeRival), DeviceRunner(FakeRival)
            old.start()
            new.start()
            manager.runners["old"] = old
            listed, replaced = threading.Event(), threading.Event()
            original = manager.get_active_devices

            def replace():
                listed.wait(2)
                with manager._lock:
                    manager.runners = {"new": new}
                replaced.set()

            def get_devices():
                devices = original()
                listed.set()
                replaced.wait(0.2)
                return devices

            worker = threading.Thread(target=replace)
            worker.start()
            try:
                with patch.object(manager, "get_active_devices", side_effect=get_devices):
                    result = fetch_snapshot(
                        lambda command, _: (
                            {"status": "ok", **manager.snapshot()} if command == "snapshot" else {}
                        )
                    )
                self.assertIn(result["selected_device"], {device["id"] for device in result["devices"]})
                self.assertEqual(result["daemon"]["devices"], len(result["devices"]))
            finally:
                listed.set()
                worker.join(2)
                old.stop()
                new.stop()
                manager.stop()
            self.assertFalse(worker.is_alive())

    def test_reconnect_between_list_and_state_never_combines_sessions(self):
        client = DemoClient()
        try:
            original = client.runner.get_capabilities

            def reconnect():
                client.runner.reconnect()
                return original()

            with patch.object(client.runner, "get_capabilities", side_effect=reconnect):
                result = client("snapshot")
            self.assertIsNone(result["info"])
            self.assertEqual(result["device_error"]["code"], "device_changed")
        finally:
            client.close()

    def test_client_rejects_mismatched_device_sessions(self):
        client = DemoClient()
        try:
            result = deepcopy(client("snapshot"))
            result["devices"][0]["session_id"] = "0" * 32
            with self.assertRaises(ProtocolError):
                fetch_snapshot(lambda *_: result)
        finally:
            client.close()

    def test_catalog_changes_when_existing_profile_is_overwritten(self):
        client = DemoClient()
        try:
            store = client.manager.profile_store
            before = store.catalog()["catalog_id"]
            profile = deepcopy(store.load("Çalışma"))
            profile["settings"]["polling_rate"] = 500
            store.save(profile, overwrite=True)
            self.assertNotEqual(store.catalog()["catalog_id"], before)
        finally:
            client.close()

    def test_external_profile_edit_during_catalog_read_is_rejected(self):
        client = DemoClient()
        try:
            store = client.manager.profile_store
            profile = deepcopy(store.load("Çalışma"))
            profile["settings"]["polling_rate"] = 500
            filename, _ = store._path(profile["name"])
            original = store._read

            def replace_during_read(path):
                result = original(path)
                filename.write_text(json.dumps(profile), encoding="utf-8")
                return result

            with patch.object(store, "_read", side_effect=replace_during_read):
                with self.assertRaisesRegex(ValidationError, "changed"):
                    store.catalog()
            self.assertEqual(store.load("Çalışma")["settings"]["polling_rate"], 500)
        finally:
            client.close()

    def test_malformed_daemon_diagnostics_are_rejected_before_display(self):
        client = DemoClient()
        try:
            snapshot = client("snapshot")
            for daemon in ([], {"scan_error": []}, {"connection_errors": []}, {"closing_devices": [False]}):
                with self.subTest(daemon=daemon):
                    result = deepcopy(snapshot)
                    result["daemon"] = daemon
                    with self.assertRaises(ProtocolError):
                        fetch_snapshot(lambda *_, result=result: result)
        finally:
            client.close()

    def test_exact_device_ids_take_priority_over_aliases_and_whitespace(self):
        manager = DeviceManager(enumerate_devices=lambda: [])
        manager.runners = {"aaa": None, "default": None, " first ": None}
        self.assertEqual(manager.resolve_device_id("default"), "default")
        self.assertEqual(manager.resolve_device_id(" first "), " first ")
        self.assertEqual(manager.resolve_device_id(None), " first ")
        manager.runners.clear()

    def test_disconnect_aborts_remaining_reports_in_running_transaction(self):
        mouse = connected_mouse(FakeHID(block=True))
        handle = mouse.device
        packets = tuple((bytes([index]) + bytes(63), 0) for index in range(3))
        try:
            future = mouse.submit(packets)
            self.assertTrue(handle.entered.wait(1))
            pending = mouse.submit(((bytes([9]) + bytes(63), 0),))
            self.assertFalse(mouse.disconnect(timeout=0.01))
            handle.release.set()
            with self.assertRaises(TransportError):
                future.result(1)
            with self.assertRaises(TransportError):
                pending.result(1)
            self.assertTrue(mouse.disconnect())
            self.assertEqual(handle.packets, [packets[0][0]])
            self.assertTrue(handle.closed)
            self.assertTrue(mouse.status()["state_uncertain"])
        finally:
            handle.release.set()
            mouse.disconnect()

    def test_disconnect_interrupts_inter_report_delay(self):
        mouse = connected_mouse()
        handle = mouse.device
        try:
            future = mouse.submit(((bytes(64), 1), (bytes([1]) + bytes(63), 0)))
            self.assertTrue(handle.entered.wait(1))
            started = time.monotonic()
            self.assertTrue(mouse.disconnect(timeout=0.2))
            self.assertLess(time.monotonic() - started, 0.3)
            with self.assertRaises(TransportError):
                future.result(1)
            self.assertEqual(len(handle.packets), 1)
        finally:
            mouse.disconnect()

    def cli_profiles(self, pages):
        with patch("cli.send_command", side_effect=pages), redirect_stdout(io.StringIO()) as output:
            result = cli.main(["--json", "list-profiles", "--all", "--limit", "1"])
        return result, json.loads(output.getvalue())

    @staticmethod
    def profile_page(name, offset=None, catalog="a" * 64):
        return {
            "status": "ok",
            "profiles": [
                {"name": name, "device": {"vendor_id": 0x1038, "product_id": 0x1870}, "unknown_fields": []}
            ],
            "profile_errors": [],
            "profile_count": 2,
            "next_offset": offset,
            "catalog_id": catalog,
        }

    def test_cli_rejects_catalog_changes_between_pages(self):
        code, result = self.cli_profiles(
            [self.profile_page("A", 1), self.profile_page("B", catalog="b" * 64)]
        )
        self.assertEqual(code, 1)
        self.assertEqual(result["code"], "invalid_request")

    def test_cli_rejects_invalid_later_page_without_a_traceback(self):
        page = self.profile_page("B")
        page["profiles"] = "invalid"
        code, result = self.cli_profiles([self.profile_page("A", 1), page])
        self.assertEqual(code, 1)
        self.assertEqual(result["code"], "invalid_request")

    def test_cli_rejects_duplicate_profile_names_across_pages(self):
        code, result = self.cli_profiles([self.profile_page("A", 1), self.profile_page("A")])
        self.assertEqual(code, 1)
        self.assertEqual(result["code"], "invalid_request")

    def test_simulation_checks_and_cleanup_run_with_python_optimization(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "result.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-O",
                    str(root / "tools/simulation_check.py"),
                    "--cycles",
                    "2",
                    "--json",
                    str(filename),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(filename.read_text(encoding="utf-8"))
            self.assertTrue(report["successful"])
            self.assertEqual(report["remaining_workers"], [])
            self.assertEqual(report["scenarios"]["reconnect_and_profiles"]["unique_sessions"], 2)
