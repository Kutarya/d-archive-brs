# Tech Context

## Teknoloji Yığını (Tech Stack)

### Core & Backend
*   **Dil:** Python 3.10+
*   **Donanım Erişimi:** `hidapi` (Cython/C types) - USB HID packet sending/receiving.
*   **Eşzamanlılık:** `threading` + `queue` (Thread-Safe USB İletişimi).
*   **Veri Yapıları & Hesaplama:**
    *   `NumPy`: Vektörel işlemler, RGB matris yönetimi.
    *   `Numba`: (İleri Safha) JIT derleme ile CPU optimizasyonu.

### Frontend (GUI)
*   **Kütüphane:** `CustomTkinter`
*   **Özellikler:** Modern, DPI-aware arayüz.

### Altyapı & Ortam
*   **OS:** Linux
*   **Yetkilendirme:** `udev` kuralları ile root-less erişim.
*   **Konfigürasyon:** JSON formatında kullanıcı ayarları (`~/.config/ProjectName/` altında).
*   **Sanal Ortam:** Python `venv` (git tarafından yok sayılmalı).

## Bağımlılıklar
*   `hidapi`
*   `customtkinter`
*   `numpy`
*   `numba` (opsiyonel/ileri faz)
