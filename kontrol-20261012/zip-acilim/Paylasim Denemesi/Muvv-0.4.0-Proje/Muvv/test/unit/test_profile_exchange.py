import json
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from demo import DemoClient
from ipc_protocol import encode_message
from managers.errors import ValidationError
from managers.profile_store import MAX_PROFILE_BYTES, ProfileStore, validate_profile
from profile_io import read_profile_file, write_profile_file
from ui_client import fetch_snapshot


class ProfileExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.client = DemoClient()
        self.store = self.client.manager.profile_store
        self.profile = self.store.load("Çalışma")

    def tearDown(self):
        self.client.close()
        self.temporary.cleanup()

    def test_file_roundtrip_requires_explicit_overwrite(self):
        target = self.root / "profile.json"
        write_profile_file(target, self.profile)
        self.assertEqual(read_profile_file(target), self.profile)
        with self.assertRaises(ValidationError):
            write_profile_file(target, self.profile)
        changed = {**self.profile, "name": "Yeni"}
        write_profile_file(target, changed, overwrite=True)
        self.assertEqual(read_profile_file(target)["name"], "Yeni")
        self.assertEqual(list(self.root.glob(".muvv-export-*")), [])

    def test_utf8_bom_is_accepted_only_on_import(self):
        target = self.root / "profile.json"
        target.write_bytes(b"\xef\xbb\xbf" + json.dumps(self.profile, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(read_profile_file(target), self.profile)

    def test_unsafe_import_shapes_and_files_are_rejected(self):
        target = self.root / "bad.json"
        for data in (b"[1]", b"\xff", b'{"version":1,"version":1}', b" " * (MAX_PROFILE_BYTES + 1)):
            target.write_bytes(data)
            with self.subTest(data=data[:40]), self.assertRaises(ValidationError):
                read_profile_file(target)
        with self.assertRaises(ValidationError):
            read_profile_file(self.root)
        with self.assertRaises(ValidationError):
            read_profile_file(self.root / "missing.json")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO safety requires POSIX.")
    def test_fifo_is_rejected_before_opening(self):
        target = self.root / "pipe"
        os.mkfifo(target)
        with patch("profile_io.os.open") as open_file, self.assertRaises(ValidationError):
            read_profile_file(target)
        open_file.assert_not_called()

    def test_export_rejects_hardlinks_and_keeps_original_bytes(self):
        target, alias = self.root / "file.json", self.root / "alias.json"
        target.write_bytes(b"original")
        os.link(target, alias)
        with self.assertRaises(ValidationError):
            write_profile_file(target, self.profile, overwrite=True)
        self.assertEqual(alias.read_bytes(), b"original")

    def test_corrupt_profile_isolated_from_devices_and_valid_profiles(self):
        invalid = self.store.directory / ("0" * 64 + ".json")
        invalid.write_bytes(b"{")
        if os.name == "posix":
            invalid.chmod(0o600)
        snapshot = fetch_snapshot(self.client)
        self.assertEqual(snapshot["selected_device"], "demo-rival-3")
        self.assertEqual([profile["name"] for profile in snapshot["profiles"]], ["Çalışma"])
        self.assertEqual(len(snapshot["profile_errors"]), 1)
        self.assertEqual(self.client("set-polling", {"hz": 500})["status"], "ok")

    def test_invalid_profile_directory_does_not_block_device_snapshot(self):
        self.client.manager.profile_store = ProfileStore(self.root / "not-directory")
        (self.root / "not-directory").write_bytes(b"data")
        snapshot = fetch_snapshot(self.client)
        self.assertIsNotNone(snapshot["info"])
        self.assertTrue(snapshot["profile_errors"])

    def test_catalog_pagination_fits_response_limit_with_maximum_unicode_names(self):
        for index in range(127):
            profile = {**self.profile, "name": f"{index:03d}" + "😀" * 61}
            self.store.save(profile)
        snapshot = fetch_snapshot(self.client)
        self.assertEqual(len(snapshot["profiles"]), 128)
        for offset in (0, 32, 64, 96):
            page = self.client("list-profiles", {"offset": offset, "limit": 32})
            self.assertLess(len(encode_message(page)), 65540)
            self.assertEqual(len(page["profiles"]), 32)
        with self.assertRaises(ValidationError):
            self.store.save({**self.profile, "name": "Overflow"})
        renamed = self.store.rename("Çalışma", "Yeni ad")
        self.assertEqual(renamed["name"], "Yeni ad")
        self.assertEqual(len(self.store.list()), 128)

    def test_rename_refuses_collision_and_rolls_back_on_source_removal_failure(self):
        self.store.save({**self.profile, "name": "Other"})
        with self.assertRaises(ValidationError):
            self.store.rename("Çalışma", "Other")
        original_delete = self.store.delete

        def delete(name):
            if name == "Çalışma":
                raise OSError("cannot unlink source")
            return original_delete(name)

        with patch.object(self.store, "delete", side_effect=delete), self.assertRaises(OSError):
            self.store.rename("Çalışma", "Rollback")
        self.assertEqual(self.store.load("Çalışma"), self.profile)
        self.assertNotIn("Rollback", [profile["name"] for profile in self.store.list()])

    def test_catalog_limits_reject_booleans_and_count_invalid_files(self):
        for offset, limit in ((True, 32), (-1, 32), (0, False), (0, 33)):
            result = self.client("list-profiles", {"offset": offset, "limit": limit})
            self.assertEqual(result["status"], "error")
        for index in range(127):
            target = self.store.directory / f"invalid-{index}.json"
            target.write_bytes(b"{")
            if os.name == "posix":
                target.chmod(0o600)
        with self.assertRaises(ValidationError):
            self.store.save({**self.profile, "name": "Extra"})

    def test_unknown_settings_must_match_profile_contents(self):
        for unknown in ([], ["colors"], ["dpi", "buttons"]):
            profile = deepcopy(self.profile)
            profile["settings"] = {"colors": self.profile["settings"]["colors"]}
            profile["effect"] = None
            profile["unknown_fields"] = unknown
            with self.subTest(unknown=unknown), self.assertRaises(ValidationError):
                validate_profile(profile)

    def test_import_and_rename_commands_do_not_write_usb(self):
        self.client.runner.stop_effect()
        before = self.client.runner.driver.status()["reports_written"]
        result = self.client("import-profile", {"profile": {**self.profile, "name": "Imported"}})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            self.client("rename-profile", {"name": "Imported", "new_name": "Renamed"})["status"], "ok"
        )
        self.assertEqual(self.client.runner.driver.status()["reports_written"], before)
