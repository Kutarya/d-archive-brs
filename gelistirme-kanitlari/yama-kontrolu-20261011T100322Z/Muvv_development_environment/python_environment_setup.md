# Geliştirme ortamı

Sanal ortam kod deposunun `Muvv/.venv` dizininde tutulur. Bu klasör Git'e eklenmez.

## Linux

```bash
cd Muvv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.2.1
python -m pip install --require-hashes -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m pip install -r requirements-dev.txt
python tools/check.py
```

GUI için dağıtımda Tk bulunmalıdır. Kullanıcı servisi ve udev kurulumu kaynak depodaki README'de açıklanır.

## Windows

```powershell
cd Muvv
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip==26.2.1
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe tools/check.py
.\.venv\Scripts\muvv-gui.exe --demo
```

Windows'ta bu komutlar demo/otomatik doğrulama içindir; gerçek Linux cihaz servisini başlatmaz.

## Bağımlılık değişikliği

Doğrudan sürümleri `pyproject.toml` ve ilgili requirements dosyasında birlikte güncelleyin. Çalışma zamanı hashlerini `tools/lock_requirements.py` ile yenileyin, değişen paketlerin metadata/hashlerini inceleyin ve pip-audit ile testleri çalıştırın. Tüm geliştirme ortamının `pip freeze` çıktısını çalışma zamanı gereksinimi olarak kullanmayın.
