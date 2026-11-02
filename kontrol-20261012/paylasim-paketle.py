"""Create and extract-check the final ZIP using an explicit file list."""

import hashlib
import json
import posixpath
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

ROOT = Path('D:/BRS')
OUT = ROOT / 'kontrol-20261012'
STAGE = OUT / 'paylasim/Muvv-0.4.0-Proje'
DEST = ROOT / 'teslim/Muvv-0.4.0-20261012-kontrol'
EXTRACT = OUT / 'zip-acilim/Paylasim Denemesi'


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


tests = read_json('test-sonuclari.json')
clean = read_json('temiz-kurulum.json')
source = read_json('kaynak-kontrolu.json')
simulation = read_json('sanal-senaryolar.json')
check(tests['successful'] and clean['successful'] and source['successful'], 'Checks failed')
check(simulation['successful'] and not simulation['remaining_workers'], 'Simulation failed')
check(not DEST.exists() and not EXTRACT.exists(), 'Delivery or extraction path already exists')

readme_path = STAGE / 'BASLANGIC.md'
readme = readme_path.read_text(encoding='utf-8')
readme = readme.replace('bu teslim Python 3.12.10 ile sınandı.', 'otomatik testler Python 3.12.10, temiz demo kurulumu Python 3.14.5 ile sınandı.')
readme_path.write_text(readme, encoding='utf-8', newline='\n')

report = f'''# Muvv 0.4.0 çalışma kontrolü

12 Ekim 2026. Uygulama kaynakları son 0.4.0 teslimiyle birebir eşleşti; yeni uygulama kodu değişikliği gerekmedi.

## Sonuç

Windows'ta demo arayüzü açıldı ve çalıştı. RGB/efekt, DPI, tuş ve profil akışları otomatik testlerle sınandı. Gerçek fare servisi Linux'a özgüdür. Linux, udev/systemd, fiziksel Rival 3 Gen 2 ve firmware kalıcılığı bu kontrolde doğrulanmadı.

| Kontrol | Sonuç |
|---|---|
| Otomatik testler | {tests['tests']} test: {tests['passed']} geçti, {len(tests['skipped'])} Linux/POSIX testi atlandı, {tests['failures']} başarısızlık, {tests['errors']} hata. |
| Gerçek Tk arayüzü | Testlerin içinde 33 GUI senaryosu; ayrıca dört sekmeli demo kullanım kontrolü ve altı güncel görüntü. |
| Sanal mesaj ve USB akışları | 500 parçalı mesaj, 400 eşzamanlı işlem / 1.200 rapor; rapor karışması yok. |
| Yeniden bağlantı ve profiller | 50 yeni oturum, 50 eski komutun engellenmesi, 50 dosya aktarımı, 100 yeniden adlandırma. |
| USB kesilmesi | Dört hata noktası; yanlış başarı ve hatadan sonra ek yazım yok. |
| Kod denetimi | Ruff denetimi ve 57 dosyanın biçim denetimi geçti. |
| Söz dizimi | 64 Python dosyası 3.10 söz dizimiyle ayrıştırıldı; bu Python 3.10 çalışma zamanı testi değildir. |
| Temiz kurulum | Windows demo başlatıcısı ayrı sanal ortamda hashli bağımlılıkları ve wheel'i kurdu; pip check ve sürüm komutu geçti. |
| Kurulu uygulama | GUI'nin normal demo giriş noktası ve DPI/RGB/efekt akışları Python 3.14.5 ile çalıştı; modüller site-packages içinden yüklendi. |
| Kapanış | Arayüz callback hatası ve kalan Muvv işçisi yok. |
| Kaynak/paket eşleşmesi | 83 uygulama + 12 geliştirme dosyası; wheel içindeki 34 modül kaynakla aynı. |
| Önceki teslimler | 50 eski teslim dosyasının SHA-256 değeri korundu. |

## Son güncellemelerin kontrolü

0.3'e göre 19 dosyada değişiklik var. Cihaz listesi ve bağlantı oturumu aynı anı temsil ediyor; bağlantı yenilenince eski oturumun yazımı engelleniyor. Kapanış çok raporlu USB işlemindeki kalan raporları durduruyor. CLI ve GUI profil sayfalarını ortak biçimde doğruluyor; katalog değişimi ve bozuk sayfa yanlış başarı oluşturmuyor. Profil hatası cihaz kontrollerini kapatmıyor; tarama ve erişim nedenleri ekranda gösteriliyor. Bu davranışların regresyon testleri mevcut tam koşuda geçti.

## Paylaşım

[Başlangıç ve kurulum](BASLANGIC.md). `DEMO-BASLAT.cmd` Windows demosunu açar; ilk kurulum için Python 3.10+ ve internet gerekir. Başlatıcı yalnızca çıkarılan proje klasörünün `.venv` ortamını kullanır. ZIP kaynak teslimidir; bağımsız Windows EXE içermez.

Güncel kanıtlar: [test sonuçları](kontrol-20261012/test-sonuclari.json), [test kaydı](kontrol-20261012/test-kaydi.log), [sanal senaryolar](kontrol-20261012/sanal-senaryolar.json), [temiz kurulum](kontrol-20261012/temiz-kurulum.json), [kaynak kontrolü](kontrol-20261012/kaynak-kontrolu.json).

Güncel demo görüntüsü:

![Muvv demo arayüzü](kontrol-20261012/arayuz/rgb.png)

`gelistirme-0.4` ve `GELISTIRME-0.4-RAPORU.md` 11 Ekim'in tarihsel geliştirme kanıtlarıdır. Yeni kayıtlar `kontrol-20261012` altındadır. Fiziksel HID bu testlerde açılmadı.
'''
(STAGE / 'KONTROL-2026-10-12.md').write_text(report, encoding='utf-8', newline='\n')

previous = ROOT / 'teslim/Muvv-0.4.0-20261011/Muvv-0.4.0-inceleme.zip'
with zipfile.ZipFile(previous) as archive:
    entries = {info.filename: STAGE / info.filename for info in archive.infolist() if not info.is_dir()}
entries.update({name: STAGE / name for name in ('BASLANGIC.md', 'KONTROL-2026-10-12.md', 'DEMO-BASLAT.cmd')})
fresh_names = (
    'test-sonuclari.json', 'test-kaydi.log', 'sanal-senaryolar.json', 'sanal-senaryolar.log',
    'ruff-check.log', 'ruff-format.log', 'arayuz-akis.json', 'arayuz-smoke.json',
    'kaynak-kontrolu.json', 'kaynak-manifest.json', 'ortam-tanisi.json',
    'temiz-kurulum.json', 'temiz-kurulum.log', 'temiz-arayuz.log',
)
for name in fresh_names:
    destination = STAGE / 'kontrol-20261012' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT / name, destination)
    entries[f'kontrol-20261012/{name}'] = destination
for path in sorted((OUT / 'arayuz').glob('*.png')):
    destination = STAGE / 'kontrol-20261012/arayuz' / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, destination)
    entries[f'kontrol-20261012/arayuz/{path.name}'] = destination

for name, path in entries.items():
    check(path.is_file() and not path.is_symlink(), f'Invalid payload: {name}')
    check(path.resolve().is_relative_to(STAGE.resolve()), f'Path outside staging: {name}')
    check(not {'.git', '.venv', '__pycache__', '.env', 'Note.md'}.intersection(PurePosixPath(name).parts), name)

manifest = [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())} for name, path in sorted(entries.items())]
(STAGE / 'PROJE-MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(STAGE / 'PROJE-SHA256SUMS.txt').write_text(''.join(f"{entry['sha256']}  {entry['path']}\n" for entry in manifest), encoding='utf-8')
entries.update({name: STAGE / name for name in ('PROJE-MANIFEST.json', 'PROJE-SHA256SUMS.txt')})

broken = []
for name, path in entries.items():
    if not name.endswith('.md'):
        continue
    for target in re.findall(r'\[[^\]\n]*\]\(([^\)\n]+)\)', path.read_text(encoding='utf-8-sig')):
        target = unquote(target.strip('<>')).split('#', 1)[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
        if resolved not in entries and not any(entry.startswith(resolved.rstrip('/') + '/') for entry in entries):
            broken.append({'file': name, 'target': target})
check(not broken, f'Broken local Markdown links: {broken}')

DEST.mkdir(parents=True)
package = DEST / 'Muvv-0.4.0-Proje-20261012.zip'
prefix = 'Muvv-0.4.0-Proje/'
with zipfile.ZipFile(package, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, path in sorted(entries.items()):
        archive.write(path, prefix + name)
with zipfile.ZipFile(package) as archive:
    check(archive.testzip() is None, 'Final ZIP failed CRC validation')
    check(len(archive.namelist()) == len(entries) == len(set(archive.namelist())), 'Archive file count mismatch')
    for name, path in entries.items():
        data = archive.read(prefix + name)
        check(data == path.read_bytes(), f'Archive bytes differ: {name}')
        target = EXTRACT / prefix / name
        check(target.resolve().is_relative_to(EXTRACT.resolve()), 'Unsafe extraction target')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for source_entry in read_json('kaynak-manifest.json'):
        check(sha(archive.read(prefix + source_entry['path'])) == source_entry['sha256'], 'Source changed during packaging')

checksum = sha(package.read_bytes())
(DEST / 'SHA256SUMS.txt').write_text(f'{checksum}  {package.name}\n', encoding='utf-8')
result = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'successful': True,
    'zip': str(package),
    'zip_bytes': package.stat().st_size,
    'sha256': checksum,
    'files': len(entries),
    'source_files_verified': len(read_json('kaynak-manifest.json')),
    'crc_and_all_file_bytes_verified': True,
    'extracted_to': str(EXTRACT / 'Muvv-0.4.0-Proje'),
    'broken_local_markdown_links': broken,
    'virtual_environments_and_personal_data_in_archive': False,
}
(DEST / 'ZIP-DOGRULAMA.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(STAGE / 'KONTROL-2026-10-12.md', DEST / 'KONTROL-2026-10-12.md')
print(json.dumps(result, ensure_ascii=False, indent=2))
