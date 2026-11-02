# Muvv 0.4.0 paylaşılabilir proje

12 Ekim 2026 kontrolü. ZIP; uygulama kaynaklarını, testleri, geliştirme notlarını, kurulum paketlerini ve kontrol kayıtlarını birlikte içerir.

## Windows'ta demoyu açma

1. ZIP'in tamamını bir klasöre çıkarın. ZIP'in içinden doğrudan çalıştırmayın.
2. Python 3.10 veya üzeri kurulu olmalıdır; otomatik testler Python 3.12.10, temiz demo kurulumu Python 3.14.5 ile sınandı.
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
