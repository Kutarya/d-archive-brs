"""Verify installed wheel modules and the GUI entry point outside the source tree."""

import importlib
import importlib.metadata
import json
import runpy
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPORT = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / 'temiz-kurulum.json'
SITE = Path(sys.prefix).resolve() / 'Lib/site-packages'


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


modules = {}
for name in ('gui', 'cli', 'demo', 'app_version', 'drivers.base_mouse', 'managers.device_manager'):
    module = importlib.import_module(name)
    location = Path(module.__file__).resolve()
    check(location.is_relative_to(SITE), f'Module did not load from the clean environment: {name}')
    modules[name] = location.relative_to(SITE).as_posix()

check(importlib.metadata.version('muvv') == '0.4.0', 'Installed version differs')
import gui

original_loop = gui.ctk.CTk.mainloop
callback_errors = []


def checked_loop(root, *args, **kwargs):
    root.report_callback_exception = lambda *values: callback_errors.append(str(values[1]))
    # Use the application's registered close callback so the normal lifecycle runs.
    root.after(1500, lambda: root.eval(root.protocol('WM_DELETE_WINDOW')))
    return original_loop(root, *args, **kwargs)


gui.ctk.CTk.mainloop = checked_loop
try:
    check(gui.main(['--demo']) == 0, 'Real GUI demo entry point failed')
finally:
    gui.ctk.CTk.mainloop = original_loop
check(not callback_errors, f'GUI callback errors: {callback_errors}')

workflow = runpy.run_path(str(OUT / 'temiz-gui-kontrolu.py'), run_name='clean_gui_workflow')
check(workflow['main']([]) == 0, 'Installed DPI/RGB/effect workflow failed')
remaining = [thread.name for thread in threading.enumerate() if thread.name.startswith('muvv-')]
check(not remaining, f'Application workers remained: {remaining}')

report = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'successful': True,
    'version': '0.4.0',
    'python': sys.version,
    'platform': sys.platform,
    'installed_modules_from_site_packages': modules,
    'normal_gui_demo_entry_point': 'passed',
    'dpi_rgb_effect_workflows': 'passed',
    'callback_errors': callback_errors,
    'remaining_workers': remaining,
    'physical_hid_access': False,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
