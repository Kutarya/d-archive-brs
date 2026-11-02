# Progress

## Yol Haritası (Roadmap)

### Faz 1: The Prototype (Mevcut Durum)
- [x] Proje Analizi ve Dokümantasyon İncelemesi
- [x] Klasör Yapısının Oluşturulması
- [x] Memory Bank Kurulumu
- [x] Python Sanal Ortam (.venv) Kurulumu
- [x] `roming` (Sanal Ortam) ve `requirements.txt`
- [x] BaseMouse ve Driver İskeleti
- [x] Rival 3 Gen 2 DPI, Hz ve Save Profile Desteği
- [x] Basit CLI DPI Testi
- [x] Sürücü Katmanı Thread Safety (Lock Mekanizması)
- [x] Kod Temizliği (Magic Numbers Refactoring)
- [x] Non-Blocking I/O (Asenkron Queue Sistemi)
- [x] Driver Update: `max_fps` Desteği (Manager Hazırlığı) <!-- Added -->

### Faz 2: The UI & Engine
- [/] Animasyon Motoru Entegrasyonu (Vitray)
    - [x] İsimlendirme ve Dokümantasyon
    - [x] Dosya/Klasör Yapısı (Scaffolding)
    - [x] Temel Sınıflar (BaseEffect, Layer)
    - [x] ZoneMap Refactoring (Koordinat Sistemi)
    - [x] Feature: Zone Filtering (Bölgesel Efektler)
    - [x] Feature: Wave Effect (Konum Bazlı Animasyon)
    - [x] Feature: Parameter Control (Hız/Renk Değişimi API)
    - [ ] Effect Registry Refactoring (Sınıf Kaydedici Altyapısı)
        - [x] Dinamik efekt yükleyici (`effect_registry.py`) eklendi (Adım 1).
        - [x] Efekt klasörü statik yüklerden temizlendi (Adım 2).
        - [x] DeviceRunner dinamik yapıya geçirilerek refactor edildi (Adım 3).
        - [x] Sistem başarıyla doğrulandı ve manuel ekleme dönemi kapandı (Adım 4).
    - [ ] Efekt Mantığı (Diğer Efektler)
- [/] Manager Entegrasyonu
    - [x] Device Registry (Cihaz Kataloğu)
    - [x] Device Runner (Thread Yönetimi)
    - [x] Device Manager (Daemon Logic)
    - [x] Manager Tests & Teardown Fix
- [/] CLI ve IPC (Socket) Entegrasyonu
    - [x] IPC ve CLI (Adım 1-4) tamamlandı: UDS dinleme, JSON komut ayrıştırma ve terminal istemcisi (cli.py) başarıyla test edilerek entegre edildi.
    - [x] Donanım Komutları Entegrasyonu (DPI, Polling Rate, Bind Key, Save Profile)
        - [x] 1. Aşama: `DeviceRunner` donanım köprü metotları eklendi.
        - [x] 2. Aşama: `DeviceManager` yönlendirme metotları eklendi.
        - [x] 3. Aşama: `IPCServer` JSON komut ayrıştırıcıları eklendi.
        - [x] 4. Aşama: `CLI` komut parser'ları ve argüman yönlendirmeleri eklendi (`cli.py`).
        - [x] 5. Aşama: Fiziki cihaz (`Rival 3 Gen 2`) üzerinde uçtan uca test ve doğrulama.
    - [x] Modüler CLI & Yetenek Doğrulama (Aşama 2.1 - TAMAMLANDI)
        - [x] Sürücü `CAPABILITIES` verisinin `DeviceManager` ve IPC tarafına aktarılması (Adım 2.1.1).
        - [x] `cli.py info <device_id>` detaylı bilgi komutunun eklenmesi (Adım 2.1.1).
        - [x] Komut Doğrulayıcı (Desteklenmeyen komutlarda çökme yerine açıklayıcı uyarı verme) (Adım 2.1.2).
        - [x] Dinamik efekt bayrakları (`--color`, `--speed`, `--direction`, `--wave-length`) (Adım 2.1.3).



- [ ] Genel Çevre Birimi Refactoring'i (`BaseDevice` -> Keyboard/Headset/Mousepad)
- [ ] Arka Plan Servisi (Systemd Daemon)
- [ ] CustomTkinter Arayüz Tasarımı (GUI - 2. Plan)


### Faz 3: The Input (Riskli Bölge)
- [ ] `evdev` Entegrasyonu (Tuş Dinleme)
- [x] Donanımsal Makro ve Tuş Atama Altyapısı (Rival 3)
- [ ] Windows Porting Araştırması

## Bilinen Sorunlar / Riskler
*   **Device Brick:** Hatalı paket gönderimi cihazı kilitler mi? (Koruma: `try-finally`)
*   **Concurrency:** Kayıt sırasındaki çakışmalar. (Çözüm: `threading.Lock` ile çözüldü)
