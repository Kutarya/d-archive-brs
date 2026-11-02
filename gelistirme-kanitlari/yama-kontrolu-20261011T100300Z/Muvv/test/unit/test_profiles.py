import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from support import FakeRival

from managers.device_runner import DeviceRunner
from managers.errors import ValidationError
from managers.profile_store import ProfileStore


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = ProfileStore(Path(self.temporary.name) / "profiles")
        self.runner = DeviceRunner(FakeRival, b"fake")
        self.runner.start()
        self.runner.set_color("123456")
        self.profile = self.runner.host_profile("İş")

    def tearDown(self):
        self.runner.stop()
        self.temporary.cleanup()

    def test_unicode_profile_roundtrip_overwrite_and_delete(self):
        self.store.save(self.profile)
        self.assertEqual(self.store.load("İş")["settings"]["colors"]["wheel"], [18, 52, 86])
        with self.assertRaises(ValidationError):
            self.store.save(self.profile)
        self.store.save(self.profile, overwrite=True)
        self.assertEqual([value["name"] for value in self.store.list()], ["İş"])
        self.store.delete("İş")
        self.assertEqual(self.store.list(), [])

    def test_invalid_name_cannot_escape_profile_directory(self):
        for name in ("", "../work", "x/y", "x\\y", " work ", "a\n", "x" * 65):
            profile = {**self.profile, "name": name}
            with self.subTest(name=name), self.assertRaises(ValidationError):
                self.store.save(profile)
        self.assertFalse((Path(self.temporary.name) / "work").exists())

    def test_saved_profile_files_have_private_posix_permissions(self):
        self.store.save(self.profile)
        if os.name != "posix":
            self.skipTest("POSIX permissions are verified on Linux.")
        self.assertEqual(self.store.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(next(self.store.directory.glob("*.json")).stat().st_mode & 0o777, 0o600)

    def test_profile_cannot_claim_readback_or_hide_bad_settings(self):
        for change in (
            {"readback_verified": True},
            {"version": True},
            {"settings": {"polling_rate": 750}},
            {"settings": {"dpi": {"stages": [800], "active": 0}}},
            {"effect": {"name": "wave", "options": {"wave_length": 0}}},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.store.save({**self.profile, **change})

    def test_loading_corrupt_or_oversized_profile_fails(self):
        self.store.save(self.profile)
        path = next(self.store.directory.glob("*.json"))
        path.write_bytes(b"{")
        with self.assertRaises(ValueError):
            self.store.load("İş")
        path.write_bytes(b" " * 32769)
        with self.assertRaises(ValidationError):
            self.store.load("İş")

    def test_different_model_and_invalid_component_write_nothing(self):
        handle = self.runner.driver.device
        before = len(handle.packets)
        wrong_model = deepcopy(self.profile)
        wrong_model["device"]["product_id"] = 1
        with self.assertRaises(ValidationError):
            self.runner.apply_profile(wrong_model)
        bad = deepcopy(self.profile)
        bad["settings"]["buttons"] = {"button1": 1}
        with self.assertRaises(ValidationError):
            self.runner.apply_profile(bad)
        self.assertEqual(len(handle.packets), before)

    def test_host_profile_application_keeps_unknown_dpi_untouched(self):
        handle = self.runner.driver.device
        self.store.save(self.profile)
        self.runner.set_color("000000")
        handle.packets.clear()
        self.runner.apply_profile(self.store.load("İş"), persist=True)
        self.assertEqual([packet[0] for packet in handle.packets], [0x21, 0x11])
        self.assertIn("dpi", self.runner.get_state()["unknown_fields"])

    def test_unsupported_or_inconsistent_profiles_fail(self):
        for change in (
            {"unknown_fields": ["colors"]},
            {"unknown_fields": ["buttons", "buttons"]},
            {"device": {"vendor_id": 1, "product_id": 2}},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.store.save({**self.profile, **change})
