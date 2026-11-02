"""Opt-in checks for a physical mouse. Writes are disabled by default."""

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cli import send_command  # noqa: E402
from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse  # noqa: E402
from managers.device_runner import DeviceRunner  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Enumerate supported HID paths without writing")
    parser.add_argument(
        "--mode", choices=("connect", "color", "dpi", "stages", "buttons", "vitray", "ipc"), default="connect"
    )
    parser.add_argument("--device", help="Exact HID path; for ipc mode use a daemon device ID")
    parser.add_argument(
        "--allow-write", action="store_true", help="Explicitly permit the requested device change"
    )
    parser.add_argument("--color", help="RGB hex color")
    parser.add_argument("--stages", nargs=5, type=int, help="Explicit replacement DPI values")
    parser.add_argument("--active", type=int, default=0)
    parser.add_argument("--button", default="button5")
    parser.add_argument("--usage", type=lambda value: int(value, 0), default=4)
    parser.add_argument(
        "--initialize-buttons", action="store_true", help="Replace unread button assignments with defaults"
    )
    parser.add_argument("--effect", choices=("static", "breathing", "wave", "spectrum"), default="wave")
    parser.add_argument("--duration", type=float, default=3)
    parser.add_argument("--persist", action="store_true", help="Also send the on-board save command")
    options = parser.parse_args(argv)
    if options.list:
        hid = importlib.import_module("hid")
        devices = [
            {
                "path": os.fsdecode(entry["path"]),
                "vendor_id": entry["vendor_id"],
                "product_id": entry["product_id"],
            }
            for entry in hid.enumerate(0x1038, 0x1870)
            if entry.get("interface_number") == 3
        ]
        print(json.dumps(devices, indent=2))
        return 0
    if not options.device:
        parser.error("--device is required; list paths before selecting one.")
    if options.mode != "connect" and not options.allow_write:
        parser.error("This check changes device settings. Use --allow-write explicitly.")
    if options.mode in ("dpi", "stages") and options.stages is None:
        parser.error("--stages must specify all five replacement DPI values.")
    if options.mode == "color" and options.color is None:
        parser.error("--color is required.")
    if options.mode == "buttons" and not options.initialize_buttons:
        parser.error("--initialize-buttons is required because current assignments cannot be read.")
    if not 0 < options.duration <= 60:
        parser.error("--duration must be between 0 and 60 seconds.")
    if options.mode == "connect" and options.persist:
        parser.error("--persist requires a write mode.")
    if options.mode == "ipc":
        response = send_command("set-effect", {"device": options.device, "effect": options.effect})
        if response.get("status") == "ok" and options.persist:
            response = send_command("save", {"device": options.device})
        print(json.dumps(response, indent=2))
        return 0 if response.get("status") == "ok" else 1
    runner = DeviceRunner(Rival3Gen2Mouse, device_path=os.fsencode(options.device))
    result = 0
    try:
        runner.start()
        receipt = {"connected": True, "path": options.device, "reports": 0}
        if options.mode == "color":
            receipt = runner.set_color(options.color)
        elif options.mode in ("dpi", "stages"):
            receipt = runner.set_dpi_stages(options.stages, options.active)
        elif options.mode == "buttons":
            receipt = runner.bind_key(options.button, options.usage, initialize=True, persist=options.persist)
        elif options.mode == "vitray":
            receipt = runner.set_effect(options.effect)
            time.sleep(options.duration)
        if options.persist and options.mode != "buttons":
            runner.save_profile()
            receipt["persistence_requested"] = True
        print(json.dumps(receipt, indent=2))
        print(
            "USB writes do not verify sensor behavior or firmware persistence. Record those observations separately."
        )
    finally:
        if not runner.stop():
            print("USB backend is still closing.", file=sys.stderr)
            result = 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
