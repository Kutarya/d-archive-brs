"""Exercise the desktop controls with an isolated in-memory device."""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from demo import DemoClient  # noqa: E402
from gui import MuvvApp, ctk  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", type=Path)
    options = parser.parse_args(argv)
    if ctk is None:
        parser.error("Install the gui extra first.")
    client = DemoClient()
    root = ctk.CTk()
    ctk.set_appearance_mode("dark")
    application = MuvvApp(root, client=client, demo=True)
    root.geometry("1050x760+80+60")
    errors = []
    root.report_callback_exception = lambda *values: errors.append(str(values[1]))

    def pump(predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            root.update()
            if predicate():
                return
            time.sleep(0.01)
        raise RuntimeError("GUI operation exceeded its deadline.")

    try:
        pump(lambda: application._device_id is not None and not application._busy)
        if options.snapshots:
            from PIL import ImageGrab

            options.snapshots.mkdir(parents=True, exist_ok=True)
            for name, filename in (
                ("Aydınlatma", "rgb.png"),
                ("DPI ve hız", "dpi.png"),
                ("Tuşlar", "buttons.png"),
                ("Profiller", "profiles.png"),
            ):
                application.tabs.set(name)
                if name == "Profiller":
                    application._show_profile("Çalışma")
                    pump(lambda: not application._busy)
                # Allow native paint events to complete before capturing this window.
                deadline = time.monotonic() + 0.3
                pump(lambda deadline=deadline: time.monotonic() >= deadline)
                ImageGrab.grab(window=root.winfo_id()).save(options.snapshots / filename)
            application.tabs.set("Aydınlatma")
            application._pages["Aydınlatma"]._parent_canvas.yview_moveto(1)
            deadline = time.monotonic() + 0.3
            pump(lambda deadline=deadline: time.monotonic() >= deadline)
            ImageGrab.grab(window=root.winfo_id()).save(options.snapshots / "rgb-zones.png")
            root.geometry("920x710+80+60")
            application.tabs.set("Tuşlar")
            deadline = time.monotonic() + 0.3
            pump(lambda deadline=deadline: time.monotonic() >= deadline)
            ImageGrab.grab(window=root.winfo_id()).save(options.snapshots / "minimum-size.png")
        application.tabs.set("Aydınlatma")
        application.effect_menu.set("Spektrum")
        application._apply_effect()
        pump(lambda: not application._busy)
        assert client.runner.get_state()["effect"]["name"] == "spectrum"
        application.tabs.set("DPI ve hız")
        application.dpi_entries[0].delete(0, "end")
        application.dpi_entries[0].insert(0, "600")
        application._apply_dpi()
        pump(lambda: not application._busy)
        assert client.runner.driver.dpi_levels[0] == 600
        application._command("stop-effect")
        pump(lambda: not application._busy)
        assert client.runner.get_state()["effect"] is None
        for zone, color in zip(application.zone_entries, ("#FF0000", "#00FF00", "#0000FF"), strict=True):
            application._replace_entry(application.zone_entries[zone], color)
        application._apply_colors()
        pump(lambda: not application._busy)
        assert client.runner.driver.led_state["wheel"] == (255, 0, 0)
        if errors:
            raise RuntimeError(f"Tk callback errors: {errors}")
        print(
            json.dumps(
                {
                    "status": "passed",
                    "mode": "isolated_demo",
                    "hardware_access": False,
                    "tabs": 4,
                    "callback_errors": errors,
                },
                ensure_ascii=True,
            )
        )
    finally:
        application.close()
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
