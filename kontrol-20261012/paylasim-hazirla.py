"""Prepare a shareable project copy without changing previous releases."""

import json
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path('D:/BRS')
OUT = ROOT / 'kontrol-20261012'
STAGE = OUT / 'paylasim/Muvv-0.4.0-Proje'


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


tests = json.loads((OUT / 'test-sonuclari.json').read_text(encoding='utf-8-sig'))
source = json.loads((OUT / 'kaynak-kontrolu.json').read_text(encoding='utf-8-sig'))
gui = json.loads((OUT / 'arayuz-smoke.json').read_text(encoding='utf-8-sig'))
simulation = json.loads((OUT / 'sanal-senaryolar.json').read_text(encoding='utf-8-sig'))
check(tests['successful'] and not tests['errors'] and not tests['failures'], 'Tests failed')
check(source['successful'] and gui['status'] == 'passed' and not gui['callback_errors'], 'Source or GUI failed')
check(simulation['successful'] and not simulation['remaining_workers'], 'Simulation failed')
check(not STAGE.exists(), 'Staging path already exists')
STAGE.mkdir(parents=True)

previous_zip = ROOT / 'teslim/Muvv-0.4.0-20261011/Muvv-0.4.0-inceleme.zip'
with zipfile.ZipFile(previous_zip) as archive:
    check(archive.testzip() is None, 'Previous review ZIP is corrupt')
    for info in archive.infolist():
        name = PurePosixPath(info.filename)
        check(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename, info.filename)
        check(not stat.S_ISLNK(info.external_attr >> 16), 'Symlink in previous archive')
        check(not {'.git', '.venv', '__pycache__', '.env', 'Note.md'}.intersection(name.parts), info.filename)
        if info.is_dir():
            continue
        destination = STAGE.joinpath(*name.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read(info))

launcher = (OUT / 'DEMO-BASLAT.cmd').read_text(encoding='utf-8').replace('\r\n', '\n')
(STAGE / 'DEMO-BASLAT.cmd').write_bytes(launcher.replace('\n', '\r\n').encode('ascii'))

readme = r'''# Muvv 0.4.0 paylaşılabilir proje

12 Ekim 2026 kontrolü. ZIP; uygulama kaynaklarını, testleri, geliştirme notlarını, kurulum paketlerini ve kontrol kayıtlarını birlikte içerir.

## Windows'ta demoyu açma

1. ZIP'in tamamını bir klasöre çıkarın. ZIP'in içinden doğrudan çalıştırmayın.
2. Python 3.10 veya üzeri kurulu olmalıdır; bu teslim Python 3.12.10 ile sınandı.
3. `DEMO-BASLAT.cmd` dosyasına çift tıklayın.

İlk çalıştırma internet üzerinden sabit sürüm ve SHA-256 ile doğrulanan bağımlılıkları yalnızca bu proje klasöründeki `.venv` ortamına kurar. Sistem Python paketlerini değiştirmez. Sonraki açılışlar kurulu ortamı kullanır. Bu dosya bir demo başlatıcısıdır; bağımsız EXE değildir.

Demo DPI, RGB, tuş ataması ve profil ekranlarını bellek içi cihazla çalıştırır. Fiziksel fareye veri göndermez. Gerçek fare servisi bu sürümde Linux içindir.

Terminalden yalnızca kurulum kontrolü için:

```powershell
.\DEMO-BASLAT.cmd --check
```

## Linux'ta gerçek cihaz kullanımı

Python 3.10+, Tk ve desteklenen SteelSeries Rival 3 Gen 2 Wired gerekir. Normal kullanıcı hesabıyla kurulum:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r Muvv/requirements-lock.txt
.venv/bin/python -m pip install --no-deps paketler/muvv-0.4.0-py3-none-any.whl
.venv/bin/muvv-gui --demo
```

Udev izinleri ve servis kurulumu [uygulama README'sinde](Muvv/README.md), fiziksel cihaz kabulü [donanım kontrol listesinde](Muvv/docs/HARDWARE-ACCEPTANCE.md) anlatılır. Gerçek kullanımda `muvvd` servisi ve `muvv-gui` arayüzü birlikte çalışır. Linux ve fiziksel cihaz kabulü bu Windows kontrolünde yapılmadı.

## Proje içeriği

- `Muvv/`: uygulama kodu, dört sekmeli arayüz, CLI, Linux servisi, testler ve teknik belgeler.
- `Muvv_development_environment/`: geliştirme ortamı, protokol ve mimari notları.
- `paketler/`: kaynakla eşleşen 0.4.0 wheel ve kaynak dağıtımı.
- `kontrol-20261012/`: güncel test sonuçları, temiz kurulum kontrolü ve ekran görüntüleri.
- `GELISTIRME-0.4-RAPORU.md` ve `gelistirme-0.4/`: 11 Ekim geliştirme raporu ve o tarihin kanıtları.
- `PROJE-MANIFEST.json` ve `PROJE-SHA256SUMS.txt`: paylaşım dosyalarının boyut ve SHA-256 kayıtları.

Güncel sonuç için [12 Ekim kontrol raporunu](KONTROL-2026-10-12.md), son değişiklikler için [CHANGELOG'u](Muvv/CHANGELOG.md) açın. Uygulama kaynakları 11 Ekim 0.4.0 teslimiyle birebir aynıdır; bu kontrol yeni bir uygulama sürümü eklemez. Git iç dosyaları, sanal ortamlar, önbellekler ve kişisel profiller paylaşım ZIP'ine alınmamıştır.

## Kaynaktan testleri tekrarlama

Kurulumdan sonra Windows'ta:

```powershell
cd Muvv
..\.venv\Scripts\python.exe tools/check.py --json test-results.json
..\.venv\Scripts\python.exe tools/simulation_check.py --cycles 50 --json simulation-results.json
..\.venv\Scripts\python.exe tools/gui_smoke.py
```

Linux'ta aynı komutlarda Python yolu `../.venv/bin/python` olur. `gui_smoke.py --snapshots` ek olarak Pillow gerektirir; normal demo ve GUI testleri için Pillow gerekmez. Tarihsel `gelistirme-0.4` içindeki yerel paketleme yardımcıları eski Windows çalışma alanına bağlıdır; taşınabilir test girişleri `Muvv/tools` altındadır.
'''
(STAGE / 'BASLANGIC.md').write_text(readme, encoding='utf-8', newline='\n')
shutil.copyfile(STAGE / 'Muvv/tools/gui_smoke.py', OUT / 'temiz-gui-kontrolu.py')
smoke = (OUT / 'temiz-gui-kontrolu.py').read_text(encoding='utf-8')
smoke = smoke.replace('sys.path.insert(0, str(ROOT))', '# Use installed modules only; do not import source from Muvv/.')
(OUT / 'temiz-gui-kontrolu.py').write_text(smoke, encoding='utf-8', newline='\n')
print(json.dumps({'stage': str(STAGE), 'tests_passed': tests['passed'], 'skipped': len(tests['skipped']), 'status': 'ready_for_clean_install'}, ensure_ascii=False))
