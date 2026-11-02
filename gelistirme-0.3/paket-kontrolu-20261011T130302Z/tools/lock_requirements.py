"""Regenerate the runtime lock from the pinned public PyPI releases."""

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = {"hidapi": "0.15.0", "customtkinter": "6.0.0", "darkdetect": "0.8.0", "packaging": "26.3"}


def main():
    lines = ["# Runtime and GUI dependencies. Hashes cover the release's wheels and source archive."]
    for name, version in PACKAGES.items():
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=20) as response:
            release = json.load(response)
        if release["info"]["version"] != version:
            raise RuntimeError(f"Unexpected release metadata for {name}.")
        hashes = sorted(
            {artifact["digests"]["sha256"] for artifact in release["urls"] if not artifact.get("yanked")}
        )
        if not hashes:
            raise RuntimeError(f"No non-yanked artifacts found for {name}.")
        lines.append(f"{name}=={version} \\")
        lines.extend(
            f"    --hash=sha256:{digest}" + (" \\" if index < len(hashes) - 1 else "")
            for index, digest in enumerate(hashes)
        )
    (ROOT / "requirements-lock.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
