"""Manual device check; no tests are collected automatically from this file."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tools.hardware_check import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--mode", "vitray", *sys.argv[1:]]))
