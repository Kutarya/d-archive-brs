"""Reconstruct both snapshots from the review patches and compare source hashes."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("D:/BRS")
EVIDENCE = ROOT / "gelistirme-kanitlari"
CHECK = EVIDENCE / ("yama-kontrolu-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))


def main():
    CHECK.mkdir()
    snapshots = json.loads((ROOT / "inceleme/kanitlar/arsiv-envanteri.json").read_text(encoding="utf-8"))
    results = []
    for name, snapshot in zip(("Muvv", "Muvv_development_environment"), snapshots, strict=True):
        target = CHECK / name
        target.mkdir()
        for entry in snapshot["files"]:
            relative = Path(*Path(entry["path"]).parts[1:])
            destination = target / relative
            assert destination.resolve().is_relative_to(target.resolve())
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / "inceleme/kaynak" / entry["path"]).read_bytes())
        patch = EVIDENCE / f"{name}.patch"
        command = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "apply"]
        subprocess.run([*command, "--check", str(patch)], cwd=target, check=True, capture_output=True)
        subprocess.run([*command, str(patch)], cwd=target, check=True, capture_output=True)
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT / name, capture_output=True, check=True
        )
        files = sorted({value.decode("utf-8") for value in listing.stdout.split(b"\0") if value})
        for filename in files:
            assert (target / filename).read_bytes() == (ROOT / name / filename).read_bytes(), filename
        results.append(
            {"repository": name, "matching_files": len(files),
             "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}
        )
    result = {"successful": True, "source_reconstructed_from_zip_and_patch": results}
    (EVIDENCE / "yama-dogrulama.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
