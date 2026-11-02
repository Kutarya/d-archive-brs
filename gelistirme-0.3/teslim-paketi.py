"""Create a separate immutable 0.3 delivery from validated source and evidence."""

import hashlib
import json
import posixpath
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path("D:/BRS")
EVIDENCE = ROOT / "gelistirme-0.3"
DESTINATION = ROOT / "teslim/Muvv-0.3.0-20261011"
SUFFIXES = {".py", ".md", ".toml", ".txt", ".yml", ".rules", ".service", ".in"}
HIDDEN_NAMES = {".gitignore", ".gitattributes"}
PROHIBITED = {".git", ".venv", "__pycache__", ".ruff_cache", "node_modules", "Note.md", ".env"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(name, path):
    return {"path": name, "bytes": path.stat().st_size, "sha256": digest(path)}


def json_file(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def write_zip(path, entries):
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in sorted(entries.items()):
            assert not PROHIBITED.intersection(Path(name).parts), name
            assert not Path(name).is_absolute() and ".." not in Path(name).parts, name
            archive.write(source, name)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(entries)
        for name, source in entries.items():
            assert archive.read(name) == source.read_bytes(), name


def portable_historical_reports(entries):
    directory = EVIDENCE / "rapor-kopyalari"
    directory.mkdir(exist_ok=True)
    pattern = r"\[([^\]\n]*)\]\(([^\)\n]+)\)"
    for name in ("inceleme/MUVV-INCELEME-RAPORU.md", "inceleme/DOSYA-HARITASI.md"):
        content = entries[name].read_text(encoding="utf-8-sig")

        def relocate(match, name=name):
            label, target = match.groups()
            target = unquote(target.strip("<>"))
            if not target.startswith("D:/BRS/"):
                return match.group(0)
            relative = target[len("D:/BRS/") :]
            if relative in entries:
                link = quote(posixpath.relpath(relative, posixpath.dirname(name)), safe="/._-")
                return f"[{label}]({link})"
            # Original snapshots and personal notes are retained locally, outside this delivery.
            return f"{label} (`{relative}`)"

        copy = directory / Path(name).name
        content = re.sub(pattern, relocate, content)
        content += "\n\nBu teslim kopyasında yerel mutlak bağlantılar taşınabilir hale getirildi. Başlangıç kaynaklarının satır referansları metin olarak tutulur; bu dosyalar orijinal ZIP'lerde ve yerel inceleme alanında korunur.\n"
        copy.write_text(content, encoding="utf-8", newline="\n")
        entries[name] = copy


def main():
    tests = json_file("test-sonuclari.json")
    package = json_file("paket-dogrulama.json")
    source_check = json_file("kaynak-dogrulama.json")
    patches = json_file("yama-dogrulama.json")
    gui = json_file("arayuz-smoke.json")
    assert tests["successful"] and tests["tests"] == 159 and tests["passed"] == 145
    assert tests["failures"] == tests["errors"] == 0 and len(tests["skipped"]) == 14
    assert package["successful"] and source_check["successful"] and patches["successful"]
    assert gui["status"] == "passed" and gui["callback_errors"] == []
    wheel_tests = json_file("wheel-test-sonuclari.json")
    assert wheel_tests["successful"]
    assert all(wheel_tests[key] == tests[key] for key in ("tests", "passed", "errors", "failures"))
    assert len(wheel_tests["skipped"]) == 14
    log = (EVIDENCE / "test-kaydi.log").read_text(encoding="utf-8")
    assert sum("test_gui.GUITests." in line for line in log.splitlines()) == 29
    simulation = json_file("sanal-senaryolar.json")
    assert simulation["successful"] and not simulation["physical_hid_access"]
    assert simulation["remaining_workers"] == []
    assert simulation["scenarios"]["reconnect_and_profiles"]["cycles"] == 200
    wheel = ROOT / "Muvv/dist/muvv-0.3.0-py3-none-any.whl"
    assert digest(wheel) == package["wheel_sha256"]
    for entry in source_check["artifacts"]:
        assert entry["sha256"] == digest(ROOT / "Muvv/dist" / entry["name"])
    for entry in patches["source_reconstructed_from_zip_and_patch"]:
        assert entry["patch_sha256"] == digest(EVIDENCE / f"{entry['repository']}.patch")

    source_entries = {}
    for name in ("Muvv", "Muvv_development_environment"):
        repository = ROOT / name
        listing = subprocess.run(["git", "ls-files", "-z"], cwd=repository, capture_output=True, check=True)
        for filename in sorted({value.decode("utf-8") for value in listing.stdout.split(b"\0") if value}):
            path = repository / filename
            assert path.resolve().is_relative_to(repository.resolve()) and not path.is_symlink(), filename
            assert path.suffix in SUFFIXES or path.name in HIDDEN_NAMES, filename
            source_entries[f"{name}/{filename}"] = path
    assert len(source_entries) == sum(entry["files"] for entry in source_check["repositories"]) == 94
    review_entries = dict(source_entries)
    for name in ("GELISTIRME-0.3-RAPORU.md", "GELISTIRME-0.3-PLANI.md"):
        review_entries[name] = ROOT / name
    for name in ("MUVV-INCELEME-RAPORU.md", "DOSYA-HARITASI.md"):
        review_entries[f"inceleme/{name}"] = ROOT / "inceleme" / name
    for name in ("arsiv-envanteri.json", "offline-inceleme-sonuclari.json"):
        review_entries[f"inceleme/kanitlar/{name}"] = ROOT / "inceleme/kanitlar" / name
    evidence_names = (
        "test-sonuclari.json",
        "wheel-test-sonuclari.json",
        "wheel-test-kaydi.log",
        "sanal-senaryolar.json",
        "sanal-senaryolar.log",
        "arayuz-once.log",
        "yeniden-baglanti-once.log",
        "yama-dogrulama-kaydi.log",
        "bagimlilik-denetimi.log",
        "gelistirme-bagimlilik-denetimi.log",
        "yama-olustur.py",
        "test-kaydi.log",
        "kapsama.json",
        "paket-dogrulama.json",
        "paket-kontrol-kaydi.log",
        "kaynak-dogrulama.json",
        "kaynak-dogrulama-kaydi.log",
        "yama-dogrulama.json",
        "arayuz-smoke.json",
        "bagimlilik-denetimi.json",
        "gelistirme-bagimlilik-denetimi.json",
        "ortam-tanisi.json",
        "paket-olusturma.log",
        "duzenlenebilir-kurulum.log",
        "ruff-check.log",
        "ruff-format.log",
        "paket-dogrulama.py",
        "kaynak-dogrulama.py",
        "yama-dogrulama.py",
        "teslim-paketi.py",
        "Muvv.patch",
        "Muvv_development_environment.patch",
    )
    for name in evidence_names:
        review_entries[f"gelistirme-0.3/{name}"] = EVIDENCE / name
    for name in ("rgb.png", "rgb-zones.png", "dpi.png", "buttons.png", "profiles.png", "minimum-size.png"):
        review_entries[f"gelistirme-0.3/arayuz/{name}"] = EVIDENCE / "arayuz" / name
    for name in ("muvv-0.3.0-py3-none-any.whl", "muvv-0.3.0.tar.gz"):
        review_entries[f"paketler/{name}"] = ROOT / "Muvv/dist" / name
    for source in review_entries.values():
        assert source.is_file() and not source.is_symlink(), source
    portable_historical_reports(review_entries)
    for target in re.findall(
        r"\[[^\]\n]*\]\(([^\)\n]+)\)", (ROOT / "GELISTIRME-0.3-RAPORU.md").read_text(encoding="utf-8")
    ):
        target = unquote(target.strip("<>").split("#", 1)[0])
        assert target in review_entries, target

    for name, source in review_entries.items():
        if source.suffix != ".md":
            continue
        for target in re.findall(r"\[[^\]\n]*\]\(([^\)\n]+)\)", source.read_text(encoding="utf-8-sig")):
            target = unquote(target.strip("<>").split("#", 1)[0])
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            assert resolved in review_entries or any(
                path.startswith(resolved.rstrip("/") + "/") for path in review_entries
            ), (name, target)

    DESTINATION.mkdir(parents=True, exist_ok=False)
    handoff = DESTINATION / "TESLIM.md"
    handoff.write_text(
        """# Muvv 0.3.0 yerel teslimi

11 Ekim 2026. İki özel repo ZIP'i üzerinden geliştirilmiş ayrı sürüm.

- `Muvv-0.3.0-kaynak.zip`: uygulama ve geliştirme notları, toplam 94 dosya.
- `Muvv-0.3.0-inceleme.zip`: aynı kaynak, rapor, test kayıtları, altı görsel, iki yama ve kurulum paketleri.
- Wheel, tar.gz, manifest ve SHA256 dosyaları ayrıca verilir.

İnceleme ZIP'ini ayrı klasöre açıp `GELISTIRME-0.3-RAPORU.md` ile başlayın. Kurulum `Muvv/README.md` içinde. Demo `muvv-gui --demo` ile çalışır ve USB açmaz.

Kaynak ortamında ve ayrı klasöre kurulan wheel'de 159 test: 145 geçti, Linux/POSIX'e özgü 14 test atlandı, hata yok. Toplamda 29 gerçek Tk senaryosu var. Kurulan paketten 2.000 parçalı mesaj, 800 eşzamanlı işlem, 200 yeniden bağlantı ve dört USB kesilme noktası da sınandı. Linux UID/izin/flock/udev, gerçek fare ve uzak CI kabulü henüz yapılmadı.

Yeni oturum koruması, arayüzde bekleyen komutun yeniden bağlanan cihaza yazmasını önler. Meşgul cihaz son değerleri korur. Kapanış işçiler bitene kadar servis kilidini tutar. Profil sayfalarındaki hata cihaz ekranını silmez. Profil şeması ve USB rapor biçimi korunur.

İki yama kendi orijinal ZIP başlangıcına göredir; 0.2 üstüne artımlı yama değildir. Repo sahibinin güncel kaynakları üzerinde ayrı inceleme dalında önce kontrol edin:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna uygulanır. Yamalar yerel başlangıç kopyalarına uygulanıp 82 + 12 dosya byte düzeyinde karşılaştırıldı. Git geçmişi eklenmedi. Orijinal ZIP'ler, 45 başlangıç dosyası ve önceki 0.1/0.2 teslimleri hashleriyle korunur.

Kaynak ZIP'i sanal ortam, Git iç dosyaları, kullanıcı profilleri ve kişisel geliştirici notunu içermez. İnceleme kopyasındaki geçmiş raporların bağlantıları taşınabilirdir; pakette olmayan özgün kaynak satır referansları düz metin olarak tutulur.

İç SHA dosyası inceleme arşivinin girişlerini, dış SHA dosyası teslim klasörünü doğrular. Manifest ve checksum dosyası kendi içeriğinde kendisini listelemez. Kanıt yardımcıları bu Windows çalışma alanına aittir; proje testleri `Muvv/tools/check.py` ve `Muvv/tools/simulation_check.py` ile tekrar çalıştırılır. Lisans ve paylaşım koşulları repo sahibiyle netleştirilmelidir.
""",
        encoding="utf-8",
        newline="\n",
    )
    review_entries["TESLIM.md"] = handoff
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": "0.3.0",
        "validation_platform": "Windows / Python 3.12.10",
        "hardware_access_during_checks": False,
        "linux_and_physical_acceptance": "pending",
        "remote_ci": "not_run",
        "source_files": [metadata(name, path) for name, path in sorted(source_entries.items())],
        "review_files": [metadata(name, path) for name, path in sorted(review_entries.items())],
        "manifest_and_checksum_file_are_not_listed_in_their_own_contents": True,
        "tests": {key: tests[key] for key in ("tests", "passed", "failures", "errors", "skipped")},
    }
    manifest_path = DESTINATION / "DOSYA-MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    review_entries["DOSYA-MANIFEST.json"] = manifest_path
    internal_checksums = EVIDENCE / "inceleme-arsivi-SHA256SUMS.txt"
    internal_checksums.write_text(
        "".join(f"{digest(path)}  {name}\n" for name, path in sorted(review_entries.items())),
        encoding="utf-8",
        newline="\n",
    )
    review_entries["SHA256SUMS.txt"] = internal_checksums
    write_zip(DESTINATION / "Muvv-0.3.0-kaynak.zip", source_entries)
    write_zip(DESTINATION / "Muvv-0.3.0-inceleme.zip", review_entries)
    for path in (
        wheel,
        ROOT / "Muvv/dist/muvv-0.3.0.tar.gz",
        EVIDENCE / "Muvv.patch",
        EVIDENCE / "Muvv_development_environment.patch",
        ROOT / "GELISTIRME-0.3-RAPORU.md",
        ROOT / "GELISTIRME-0.3-PLANI.md",
    ):
        (DESTINATION / path.name).write_bytes(path.read_bytes())
    deliveries = [metadata(path.name, path) for path in sorted(DESTINATION.iterdir()) if path.is_file()]
    (DESTINATION / "SHA256SUMS.txt").write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in deliveries),
        encoding="utf-8",
        newline="\n",
    )
    result = {
        "successful": True,
        "directory": str(DESTINATION),
        "source_files": len(source_entries),
        "review_zip_entries": len(review_entries),
        "archive_crc_and_file_contents_verified": True,
        "files": deliveries,
    }
    (EVIDENCE / "teslim-dogrulama.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
