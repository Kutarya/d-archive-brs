import faulthandler
import gc
import os
import sys
import time
import unittest
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
