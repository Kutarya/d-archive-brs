"""Run automatic checks without opening a physical HID device."""

import argparse
import io
import json
import logging
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, help="Save the test summary")
    options = parser.parse_args(argv)
    logging.basicConfig(level=logging.ERROR)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.discover(str(ROOT / "test" / "unit")))
    for filename in ("test_capabilities_info.py", "test_effect_options.py", "test_validator.py"):
        suite.addTests(loader.discover(str(ROOT / "test" / "manager"), pattern=filename))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    sys.stdout.write(stream.getvalue())
    summary = {
        "tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
        "platform": sys.platform,
        "python": sys.version,
        "hardware_access": False,
        "successful": result.wasSuccessful(),
    }
    if options.json:
        options.json.parent.mkdir(parents=True, exist_ok=True)
        options.json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
