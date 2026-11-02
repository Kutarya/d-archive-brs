"""Check preserved inputs, syntax, document links and built package contents."""

import ast
import hashlib
import json
import re
import subprocess
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path("D:/BRS")
EVIDENCE = ROOT / "gelistirme-kanitlari"
GIT = Path("C:/Program Files/Git/cmd/git.exe")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(repository):
    result = subprocess.run(
        [str(GIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repository,
        capture_output=True,
        check=True,
    )
    return sorted({value.decode("utf-8") for value in result.stdout.split(b"\0") if value})


def main():
    inputs = json.loads((ROOT / "inceleme/kanitlar/arsiv-envanteri.json").read_text(encoding="utf-8"))
    preserved = []
    for archive in inputs:
        assert sha256(ROOT / archive["archive"]) == archive["archive_sha256"], archive["archive"]
        for entry in archive["files"]:
            path = ROOT / "inceleme/kaynak" / entry["path"]
            assert sha256(path) == entry["sha256"], str(path)
        preserved.append(
            {
                "archive": archive["archive"],
                "sha256": archive["archive_sha256"],
                "preserved_source_files": len(archive["files"]),
            }
        )
    repositories = []
    syntax_count = 0
    link_count = 0
    for name in ("Muvv", "Muvv_development_environment"):
        repository = ROOT / name
        paths = source_files(repository)
        for filename in paths:
            path = repository / filename
            assert path.resolve().is_relative_to(repository.resolve()), filename
            assert not path.is_symlink(), filename
            if path.suffix == ".py":
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path), feature_version=(3, 10))
                syntax_count += 1
            elif path.suffix == ".md":
                content = path.read_text(encoding="utf-8-sig")
                fences = sum(line.lstrip().startswith("```") for line in content.splitlines())
                assert fences % 2 == 0, f"Unclosed Markdown fence: {filename}"
                for target in re.findall(r"\[[^\]\n]*\]\(([^\)\n]+)\)", content):
                    target = target.strip("<>").split("#", 1)[0]
                    if not target or "://" in target or target.startswith("mailto:"):
                        continue
                    assert (path.parent / unquote(target)).exists(), f"Broken link: {filename} -> {target}"
                    link_count += 1
        diff = subprocess.run(
            [str(GIT), "diff", "--check"], cwd=repository, capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True
        )
        repositories.append({"repository": name, "files": len(paths), "diff_check": diff.returncode})
    wheel = ROOT / "Muvv/dist/muvv-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as archive:
        module_count = 0
        for entry in archive.infolist():
            assert not entry.filename.startswith("/") and ".." not in Path(entry.filename).parts
            if entry.filename.endswith(".py"):
                assert archive.read(entry) == (ROOT / "Muvv" / entry.filename).read_bytes(), entry.filename
                module_count += 1
        assert not any(".venv/" in entry.filename or ".git/" in entry.filename for entry in archive.infolist())
    sdist = ROOT / "Muvv/dist/muvv-0.1.0.tar.gz"
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        assert all(not member.issym() and not member.islnk() for member in members)
        assert all(not member.name.startswith("/") and ".." not in Path(member.name).parts for member in members)
        assert all("/.venv/" not in member.name and "/.git/" not in member.name for member in members)
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "successful": True,
        "original_archives_and_sources_unchanged": preserved,
        "repositories": repositories,
        "python_files_parsed_for_3_10": syntax_count,
        "local_document_links_checked": link_count,
        "wheel_source_modules_matching": module_count,
        "artifacts": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (wheel, sdist)
        ],
    }
    (EVIDENCE / "kaynak-dogrulama.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
