"""Verify the completed archives, manifests and portable document links."""

import hashlib
import json
import posixpath
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote

root = Path("D:/BRS")
destination = root / "teslim/Muvv-0.3.0-20261011"


def digest(data):
    return hashlib.sha256(data).hexdigest()


manifest = json.loads((destination / "DOSYA-MANIFEST.json").read_text(encoding="utf-8"))
external = []
for line in (destination / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    expected, filename = line.split("  ", 1)
    path = destination / filename
    assert path.resolve().is_relative_to(destination.resolve())
    assert digest(path.read_bytes()) == expected, filename
    external.append(filename)
assert len(external) == len(set(external)) == 10
assert set(external) == {path.name for path in destination.iterdir() if path.name != "SHA256SUMS.txt"}

with zipfile.ZipFile(destination / "Muvv-0.3.0-kaynak.zip") as archive:
    assert archive.testzip() is None
    sources = {entry["path"]: entry for entry in manifest["source_files"]}
    assert set(archive.namelist()) == set(sources)
    for name, entry in sources.items():
        data = archive.read(name)
        assert digest(data) == entry["sha256"] and len(data) == entry["bytes"]
        assert data == (root / name).read_bytes(), name

links = 0
with zipfile.ZipFile(destination / "Muvv-0.3.0-inceleme.zip") as archive:
    assert archive.testzip() is None
    names = set(archive.namelist())
    assert len(names) == len(archive.namelist()) == 143
    assert archive.read("DOSYA-MANIFEST.json") == (destination / "DOSYA-MANIFEST.json").read_bytes()
    for entry in manifest["review_files"]:
        data = archive.read(entry["path"])
        assert digest(data) == entry["sha256"] and len(data) == entry["bytes"], entry["path"]
    checksummed = set()
    for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert name not in checksummed
        checksummed.add(name)
        assert digest(archive.read(name)) == expected, name
    assert checksummed == names - {"SHA256SUMS.txt"}
    for name in names:
        assert not {".git", ".venv", "__pycache__", "Note.md", ".env"}.intersection(Path(name).parts)
        assert not name.startswith("/") and ".." not in Path(name).parts
        if not name.endswith(".md"):
            continue
        content = archive.read(name).decode("utf-8-sig")
        for target in re.findall(r"\[[^\]\n]*\]\(([^\)\n]+)\)", content):
            target = unquote(target.strip("<>").split("#", 1)[0])
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert not re.match(r"^[A-Za-z]:", target), (name, target)
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            assert resolved in names or any(path.startswith(resolved.rstrip("/") + "/") for path in names), (name, target)
            links += 1

result = {"successful": True, "source_files_matching_current_source": len(sources),
          "review_archive_entries": len(names), "external_checksums": len(external),
          "internal_checksums": len(checksummed), "portable_document_links": links,
          "crc_and_manifest_checks": "passed"}
(root / "gelistirme-0.3/teslim-son-kontrol.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
