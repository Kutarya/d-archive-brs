# Muvv dosya haritası

**11 Ekim 2026 — iki ZIP'teki 45 dosyanın tamamı.**

[Ana inceleme ve geliştirme raporu](MUVV-INCELEME-RAPORU.md)

Bu tablo dosyaların görevini ve dikkat edilmesi gereken noktaları özetler. Satır sayıları boş satırlar ve yorumlar dahil metin satırlarıdır. Kaynaklar değiştirilmedi.

## Muvv-main — 34 dosya

| Dosya | Satır | Görevi | Dikkat |
|---|---:|---|---|
| .gitignore (`inceleme/kaynak/Muvv-main/.gitignore`) | 49 | Python ortamı, cache, build ve IDE kalıntılarını dışlar. | Sır dosyası politikası ayrıca tanımlanmalı; ignore geçmişi temizlemez. |
| animations/effect_registry.py (`inceleme/kaynak/Muvv-main/animations/effect_registry.py`) | 75 | Effect dizininden BaseEffect sınıflarını isimleriyle kaydeder; Effect son ekini kısaltabilir. | StaticColor için static alias üretmiyor; import güvenli eklenti sınırına alınmalı. |
| animations/effects/__init__.py (`inceleme/kaynak/Muvv-main/animations/effects/__init__.py`) | 3 | Efekt paketini ve dinamik registry yaklaşımını açıklayan paket dosyası. | Doğrudan efekt ithali içermiyor. |
| animations/effects/base_effect.py (`inceleme/kaynak/Muvv-main/animations/effects/base_effect.py`) | 67 | BaseEffect: zaman, speed, reset, apply soyut metodu ve genel parametre güncellemesi. | hasattr + setattr yöntem/özel alanları değiştirir; izinli parametre şeması gerekli. |
| animations/effects/breathing.py (`inceleme/kaynak/Muvv-main/animations/effects/breathing.py`) | 49 | Sinüsle tek rengin parlaklığını değiştirir; tüm LED'ler için renk üretir. | RGB ve speed girdileri doğrulanmalı; duvar saati yerine monoton zaman değerlendirilmeli. |
| animations/effects/static_color.py (`inceleme/kaynak/Muvv-main/animations/effects/static_color.py`) | 24 | Sabit RGB rengi tüm LED'lere uygular; kurucuda color zorunlu. | set-color kullanımı çalışıyor; generic parametresiz factory ile kurulamıyor. |
| animations/effects/wave.py (`inceleme/kaynak/Muvv-main/animations/effects/wave.py`) | 62 | LED x/y konumuna göre yönlü sinüs dalgası üretir. | Speed iki kez çarpılıyor; update_parameters kurucu wave_length sınırını atlayabiliyor. |
| animations/layer.py (`inceleme/kaynak/Muvv-main/animations/layer.py`) | 116 | Efekt, opacity, enable, hedef bölgeler ve normal/add/multiply harmanlama. | Çıktı kanalları 0–255'e kırpılıyor; bozuk tip/NaN hataları üst katmanda engellenmeli. |
| animations/maps.py (`inceleme/kaynak/Muvv-main/animations/maps.py`) | 55 | ZoneMap: bölge isimleri, indeksler ve normalize fiziksel LED koordinatları. | Donanımdan bağımsız yerleşim iyi; yeni cihaz girdileri ayrıca doğrulanmalı. |
| animations/vitray.py (`inceleme/kaynak/Muvv-main/animations/vitray.py`) | 59 | Layer yığınını siyah arka plan üzerinde işler; nihai RGB kareyi üretir. | Layer listesi render ve IPC arasında paylaşılıyor; atomik snapshot yaklaşımı gerekli. |
| cli.py (`inceleme/kaynak/Muvv-main/cli.py`) | 279 | send_command, print_response, renk ayrıştırma, argüman normalizasyonu ve argparse komut menüsü. | Sabit soket, tek recv, timeout/exit code eksikleri; static komutu registry ile uyuşmuyor. |
| docs/SteelSeries/Rival 3 Gen 2/tr/DPI dökümantasyonu.md (`inceleme/kaynak/Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/DPI dökümantasyonu.md`) | 188 | DPI/polling/kayıt paket yapıları, TrueMove Core tablosu ve HID örneği. | Protokol belgesi; fiziksel doğrulama kaydı değil. Örnekleri doğrudan çalıştırma. |
| docs/SteelSeries/Rival 3 Gen 2/tr/Renk dökümantasyonu.md (`inceleme/kaynak/Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/Renk dökümantasyonu.md`) | 128 | Üç LED bölgesi, maskeler ve RGB paket örneği. | Örnek yalnız write yapmasına rağmen kaydedildi mesajı veriyor; kalıcılık ayrımı düzeltilmeli. |
| docs/SteelSeries/Rival 3 Gen 2/tr/Tuş Atama Dökümanı.md (`inceleme/kaynak/Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/Tuş Atama Dökümanı.md`) | 145 | Buton byte adresleri, HID key mode, kayıt paketi ve sol tık/scroll koruma notları. | Markdown kod bloklarında kapanış eksikleri var; gerçek kurtarma ve garanti tanımlı değil. |
| drivers/base_mouse.py (`inceleme/kaynak/Muvv-main/drivers/base_mouse.py`) | 129 | BaseMouse soyut connect/disconnect/reconnect/color/DPI/save/flush API'si; FIFO USB işçisi. | Sınırsız kuyruk, çıkışsız worker, süre sınırı olmayan join; lock tanımlı ama kullanılmıyor. |
| drivers/steelseries/__init__.py (`inceleme/kaynak/Muvv-main/drivers/steelseries/__init__.py`) | 0 | SteelSeries sürücülerinin boş paket işaretçisi. | İşlevsel kod içermiyor. |
| drivers/steelseries/rival3_gen2.py (`inceleme/kaynak/Muvv-main/drivers/steelseries/rival3_gen2.py`) | 440 | Tek somut sürücü: VID/PID/interface, DPI/polling/buton/RGB paketleri, kayıt ve ZoneMap. | Tuş durumunda ret sonrası rollback yok; kalıcı kayıt otomatik; gerçek ayar okuma ve yazım sonucu yok. |
| managers/device_manager.py (`inceleme/kaynak/Muvv-main/managers/device_manager.py`) | 302 | Daemon koordinasyonu, 2 saniyelik HID tarama, runner yaşam döngüsü, cihaz çözümleme ve komut yönlendirme. | Sözlük kilitsiz; başarısız bağlantı runner'ı listede kalır; belirsiz isim ilk eşleşmeyi seçer. |
| managers/device_registry.py (`inceleme/kaynak/Muvv-main/managers/device_registry.py`) | 75 | Driver dizinini tarar, BaseMouse alt sınıflarını VID/PID kataloğuna ekler. | Import güvenilen kod çalıştırır; çakışma, yükleme sırası ve dağıtım izinleri yönetilmeli. |
| managers/device_runner.py (`inceleme/kaynak/Muvv-main/managers/device_runner.py`) | 277 | Tek cihazın bağlantı/render thread'i, Vitray kurulumu ve donanım köprüleri. | Eski efekt önce silinir; static factory hatalı; driver hatası/ret sonucu kaybolabilir. |
| managers/ipc_server.py (`inceleme/kaynak/Muvv-main/managers/ipc_server.py`) | 250 | Unix socket sunucusu; bağlantı thread'leri, JSON komut ayrıştırma, manager çağrısı. | Erişim politikası, timeout, işçi sınırı, framing ve katı şema eksik; JSON iki kez ayrıştırılıyor. |
| managers/validator.py (`inceleme/kaynak/Muvv-main/managers/validator.py`) | 33 | DPI kademe ve polling listesi doğrulama; basit buton metni kontrolü. | Capability yokken kabul; buton doğrulaması yönlendirme yolunda kullanılmıyor. |
| requirements.txt (`inceleme/kaynak/Muvv-main/requirements.txt`) | 3 | hidapi, customtkinter, numpy bağımlılık listesi. | Sürüm/hash yok; GUI ve NumPy henüz kodda kullanılmıyor. |
| schemas.py (`inceleme/kaynak/Muvv-main/schemas.py`) | 32 | DPI stage/range, RGB ve mouse capability TypedDict sözleşmeleri. | Statik tip tanımı; çalışma zamanı doğrulaması değil. Optional alanlar uygulanmalı. |
| test/hardware/steelseries/rival3_gen2/test_buttons.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_buttons.py`) | 55 | Button5'i A'ya atar, kullanıcı doğrulaması ister ve varsayılan forward'a döner. | Manuel ve kalıcı cihaz ayarı değiştirir; çalıştırılmadı. Önceki özel eşlemeyi yedeklemiyor. |
| test/hardware/steelseries/rival3_gen2/test_color.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_color.py`) | 84 | Gerçek farede renk döngüsü ve bölgesel RGB denemesi; sonunda LED'leri kapatır. | Donanım işlevi; çalıştırılmadı. Hatalar pytest keşfinde normal dönüşe dönüşebilir. |
| test/hardware/steelseries/rival3_gen2/test_connection.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_connection.py`) | 43 | Gerçek cihaz bağlantı ve kapanışını dener; izin/cihaz olasılıkları yazdırır. | Çalıştırılmadı; otomatik assert ile donanım kabulü oluşturmuyor. |
| test/hardware/steelseries/rival3_gen2/test_dpi.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_dpi.py`) | 63 | Kullanıcı adımlarıyla beş DPI, polling ve save denemesi. | Çalıştırılmadı; hassasiyet ve cihaz hafızası değişir; mevcut özel profil geri yüklenmiyor. |
| test/hardware/steelseries/rival3_gen2/test_dpi_stages.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_dpi_stages.py`) | 58 | Özel beş DPI kademe listesi uygular, ardından sürücünün varsayılan listesine döner. | Manuel; çalıştırılmadı. Varsayılan liste gerçek kullanıcı yedeği değil. |
| test/hardware/steelseries/rival3_gen2/test_vitray_cli.py (`inceleme/kaynak/Muvv-main/test/hardware/steelseries/rival3_gen2/test_vitray_cli.py`) | 161 | Gerçek farede katman, fade, add, breathing, zone filtering, wave ve hız değişimi. | Manuel görsel kabul akışı; çalıştırılmadı. Hata yakalaması otomatik başarıya karışmamalı. |
| test/manager/test_capabilities_info.py (`inceleme/kaynak/Muvv-main/test/manager/test_capabilities_info.py`) | 53 | 2 unittest: capability içeriği ve IPC info komutu; sahte runner kullanır. | Bu incelemede 2/2 geçti; donanım veya socket izin testi değil. |
| test/manager/test_effect_options.py (`inceleme/kaynak/Muvv-main/test/manager/test_effect_options.py`) | 51 | 1 unittest: efekt seçeneklerinin IPC'den runner'a aktarımı. | 1/1 geçti; gerçek efekt oluşturma/render ve yanlış parametre retlerini kapsamıyor. |
| test/manager/test_manager.py (`inceleme/kaynak/Muvv-main/test/manager/test_manager.py`) | 78 | Gerçek fareyle manager, tarama ve wave/breathing akışını çalıştıran manuel entegrasyon. | Çalıştırılmadı; cihaz yokken Passing test diyor, hata da yakalanıp yazdırılıyor. |
| test/manager/test_validator.py (`inceleme/kaynak/Muvv-main/test/manager/test_validator.py`) | 91 | 3 unittest: DPI/polling sınırları ve IPC doğrulama reddi. | 3/3 geçti; eksik capability, bool/fraction ve buton sınırları mevcut testte yok. |

## Muvv_development_environment-main — 11 dosya

| Dosya | Satır | Görevi | Dikkat |
|---|---:|---|---|
| .gitignore (`inceleme/kaynak/Muvv_development_environment-main/.gitignore`) | 1 | Note.md dosyasını ignore etmeyi amaçlar. | Note.md ZIP'te mevcut; ignore özel notun dağıtılmasını tek başına engellemez. |
| development environment.md (`inceleme/kaynak/Muvv_development_environment-main/development environment.md`) | 35 | İki klasör/depo ayrımı, memory-bank konumu, venv ve commit politikası. | Ayrı repo ve ayrı commit yaklaşımı gelecekteki geliştirmede korunmalı. |
| memory-bank/activeContext.md (`inceleme/kaynak/Muvv_development_environment-main/memory-bank/activeContext.md`) | 22 | Aşama 2.1 tamamlandı ve 2.2 efekt genişleme/canlı güncelleme odağı. | Tarih/commit bağlantısı yok; gerçek factory ve doğrulama hataları dikkate alınmalı. |
| memory-bank/progress.md (`inceleme/kaynak/Muvv_development_environment-main/memory-bank/progress.md`) | 67 | İlerleme check-listesi, manager/CLI/driver, GUI/systemd/evdev/Windows yol haritası. | Lock ile çözüldü ve fiziksel test ifadeleri bu incelemenin çalışma zamanı kanıtı değildir. |
| memory-bank/projectbrief.md (`inceleme/kaynak/Muvv_development_environment-main/memory-bank/projectbrief.md`) | 16 | Linux ve marka bağımsız modüler çatı vizyonu; dört ürün katmanı. | Hedefi açıklar; mevcut tek driver ve eksik GUI'den ayrı okunmalı. |
| memory-bank/systemPatterns.md (`inceleme/kaynak/Muvv_development_environment-main/memory-bank/systemPatterns.md`) | 31 | Driver, sanal LED durumu, Vitray, daemon/GUI ayrımı ve queue desenleri. | Kaynak temizliği ve thread-safe hedefini anlatır; bugünkü uygulama garanti etmez. |
| memory-bank/techContext.md (`inceleme/kaynak/Muvv_development_environment-main/memory-bank/techContext.md`) | 27 | Python 3.10+, hidapi, NumPy/Numba, CustomTkinter, Linux/udev ve profil hedefleri. | NumPy/GUI kullanım ve profil saklama hedef; kaynakta tamamlanmamış. |
| Note.md (`inceleme/kaynak/Muvv_development_environment-main/Note.md`) | 33 | Driver/animasyon/manager/CLI tamamlanma iddiaları ve gelecek GUI/event fikirleri. | Kusursuz/tamamen hazır iddiaları kod bulgularıyla uyuşmuyor; dağıtımda özel not politikası gerekli. |
| proje.md (`inceleme/kaynak/Muvv_development_environment-main/proje.md`) | 113 | Vizyon, Python/HID/GUI mimarisi, Vitray yaklaşımı, riskler ve ilk yol haritası. | Eski plan; uygulama durumu bu belgeyle tek başına belirlenemez. reset_state uygulaması yok. |
| python_environment_setup.md (`inceleme/kaynak/Muvv_development_environment-main/python_environment_setup.md`) | 38 | Linux venv oluşturma/aktif etme ve requirements güncelleme yönergesi. | Kuruldu ifadesi tarihsel not; bu bilgisayarda kurulum kanıtı değil. Freeze temiz ortamdan üretilmeli. |
| Truemove_core.txt (`inceleme/kaynak/Muvv_development_environment-main/Truemove_core.txt`) | 89 | TrueMove Core DPI/CPI → hex değer tablosu. | Çalıştırılabilir araç değil; driver DPI_MAP için referans veri. |

## İşlevsel giriş noktaları

- `managers/device_manager.py` doğrudan çalıştırılırsa daemon başlar, HID tarar ve IPC açar. Bu incelemede çalıştırılmadı.
- `cli.py` çalışan daemon'a bağlanır; daemon'ı kendi başlatmaz.
- `managers/ipc_server.py` tek başına çalıştırıldığında device manager verilmez; cihaz kontrolü sağlayan tam daemon değildir.
- `test/hardware/` altındaki altı dosya ve `test/manager/test_manager.py` gerçek donanım/manuel akışlardır. Toplu test keşfinde ayrı tutulmalıdır.
- Diğer üç manager test dosyasındaki altı `unittest` yöntemi burada sahte HID importuyla geçirildi.
- GUI, installer, servis/unit dosyası, udev kuralı, paket metadata dosyası, README ve LICENSE bu ZIP'lerde bulunmuyor.


Bu teslim kopyasında yerel mutlak bağlantılar taşınabilir hale getirildi. Başlangıç kaynaklarının satır referansları metin olarak tutulur; bu dosyalar orijinal ZIP'lerde ve yerel inceleme alanında korunur.
