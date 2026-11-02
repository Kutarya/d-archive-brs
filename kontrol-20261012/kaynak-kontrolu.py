"""Read-only source and archive checks for the 12 October handoff."""

import ast
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/BRS')
OUT = ROOT / 'kontrol-20261012'


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


sources = {}
counts = {}
for repository in ('Muvv', 'Muvv_development_environment'):
    directory = ROOT / repository
    listing = subprocess.run(['git', 'ls-files', '-z'], cwd=directory, capture_output=True, check=True)
    files = sorted({name.decode('utf-8') for name in listing.stdout.split(b'\0') if name})
    counts[repository] = len(files)
    for name in files:
        path = directory / name
        check(path.is_file() and not path.is_symlink(), f'Invalid source: {name}')
        check(path.resolve().is_relative_to(directory.resolve()), f'Path outside repository: {name}')
        check(not {'.git', '.venv', '__pycache__', '.env', 'Note.md'}.intersection(path.parts), name)
        sources[f'{repository}/{name}'] = path.read_bytes()

latest = ROOT / 'teslim/Muvv-0.4.0-20261011/Muvv-0.4.0-kaynak.zip'
with zipfile.ZipFile(latest) as archive:
    check(archive.testzip() is None, 'Previous source ZIP is corrupt')
    check(set(archive.namelist()) == set(sources), 'Current source file list differs from the latest release')
    for name, data in sources.items():
        check(archive.read(name) == data, f'Current source differs from 0.4.0: {name}')

with zipfile.ZipFile(ROOT / 'teslim/Muvv-0.3.0-20261011/Muvv-0.3.0-kaynak.zip') as archive:
    before = {name: archive.read(name) for name in archive.namelist()}
    changes = [name for name, data in sources.items() if before.get(name) != data]
    removed = sorted(set(before) - set(sources))

python_files = []
for name, data in sources.items():
    if name.endswith('.py'):
        ast.parse(data.decode('utf-8-sig'), filename=name, feature_version=(3, 10))
        python_files.append(name)

wheel = ROOT / 'teslim/Muvv-0.4.0-20261011/muvv-0.4.0-py3-none-any.whl'
with zipfile.ZipFile(wheel) as archive:
    check(archive.testzip() is None, 'Wheel is corrupt')
    modules = [name for name in archive.namelist() if name.endswith('.py')]
    for name in modules:
        check(sources.get('Muvv/' + name) == archive.read(name), f'Wheel source mismatch: {name}')

preserved = []
for directory in sorted((ROOT / 'teslim').iterdir()):
    checksums = directory / 'SHA256SUMS.txt'
    if not checksums.is_file():
        continue
    for line in checksums.read_text(encoding='utf-8-sig').splitlines():
        expected, name = line.split(maxsplit=1)
        path = directory / name.lstrip('*')
        check(path.resolve().is_relative_to(directory.resolve()), 'Unsafe previous checksum path')
        check(path.is_file() and sha(path.read_bytes()) == expected, f'Old release changed: {path}')
        preserved.append(f'{directory.name}/{path.name}')

result = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'successful': True,
    'version': '0.4.0',
    'source_files': counts,
    'current_sources_match_latest_0_4_zip': True,
    'changed_files_since_0_3': changes,
    'removed_files_since_0_3': removed,
    'python_3_10_syntax_files': len(python_files),
    'wheel_source_modules_match': len(modules),
    'wheel_sha256': sha(wheel.read_bytes()),
    'previous_delivery_files_preserved': len(preserved),
    'physical_hid_access': False,
}
(OUT / 'kaynak-kontrolu.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'kaynak-manifest.json').write_text(json.dumps([
    {'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(sources.items())
], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
