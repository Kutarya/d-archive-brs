# Teknik ortam

- Python 3.10+; gerçek cihaz servisi Linux.
- HID erişimi: `hidapi==0.15.0`.
- Masaüstü: `customtkinter==6.0.0` ve dağıtımın Tk paketi.
- Eşzamanlılık: `threading`, sınırlı `queue.Queue`, `concurrent.futures.Future`.
- İletişim: kullanıcıya özel Unix stream socket, uzunluk başlığı ve UTF-8 JSON.
- Profil: `$XDG_CONFIG_HOME/muvv/profiles` veya `~/.config/muvv/profiles`.
- RGB hesaplama: standart kütüphane `math` / `colorsys`; NumPy ve Numba çalışma zamanı bağımlılığı değil.
- Paketleme: `pyproject.toml`; `muvv`, `muvvd`, `muvv-gui` girişleri.
- Kontroller: unittest, Ruff, coverage ve pip-audit.

Çalışma zamanı/GUI hash kilidi kaynak depodaki `requirements-lock.txt` dosyasında. Geliştirme araçları `requirements-dev.txt` ve dev extra altında ayrıdır. Sanal ortam, test önbelleği ve derleme çıktısı Git'e girmez.

Windows yerel ortamında GUI demosu kullanılabilir. Linux `SO_PEERCRED`, POSIX izinleri ve hidraw davranışı Windows demosunda doğrulanmaz.
