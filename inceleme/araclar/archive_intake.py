"""Read ZIP snapshots safely and retain evidence without executing their contents."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import stat
import zipfile

ROOT = Path(r"D:\BRS")
DEST = ROOT / "inceleme" / "kaynak"
records = []
for archive_path in sorted(ROOT.glob("*.zip")):
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        if sum(entry.file_size for entry in entries) > 50_000_000:
            raise ValueError("Expanded archive exceeds intake limit")
        targets = set()
        for entry in entries:
            name = entry.filename
            parts = PurePosixPath(name).parts
            if "\\" in name or ":" in name or name.startswith("/") or ".." in parts:
                raise ValueError(f"Unsafe ZIP path: {name!r}")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Symlink rejected: {name!r}")
            target = (DEST / Path(*parts)).resolve()
            target.relative_to(DEST.resolve())
            folded = str(target).casefold()
            if folded in targets:
                raise ValueError(f"Duplicate ZIP target: {name!r}")
            targets.add(folded)
            if target.exists():
                raise FileExistsError(target)
        files = []
        for entry in entries:
            target = DEST / Path(*PurePosixPath(entry.filename).parts)
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            data = archive.read(entry)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
            files.append({"path": entry.filename, "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()})
        records.append({"archive": archive_path.name,
                        "archive_bytes": archive_path.stat().st_size,
                        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                        "zip_comment": archive.comment.decode("utf-8", errors="replace"),
                        "file_count": len(files), "expanded_bytes": sum(x["bytes"] for x in files),
                        "files": files})
evidence = ROOT / "inceleme" / "kanitlar"
evidence.mkdir(parents=True, exist_ok=True)
(evidence / "arsiv-envanteri.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
for record in records:
    print(json.dumps({key: value for key, value in record.items() if key != "files"},
                     ensure_ascii=False))
