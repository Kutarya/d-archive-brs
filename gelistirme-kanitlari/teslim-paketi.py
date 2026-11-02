"""Create immutable source/review ZIPs from an explicit local source allowlist."""

import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path("D:/BRS")
EVIDENCE = ROOT / "gelistirme-kanitlari"
DESTINATION = ROOT / "teslim/Muvv-0.1.0-20261011"
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


def main():
    tests = json_file("test-sonuclari.json")
    package = json_file("paket-dogrulama.json")
    source_check = json_file("kaynak-dogrulama.json")
    patches = json_file("yama-dogrulama.json")
    gui = json_file("arayuz-smoke.json")
    assert tests["successful"] and tests["passed"] == 78 and len(tests["skipped"]) == 11
    assert package["successful"] and source_check["successful"] and patches["successful"]
    assert gui["status"] == "passed" and gui["callback_errors"] == []
    wheel = ROOT / "Muvv/dist/muvv-0.1.0-py3-none-any.whl"
    assert digest(wheel) == package["wheel_sha256"]
    for entry in patches["source_reconstructed_from_zip_and_patch"]:
        assert entry["patch_sha256"] == digest(EVIDENCE / f"{entry['repository']}.patch")

    source_entries = {}
    for name in ("Muvv", "Muvv_development_environment"):
        repository = ROOT / name
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=repository, capture_output=True, check=True
        )
        filenames = sorted({value.decode("utf-8") for value in listing.stdout.split(b"\0") if value})
        for filename in filenames:
            path = repository / filename
            assert path.resolve().is_relative_to(repository.resolve()) and not path.is_symlink(), filename
            assert path.suffix in SUFFIXES or path.name in HIDDEN_NAMES, filename
            source_entries[f"{name}/{filename}"] = path
    assert len(source_entries) == 84
    review_entries = dict(source_entries)
    for name in ("GELISTIRME-RAPORU.md", "GELISTIRME-PLANI.md"):
        review_entries[name] = ROOT / name
    for name in ("MUVV-INCELEME-RAPORU.md", "DOSYA-HARITASI.md"):
        review_entries[f"inceleme/{name}"] = ROOT / "inceleme" / name
    for name in ("arsiv-envanteri.json", "offline-inceleme-sonuclari.json"):
        review_entries[f"inceleme/kanitlar/{name}"] = ROOT / "inceleme/kanitlar" / name
    evidence_names = (
        "test-sonuclari.json", "test-kaydi.log", "kapsama.json", "paket-dogrulama.json",
        "kaynak-dogrulama.json", "yama-dogrulama.json", "arayuz-smoke.json",
        "bagimlilik-denetimi.json", "gelistirme-bagimlilik-denetimi.json",
        "gelistirme-bagimlilik-denetimi-son.json", "paket-olusturma.log",
        "paket-dogrulama.py", "kaynak-dogrulama.py", "yama-dogrulama.py", "teslim-paketi.py",
        "Muvv.patch", "Muvv_development_environment.patch",
    )
    for name in evidence_names:
        review_entries[f"gelistirme-kanitlari/{name}"] = EVIDENCE / name
    for name in ("rgb.png", "dpi.png", "buttons.png", "profiles.png"):
        review_entries[f"gelistirme-kanitlari/arayuz/{name}"] = EVIDENCE / "arayuz" / name
    for name in ("muvv-0.1.0-py3-none-any.whl", "muvv-0.1.0.tar.gz"):
        review_entries[f"paketler/{name}"] = ROOT / "Muvv/dist" / name

    DESTINATION.mkdir(parents=True, exist_ok=False)
    handoff = DESTINATION / "TESLIM.md"
    handoff.write_text(
        """# Muvv 0.1.0 yerel teslimi

11 Ekim 2026. Kaynak ZIP'inden hazırlanan özel geliştirme kopyası.

- `Muvv-0.1.0-kaynak.zip`: iki güncel kaynak deposu, 84 dosya.
- `Muvv-0.1.0-inceleme.zip`: aynı kaynaklar, raporlar, test kanıtları, arayüz görüntüleri, yamalar ve kurulum paketleri.
- Wheel ve tar.gz: Python kurulumu ve kaynak dağıtımı. Kaynak README'sindeki hashli kurulum yolu önerilir.
- İki `.patch`: kendi depolarının başlangıç ZIP'ine göre değişiklikler.
- `SHA256SUMS.txt`: bu klasördeki teslim dosyalarının SHA-256 değerleri.

İnceleme ZIP'ini ayrı bir klasöre açıp `GELISTIRME-RAPORU.md` ile başlayın. Uygulama komutları `Muvv/README.md` içindedir. Demo `muvv-gui --demo` ile açılır; USB cihazı kullanmaz.

Yerel test sonucu: 89 toplam, 78 geçti, Linux gerektiren 11 atlandı; hata/başarısızlık yok. Linux IPC/izin, udev/systemd ve fiziksel fare kabulü bekliyor. GitHub CI çalıştırılmadı ve yayın yapılmadı.

Yamayı ilgili özel repo için ayrı inceleme dalında kontrol edin. Başlangıçtan sonra repo değiştiyse çakışmaları ayrıca çözün; `--reject` veya zorla uygulama ile hatayı geçiştirmeyin. Windows'ta satır sonu dönüşümünü önleyen kontrol örneği:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna ayrı uygulanır. İki yama başlangıçların ayrı kopyalarına uygulanıp 84 güncel dosyayla birebir karşılaştırıldı. ZIP'ler Git geçmişi içermez. Kaynaklarda yayın lisansı belirlenmediğinden paylaşım/yayın koşullarını repo sahibi netleştirmelidir.

İnceleme ZIP'indeki `DOSYA-MANIFEST.json` paketlenen dosyaları listeler. ZIP içindeki `SHA256SUMS.txt` yalnızca ZIP içindeki dosyaları, dış klasördeki aynı isimli dosya ise dış teslim dosyalarını doğrular; her biri kendisini kapsam dışı tutar.

`gelistirme-kanitlari/gelistirme-bagimlilik-denetimi.json` ilk pip taramasıdır. Son durum `gelistirme-bagimlilik-denetimi-son.json` içindedir. Test kaydındaki root/başlangıç hata mesajları beklenen negatif senaryolardır; son toplamda başarısız test yoktur.

Kanıt yardımcıları bu Windows çalışma klasörüne aittir. Taşınabilir proje testleri `Muvv/tools/check.py` ve `Muvv/test/` içindedir. Orijinal ZIP'ler ve başlangıç kopyaları yerel inceleme alanında korunmuştur.
""", encoding="utf-8"
    )
    review_entries["TESLIM.md"] = handoff
    for target in re.findall(r"\[[^\]\n]*\]\(([^\)\n]+)\)", (ROOT / "GELISTIRME-RAPORU.md").read_text(encoding="utf-8")):
        target = unquote(target.strip("<>").split("#", 1)[0])
        assert target in review_entries or any(name.startswith(target.rstrip("/") + "/") for name in review_entries), target
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
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
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_entries["DOSYA-MANIFEST.json"] = manifest_path
    internal_checksums = EVIDENCE / "inceleme-arsivi-SHA256SUMS.txt"
    internal_checksums.write_text(
        "".join(f"{digest(path)}  {name}\n" for name, path in sorted(review_entries.items())), encoding="utf-8"
    )
    review_entries["SHA256SUMS.txt"] = internal_checksums
    source_zip = DESTINATION / "Muvv-0.1.0-kaynak.zip"
    review_zip = DESTINATION / "Muvv-0.1.0-inceleme.zip"
    write_zip(source_zip, source_entries)
    write_zip(review_zip, review_entries)
    for path in (
        wheel, ROOT / "Muvv/dist/muvv-0.1.0.tar.gz",
        EVIDENCE / "Muvv.patch", EVIDENCE / "Muvv_development_environment.patch",
        ROOT / "GELISTIRME-RAPORU.md", ROOT / "GELISTIRME-PLANI.md",
    ):
        (DESTINATION / path.name).write_bytes(path.read_bytes())
    deliveries = [metadata(path.name, path) for path in sorted(DESTINATION.iterdir()) if path.is_file()]
    (DESTINATION / "SHA256SUMS.txt").write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in deliveries), encoding="utf-8"
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
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
