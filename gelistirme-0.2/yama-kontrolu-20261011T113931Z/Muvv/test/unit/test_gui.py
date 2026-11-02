import faulthandler
import gc
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from demo import DemoClient
from gui import MuvvApp, ctk

HAS_DISPLAY = sys.platform == "win32" or bool(os.environ.get("DISPLAY"))


@unittest.skipUnless(ctk is not None and HAS_DISPLAY, "GUI tests need the gui extra and a display.")
class GUITests(unittest.TestCase):
    def setUp(self):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.withdraw()
        self.callback_errors = []
        self.root.report_callback_exception = lambda *args: self.callback_errors.append(args)
        self.client = DemoClient()
        self.app = MuvvApp(self.root, client=self.client, demo=True)
        self.pump(lambda: self.app._device_id is not None and not self.app._busy)

    def tearDown(self):
        if not self.app._closed:
            self.pump(lambda: not self.app._busy)
            self.app.close()
        self.client.close()
        self.assertEqual(self.callback_errors, [])
        self.app = None
        self.root = None
        gc.collect()

    def pump(self, predicate, timeout=6):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(0.005)
        faulthandler.dump_traceback()
        self.fail(
            f"GUI deadline exceeded: busy={self.app._busy}, status={self.app.status_label.cget('text')}, callbacks={self.callback_errors}"
        )

    def done(self):
        self.pump(lambda: not self.app._busy)

    def test_refresh_populates_device_dpi_and_profiles(self):
        self.assertEqual(self.app._device_id, "demo-rival-3")
        self.assertEqual(self.app.dpi_entries[1].get(), "800")
        self.assertEqual(self.app.polling_menu.get(), "1000")
        self.assertIn("Çalışma", self.app.profile_menu.cget("values"))

    def test_effect_and_live_color_update_flow(self):
        self.app.effect_menu.set("Nefes")
        self.app.color_entry.delete(0, "end")
        self.app.color_entry.insert(0, "#FF0080")
        self.app._apply_effect()
        self.done()
        self.assertEqual(self.client.runner.get_state()["effect"]["name"], "breathing")
        self.app.speed.set(2)
        self.app._update_effect()
        self.done()
        self.assertEqual(self.client.runner.get_state()["effect"]["options"]["speed"], 2)

    def test_invalid_color_does_not_change_device(self):
        previous = self.client.runner.get_state()["effect"]
        self.app.color_entry.delete(0, "end")
        self.app.color_entry.insert(0, "FFFFF")
        self.app._apply_effect()
        self.assertFalse(self.app._busy)
        self.assertEqual(self.client.runner.get_state()["effect"], previous)

    def test_dpi_and_polling_forms_apply_typed_values(self):
        self.app.dpi_entries[0].delete(0, "end")
        self.app.dpi_entries[0].insert(0, "600")
        self.app._apply_dpi()
        self.done()
        self.assertEqual(self.client.runner.driver.dpi_levels[0], 600)
        self.app.polling_menu.set("500")
        self.app._apply_polling()
        self.done()
        self.assertEqual(self.client.runner.driver.polling_rate, 500)

    def test_key_assignment_and_left_click_protection(self):
        self.app.button_menu.set("Yan / geri")
        self.app.usage_entry.delete(0, "end")
        self.app.usage_entry.insert(0, "0xE1")
        self.app._bind()
        self.done()
        self.assertEqual(self.client.runner.driver.button_config["button4"], (0x51, 0xE1))
        self.app.button_menu.set("Sol tık")
        self.app._bind()
        self.done()
        self.assertEqual(self.client.runner.driver.button_config["button1"], 1)

    def test_profile_save_preview_apply_and_confirmed_delete(self):
        self.app.profile_name.insert(0, "Oyun")
        self.app._save_profile()
        self.done()
        self.app.profile_menu.set("Oyun")
        self.app._show_profile("Oyun")
        self.done()
        self.assertIn("DPI:", self.app.profile_detail.get("1.0", "end"))
        self.app._apply_profile()
        self.done()
        with patch("gui.messagebox.askyesno", return_value=True):
            self.app._delete_profile()
        self.pump(lambda: not self.app._busy and "Oyun" not in self.app.profile_menu.cget("values"))
        self.assertEqual(len(self.client.manager.profile_store.list()), 1)

    def test_missing_service_error_is_visible_without_callback_exception(self):
        self.app.client = lambda *_: {"status": "error", "message": "service unavailable"}
        self.app.refresh()
        self.done()
        self.assertIn("service unavailable", self.app.status_label.cget("text"))

    def test_duplicate_clicks_do_not_enqueue_unbounded_jobs(self):
        self.app._apply_dpi()
        for _ in range(20):
            self.app._apply_dpi()
        self.done()
        self.assertFalse(self.app._busy)

    def test_demo_is_separate_from_real_hid_module(self):
        with patch.dict("sys.modules", {"hid": None}):
            self.app._apply_dpi()
            self.done()
            self.assertEqual(self.client.runner.driver.dpi_levels[0], 400)

    def test_background_refresh_preserves_all_unapplied_inputs(self):
        self.app._replace_entry(self.app.dpi_entries[0], "600")
        self.app._mark_dirty("dpi")
        self.app._replace_entry(self.app.color_entry, "#010203")
        self.app._mark_dirty("lighting")
        self.app._replace_entry(self.app.zone_entries["wheel"], "#ABCDEF")
        self.app._mark_dirty("zones")
        self.app.polling_menu.set("250")
        self.app._mark_dirty("polling")
        self.app.refresh(background=True)
        self.done()
        self.assertEqual(self.app.dpi_entries[0].get(), "600")
        self.assertEqual(self.app.color_entry.get(), "#010203")
        self.assertEqual(self.app.zone_entries["wheel"].get(), "#ABCDEF")
        self.assertEqual(self.app.polling_menu.get(), "250")
        self.assertEqual(self.client.runner.driver.dpi_levels[0], 400)

    def test_polling_apply_does_not_discard_dpi_draft(self):
        self.app._replace_entry(self.app.dpi_entries[0], "600")
        self.app._mark_dirty("dpi")
        self.app.polling_menu.set("500")
        self.app._apply_polling()
        self.done()
        self.assertEqual(self.app.dpi_entries[0].get(), "600")
        self.assertIn("dpi", self.app._dirty)
        self.assertEqual(self.client.runner.driver.dpi_levels[0], 400)

    def test_edits_while_a_command_runs_are_not_overwritten(self):
        entered, release = threading.Event(), threading.Event()

        def client(command, args):
            if command == "set-dpi-stages":
                entered.set()
                release.wait(2)
            return self.client(command, args)

        self.app.client = client
        self.app._apply_dpi()
        self.assertTrue(entered.wait(1))
        self.app._replace_entry(self.app.dpi_entries[0], "600")
        self.app._mark_dirty("dpi")
        release.set()
        self.done()
        self.assertEqual(self.app.dpi_entries[0].get(), "600")
        self.assertEqual(self.client.runner.driver.dpi_levels[0], 400)
        self.assertIn("dpi", self.app._dirty)

    def test_completed_command_survives_refresh_error_in_ui(self):
        def client(command, args):
            if command == "snapshot":
                return {"status": "error", "message": "refresh unavailable"}
            return self.client(command, args)

        self.app.client = client
        self.app.polling_menu.set("500")
        self.app._apply_polling()
        self.done()
        self.assertEqual(self.client.runner.driver.polling_rate, 500)
        self.assertIn("Ayar uygulandı", self.app.status_label.cget("text"))
        self.assertIn("yenilenemedi", self.app.status_label.cget("text"))
        self.assertFalse(self.app._service_online)

    def test_explicit_command_is_queued_once_behind_background_refresh(self):
        entered, release = threading.Event(), threading.Event()

        def client(command, args):
            if command == "snapshot" and not release.is_set():
                entered.set()
                release.wait(2)
            return self.client(command, args)

        self.app.client = client
        self.app.refresh(background=True)
        self.assertTrue(entered.wait(1))
        self.app.polling_menu.set("500")
        self.app._apply_polling()
        self.app._apply_polling()
        self.assertIsNotNone(self.app._pending_job)
        release.set()
        self.done()
        self.assertEqual(self.client.runner.driver.polling_rate, 500)
        self.assertIsNone(self.app._pending_job)

    def test_disconnected_device_disables_writes_but_profiles_can_be_managed(self):
        self.client.runner.stop()
        self.client.manager.runners.clear()
        self.app.refresh()
        self.done()
        self.assertIsNone(self.app._device_id)
        for button, needs in self.app._buttons:
            if needs == "device":
                self.assertEqual(button.cget("state"), "disabled")
        self.app.profile_menu.set("Çalışma")
        with patch("gui.simpledialog.askstring", return_value="Renamed"):
            self.app._rename_profile()
        self.done()
        self.assertEqual(self.client.manager.profile_store.load("Renamed")["name"], "Renamed")

    def test_reconnect_clears_stale_known_forms(self):
        self.app._replace_entry(self.app.dpi_entries[0], "600")
        self.app._apply_dpi()
        self.done()
        self.app._command("reconnect")
        self.done()
        self.assertEqual(self.app.dpi_entries[0].get(), "400")
        self.assertEqual(self.app.polling_menu.get(), "Bilinmiyor")
        self.assertIsNone(self.app._preview_effect)
        self.assertEqual(self.app._state["settings"], {})

    def test_mouse_function_picker_and_independent_zone_colors(self):
        self.app.assignment_menu.set("Fare işlevi")
        self.app._assignment_changed()
        self.app.function_menu.set("DPI değiştir")
        self.app._bind()
        self.done()
        self.assertEqual(self.client.runner.driver.button_config["button4"], 0x30)
        for zone, value in zip(self.app.zone_entries, ("#FF0000", "#00FF00", "#0000FF"), strict=True):
            self.app._replace_entry(self.app.zone_entries[zone], value)
        self.app._apply_colors()
        self.done()
        self.assertIsNone(self.app._preview_effect)
        self.assertEqual(self.client.runner.driver.led_state["wheel"], (255, 0, 0))

    def test_profile_export_import_and_collision_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = str(Path(directory) / "profile.json")
            self.app.profile_menu.set("Çalışma")
            with patch("gui.filedialog.asksaveasfilename", return_value=filename):
                self.app._export_profile()
            self.done()
            self.assertTrue(Path(filename).is_file())
            with (
                patch("gui.filedialog.askopenfilename", return_value=filename),
                patch("gui.messagebox.askyesno", return_value=True) as confirm,
            ):
                self.app._import_profile()
                self.done()
            confirm.assert_called_once()
            self.assertEqual(len(self.client.manager.profile_store.list()), 1)

    def test_bad_color_dialog_initial_value_has_safe_default(self):
        self.app._replace_entry(self.app.color_entry, "wrong")
        with patch("gui.colorchooser.askcolor", return_value=((0, 0, 0), "#123456")) as chooser:
            self.app._choose_color()
        self.assertEqual(chooser.call_args.kwargs["initialcolor"], "#4AD2B1")
        self.assertEqual(self.app.color_entry.get(), "#123456")

    def test_close_during_io_discards_late_callbacks(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        called = []

        def task():
            entered.set()
            release.wait(2)
            finished.set()
            return "late"

        self.app._submit(task, called.append)
        self.assertTrue(entered.wait(1))
        self.app.close()
        release.set()
        self.assertTrue(finished.wait(1))
        self.assertEqual(called, [])
        self.assertEqual(self.app._callbacks, {})

    def test_corrupt_profile_warning_does_not_disable_device_actions(self):
        target = self.client.manager.profile_store.directory / ("0" * 64 + ".json")
        target.write_bytes(b"{")
        if os.name == "posix":
            target.chmod(0o600)
        self.app.refresh()
        self.done()
        self.assertIn("1 profil okunamadı", self.app.profile_issues.cget("text"))
        self.app.polling_menu.set("500")
        self.app._apply_polling()
        self.done()
        self.assertEqual(self.client.runner.driver.polling_rate, 500)

    def test_uncertain_usb_result_disables_writes_and_keeps_reconnect_available(self):
        self.app.client = lambda *_: {
            "status": "error",
            "code": "operation_uncertain",
            "message": "USB timeout",
        }
        self.app._apply_dpi()
        self.done()
        for button, needs in self.app._buttons:
            if needs == "device":
                self.assertEqual(button.cget("state"), "disabled")
            elif needs == "reconnect":
                self.assertEqual(button.cget("state"), "normal")

    def test_named_keyboard_picker_updates_hid_usage(self):
        self.app._pick_key("Left Shift")
        self.assertEqual(self.app.usage_entry.get(), "0xE1")
        self.app._bind()
        self.done()
        self.assertEqual(self.client.runner.driver.button_config["button4"], (0x51, 0xE1))
