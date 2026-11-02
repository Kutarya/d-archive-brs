# System Patterns

## Mimari Desenler

### Katmanlı Mimari (Layered Architecture)
Sistem 4 ana katmana ayrılmıştır:
1.  **Driver (Sürücü):** Donanım protokolünü yönetir (Packet level).
2.  **Artist (Animasyon):** Işık/Renk hesaplamalarını yapar (Donanım bağımsız).
3.  **Manager (Yönetici):** Koordinasyon ve yaşam döngüsü yönetimi.(Donanımdan Bağımsız)
4.  **GUI (Arayüz):** Kullanıcı etkileşimi.

### Sürücü Deseni (Driver Pattern)
*   **Soyutlama:** `BaseMouse` abstract sınıfı temel arayüzü (`set_color`, `set_dpi` vb.) tanımlar.
*   **Uygulama:** Her cihaz (örn: `Rival3.py`) bu sınıfı miras alır ve kendi protokolünü implemente eder.
*   **Sanal Durum:** LED durumu RAM'de tutulur, `flush()` ile cihaza gönderilir.

### Animasyon Deseni (The Artist)
*   **Vitray (Stained Glass) Mantığı:**
    *   **Map:** Renk haritası (sabit).
    *   **Mask:** Parlaklık maskesi (hareketli).
    *   Sonuç = Map * Mask (Additive Blending).
*   **Decoupling:** Animasyon motoru hangi fareyi sürdüğünü bilmez.

### Yönetici ve İletişim
*   **Daemon:** Arka planda çalışan servis.
*   **IPC:** GUI ile Daemon arasında Socket veya Named Pipe iletişimi.

## Kodlama Standartları
*   **Python:** Type hints kullanılmalı.
*   **Hata Yönetimi:** USB iletişiminde `try-finally` blokları ile kaynak temizliği (disconnect, reset_state) esastır.
*   **Eşzamanlılık:** Thread-safe iletişim için `queue` kullanımı.
