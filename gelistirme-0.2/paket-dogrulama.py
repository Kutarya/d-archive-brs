"""Install the built wheel outside the source tree and record reproducible checks."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("D:/BRS")
SOURCE = WORKSPACE / "Muvv"
EVIDENCE = WORKSPACE / "gelistirme-0.2"
CHECK = EVIDENCE / ("paket-kontrolu-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
RECORDS = []
ENVIRONMENT = dict(os.environ)
ENVIRONMENT.pop("PYTHONPATH", None)
ENVIRONMENT["PYTHONUTF8"] = "1"
ENVIRONMENT["PYTHONNOUSERSITE"] = "1"


def run(arguments, expected=0):
    result = subprocess.run(
        [str(argument) for argument in arguments],
        cwd=CHECK,
        env=ENVIRONMENT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    RECORDS.append(
        {
            "command": [str(argument) for argument in arguments],
            "exit_code": result.returncode,
            "expected_exit_code": expected,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    print(f"{Path(str(arguments[0])).name}: exit {result.returncode}", flush=True)
    if result.returncode != expected:
        raise RuntimeError(f"Package check failed: {arguments!r}\n{result.stderr}")


GUI_CHECK = """
import json
import sys
import time
import tempfile
from pathlib import Path
from demo import DemoClient
from gui import MuvvApp, ctk
from app_version import __version__
from importlib.metadata import version
from profile_io import read_profile_file, write_profile_file

ctk.set_appearance_mode('dark')
root = ctk.CTk()
root.withdraw()
errors = []
root.report_callback_exception = lambda *args: errors.append(str(args[1]))
client = DemoClient()
app = MuvvApp(root, client=client, demo=True)

def pump(predicate):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(0.01)
    raise RuntimeError('Packaged GUI deadline exceeded')

try:
    assert version('muvv') == __version__ == '0.2.0'
    pump(lambda: app._device_id is not None and not app._busy)
    app.dpi_entries[0].delete(0, 'end')
    app.dpi_entries[0].insert(0, '600')
    app._apply_dpi()
    pump(lambda: not app._busy)
    assert client.runner.driver.dpi_levels[0] == 600
    app.profile_name.insert(0, 'Temiz Kurulum')
    app._save_profile()
    pump(lambda: not app._busy)
    assert client.manager.profile_store.load('Temiz Kurulum')['settings']['dpi']['stages'][0] == 600
    app._command('stop-effect')
    pump(lambda: not app._busy)
    assert client.runner.get_state()['effect'] is None
    for zone, color in zip(app.zone_entries, ('#FF0000', '#00FF00', '#0000FF'), strict=True):
        app._replace_entry(app.zone_entries[zone], color)
    app._apply_colors()
    pump(lambda: not app._busy)
    assert client.runner.driver.led_state['wheel'] == (255, 0, 0)
    app.assignment_menu.set('Fare işlevi')
    app.function_menu.set('DPI değiştir')
    app._bind()
    pump(lambda: not app._busy)
    assert client.runner.driver.button_config['button4'] == 0x30
    profile = client.manager.profile_store.load('Temiz Kurulum')
    with tempfile.TemporaryDirectory() as directory:
        filename = Path(directory) / 'profile.json'
        write_profile_file(filename, profile)
        assert read_profile_file(filename) == profile
    app._command('rename-profile', {'name': 'Temiz Kurulum', 'new_name': 'Paket Testi'}, device=False)
    pump(lambda: not app._busy)
    assert 'Paket Testi' in app.profile_menu.cget('values')
    assert not errors, errors
    assert 'hid' not in sys.modules
    print(json.dumps({'gui': 'passed', 'hardware_access': False, 'callback_errors': errors}))
finally:
    app.close()
    client.close()
"""


def main():
    CHECK.mkdir()
    wheel = SOURCE / "dist" / "muvv-0.2.0-py3-none-any.whl"
    interpreter = CHECK / ".venv" / "Scripts" / "python.exe"
    successful = False
    try:
        run([sys.executable, "-m", "venv", CHECK / ".venv"])
        run([interpreter, "-m", "pip", "install", "--no-index", "--no-deps", wheel])
        run(
            [
                interpreter,
                "-I",
                "-c",
                "import cli, daemon, gui; from importlib.metadata import version; print(version('muvv')); print(cli.__file__); assert gui.ctk is None",
            ]
        )
        run([CHECK / ".venv/Scripts/muvv.exe", "--help"])
        run([CHECK / ".venv/Scripts/muvv.exe", "--version"])
        run([CHECK / ".venv/Scripts/muvv.exe", "--json", "doctor"])
        run([CHECK / ".venv/Scripts/muvv-gui.exe", "--demo"], expected=1)
        run([interpreter, "-m", "pip", "install", "--upgrade", "pip==26.2.1"])
        run([interpreter, "-m", "pip", "install", "--require-hashes", "-r", SOURCE / "requirements-lock.txt"])
        run([interpreter, "-m", "pip", "check"])
        run([interpreter, "-I", "-c", GUI_CHECK])
        successful = True
    finally:
        report = {
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "platform": sys.platform,
            "wheel": wheel.name,
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "outside_source_tree": True,
            "hardware_access": False,
            "successful": successful,
            "checks": RECORDS,
        }
        (EVIDENCE / "paket-dogrulama.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
