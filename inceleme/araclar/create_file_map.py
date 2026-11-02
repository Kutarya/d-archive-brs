"""Create a complete human-readable map from the verified static inventory."""
from pathlib import Path
import json

BASE = Path(r"D:\BRS\inceleme")
inventory = json.loads((BASE / "kanitlar" / "statik-envanter.json").read_text(encoding="utf-8"))
roles = {
    "Muvv-main/.gitignore": ("Python ortamı, cache, build ve IDE kalıntılarını dışlar.", "Sır dosyası politikası ayrıca tanımlanmalı; ignore geçmişi temizlemez."),
    "Muvv-main/requirements.txt": ("hidapi, customtkinter, numpy bağımlılık listesi.", "Sürüm/hash yok; GUI ve NumPy henüz kodda kullanılmıyor."),
    "Muvv-main/schemas.py": ("DPI stage/range, RGB ve mouse capability TypedDict sözleşmeleri.", "Statik tip tanımı; çalışma zamanı doğrulaması değil. Optional alanlar uygulanmalı."),
    "Muvv-main/cli.py": ("send_command, print_response, renk ayrıştırma, argüman normalizasyonu ve argparse komut menüsü.", "Sabit soket, tek recv, timeout/exit code eksikleri; static komutu registry ile uyuşmuyor."),
    "Muvv-main/drivers/base_mouse.py": ("BaseMouse soyut connect/disconnect/reconnect/color/DPI/save/flush API'si; FIFO USB işçisi.", "Sınırsız kuyruk, çıkışsız worker, süre sınırı olmayan join; lock tanımlı ama kullanılmıyor."),
    "Muvv-main/drivers/steelseries/__init__.py": ("SteelSeries sürücülerinin boş paket işaretçisi.", "İşlevsel kod içermiyor."),
    "Muvv-main/drivers/steelseries/rival3_gen2.py": ("Tek somut sürücü: VID/PID/interface, DPI/polling/buton/RGB paketleri, kayıt ve ZoneMap.", "Tuş durumunda ret sonrası rollback yok; kalıcı kayıt otomatik; gerçek ayar okuma ve yazım sonucu yok."),
    "Muvv-main/managers/device_registry.py": ("Driver dizinini tarar, BaseMouse alt sınıflarını VID/PID kataloğuna ekler.", "Import güvenilen kod çalıştırır; çakışma, yükleme sırası ve dağıtım izinleri yönetilmeli."),
    "Muvv-main/managers/device_manager.py": ("Daemon koordinasyonu, 2 saniyelik HID tarama, runner yaşam döngüsü, cihaz çözümleme ve komut yönlendirme.", "Sözlük kilitsiz; başarısız bağlantı runner'ı listede kalır; belirsiz isim ilk eşleşmeyi seçer."),
    "Muvv-main/managers/device_runner.py": ("Tek cihazın bağlantı/render thread'i, Vitray kurulumu ve donanım köprüleri.", "Eski efekt önce silinir; static factory hatalı; driver hatası/ret sonucu kaybolabilir."),
    "Muvv-main/managers/ipc_server.py": ("Unix socket sunucusu; bağlantı thread'leri, JSON komut ayrıştırma, manager çağrısı.", "Erişim politikası, timeout, işçi sınırı, framing ve katı şema eksik; JSON iki kez ayrıştırılıyor."),
    "Muvv-main/managers/validator.py": ("DPI kademe ve polling listesi doğrulama; basit buton metni kontrolü.", "Capability yokken kabul; buton doğrulaması yönlendirme yolunda kullanılmıyor."),
    "Muvv-main/animations/maps.py": ("ZoneMap: bölge isimleri, indeksler ve normalize fiziksel LED koordinatları.", "Donanımdan bağımsız yerleşim iyi; yeni cihaz girdileri ayrıca doğrulanmalı."),
    "Muvv-main/animations/vitray.py": ("Layer yığınını siyah arka plan üzerinde işler; nihai RGB kareyi üretir.", "Layer listesi render ve IPC arasında paylaşılıyor; atomik snapshot yaklaşımı gerekli."),
    "Muvv-main/animations/layer.py": ("Efekt, opacity, enable, hedef bölgeler ve normal/add/multiply harmanlama.", "Çıktı kanalları 0–255'e kırpılıyor; bozuk tip/NaN hataları üst katmanda engellenmeli."),
    "Muvv-main/animations/effect_registry.py": ("Effect dizininden BaseEffect sınıflarını isimleriyle kaydeder; Effect son ekini kısaltabilir.", "StaticColor için static alias üretmiyor; import güvenli eklenti sınırına alınmalı."),
    "Muvv-main/animations/effects/__init__.py": ("Efekt paketini ve dinamik registry yaklaşımını açıklayan paket dosyası.", "Doğrudan efekt ithali içermiyor."),
    "Muvv-main/animations/effects/base_effect.py": ("BaseEffect: zaman, speed, reset, apply soyut metodu ve genel parametre güncellemesi.", "hasattr + setattr yöntem/özel alanları değiştirir; izinli parametre şeması gerekli."),
    "Muvv-main/animations/effects/breathing.py": ("Sinüsle tek rengin parlaklığını değiştirir; tüm LED'ler için renk üretir.", "RGB ve speed girdileri doğrulanmalı; duvar saati yerine monoton zaman değerlendirilmeli."),
    "Muvv-main/animations/effects/static_color.py": ("Sabit RGB rengi tüm LED'lere uygular; kurucuda color zorunlu.", "set-color kullanımı çalışıyor; generic parametresiz factory ile kurulamıyor."),
    "Muvv-main/animations/effects/wave.py": ("LED x/y konumuna göre yönlü sinüs dalgası üretir.", "Speed iki kez çarpılıyor; update_parameters kurucu wave_length sınırını atlayabiliyor."),
    "Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/DPI dökümantasyonu.md": ("DPI/polling/kayıt paket yapıları, TrueMove Core tablosu ve HID örneği.", "Protokol belgesi; fiziksel doğrulama kaydı değil. Örnekleri doğrudan çalıştırma."),
    "Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/Renk dökümantasyonu.md": ("Üç LED bölgesi, maskeler ve RGB paket örneği.", "Örnek yalnız write yapmasına rağmen kaydedildi mesajı veriyor; kalıcılık ayrımı düzeltilmeli."),
    "Muvv-main/docs/SteelSeries/Rival 3 Gen 2/tr/Tuş Atama Dökümanı.md": ("Buton byte adresleri, HID key mode, kayıt paketi ve sol tık/scroll koruma notları.", "Markdown kod bloklarında kapanış eksikleri var; gerçek kurtarma ve garanti tanımlı değil."),
    "Muvv-main/test/manager/test_capabilities_info.py": ("2 unittest: capability içeriği ve IPC info komutu; sahte runner kullanır.", "Bu incelemede 2/2 geçti; donanım veya socket izin testi değil."),
    "Muvv-main/test/manager/test_effect_options.py": ("1 unittest: efekt seçeneklerinin IPC'den runner'a aktarımı.", "1/1 geçti; gerçek efekt oluşturma/render ve yanlış parametre retlerini kapsamıyor."),
    "Muvv-main/test/manager/test_validator.py": ("3 unittest: DPI/polling sınırları ve IPC doğrulama reddi.", "3/3 geçti; eksik capability, bool/fraction ve buton sınırları mevcut testte yok."),
    "Muvv-main/test/manager/test_manager.py": ("Gerçek fareyle manager, tarama ve wave/breathing akışını çalıştıran manuel entegrasyon.", "Çalıştırılmadı; cihaz yokken Passing test diyor, hata da yakalanıp yazdırılıyor."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_buttons.py": ("Button5'i A'ya atar, kullanıcı doğrulaması ister ve varsayılan forward'a döner.", "Manuel ve kalıcı cihaz ayarı değiştirir; çalıştırılmadı. Önceki özel eşlemeyi yedeklemiyor."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_color.py": ("Gerçek farede renk döngüsü ve bölgesel RGB denemesi; sonunda LED'leri kapatır.", "Donanım işlevi; çalıştırılmadı. Hatalar pytest keşfinde normal dönüşe dönüşebilir."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_connection.py": ("Gerçek cihaz bağlantı ve kapanışını dener; izin/cihaz olasılıkları yazdırır.", "Çalıştırılmadı; otomatik assert ile donanım kabulü oluşturmuyor."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_dpi.py": ("Kullanıcı adımlarıyla beş DPI, polling ve save denemesi.", "Çalıştırılmadı; hassasiyet ve cihaz hafızası değişir; mevcut özel profil geri yüklenmiyor."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_dpi_stages.py": ("Özel beş DPI kademe listesi uygular, ardından sürücünün varsayılan listesine döner.", "Manuel; çalıştırılmadı. Varsayılan liste gerçek kullanıcı yedeği değil."),
    "Muvv-main/test/hardware/steelseries/rival3_gen2/test_vitray_cli.py": ("Gerçek farede katman, fade, add, breathing, zone filtering, wave ve hız değişimi.", "Manuel görsel kabul akışı; çalıştırılmadı. Hata yakalaması otomatik başarıya karışmamalı."),
    "Muvv_development_environment-main/.gitignore": ("Note.md dosyasını ignore etmeyi amaçlar.", "Note.md ZIP'te mevcut; ignore özel notun dağıtılmasını tek başına engellemez."),
    "Muvv_development_environment-main/development environment.md": ("İki klasör/depo ayrımı, memory-bank konumu, venv ve commit politikası.", "Ayrı repo ve ayrı commit yaklaşımı gelecekteki geliştirmede korunmalı."),
    "Muvv_development_environment-main/python_environment_setup.md": ("Linux venv oluşturma/aktif etme ve requirements güncelleme yönergesi.", "Kuruldu ifadesi tarihsel not; bu bilgisayarda kurulum kanıtı değil. Freeze temiz ortamdan üretilmeli."),
    "Muvv_development_environment-main/Truemove_core.txt": ("TrueMove Core DPI/CPI → hex değer tablosu.", "Çalıştırılabilir araç değil; driver DPI_MAP için referans veri."),
    "Muvv_development_environment-main/proje.md": ("Vizyon, Python/HID/GUI mimarisi, Vitray yaklaşımı, riskler ve ilk yol haritası.", "Eski plan; uygulama durumu bu belgeyle tek başına belirlenemez. reset_state uygulaması yok."),
    "Muvv_development_environment-main/Note.md": ("Driver/animasyon/manager/CLI tamamlanma iddiaları ve gelecek GUI/event fikirleri.", "Kusursuz/tamamen hazır iddiaları kod bulgularıyla uyuşmuyor; dağıtımda özel not politikası gerekli."),
    "Muvv_development_environment-main/memory-bank/projectbrief.md": ("Linux ve marka bağımsız modüler çatı vizyonu; dört ürün katmanı.", "Hedefi açıklar; mevcut tek driver ve eksik GUI'den ayrı okunmalı."),
    "Muvv_development_environment-main/memory-bank/systemPatterns.md": ("Driver, sanal LED durumu, Vitray, daemon/GUI ayrımı ve queue desenleri.", "Kaynak temizliği ve thread-safe hedefini anlatır; bugünkü uygulama garanti etmez."),
    "Muvv_development_environment-main/memory-bank/techContext.md": ("Python 3.10+, hidapi, NumPy/Numba, CustomTkinter, Linux/udev ve profil hedefleri.", "NumPy/GUI kullanım ve profil saklama hedef; kaynakta tamamlanmamış."),
    "Muvv_development_environment-main/memory-bank/activeContext.md": ("Aşama 2.1 tamamlandı ve 2.2 efekt genişleme/canlı güncelleme odağı.", "Tarih/commit bağlantısı yok; gerçek factory ve doğrulama hataları dikkate alınmalı."),
    "Muvv_development_environment-main/memory-bank/progress.md": ("İlerleme check-listesi, manager/CLI/driver, GUI/systemd/evdev/Windows yol haritası.", "Lock ile çözüldü ve fiziksel test ifadeleri bu incelemenin çalışma zamanı kanıtı değildir."),
}

actual_paths = {entry["path"].replace("\\", "/") for entry in inventory}
if actual_paths != set(roles):
    raise ValueError({"unmapped": sorted(actual_paths - set(roles)), "extra": sorted(set(roles) - actual_paths)})
lines = ["# Muvv dosya haritası", "", "**11 Ekim 2026 — iki ZIP'teki 45 dosyanın tamamı.**", "",
         "[Ana inceleme ve geliştirme raporu](D:/BRS/inceleme/MUVV-INCELEME-RAPORU.md)", "",
         "Bu tablo dosyaların görevini ve dikkat edilmesi gereken noktaları özetler. Satır sayıları boş satırlar ve yorumlar dahil metin satırlarıdır. Kaynaklar değiştirilmedi.", ""]
for project in ("Muvv-main", "Muvv_development_environment-main"):
    entries = [entry for entry in inventory if entry["path"].replace("\\", "/").startswith(project + "/")]
    lines.extend([f"## {project} — {len(entries)} dosya", "",
                  "| Dosya | Satır | Görevi | Dikkat |", "|---|---:|---|---|"])
    for entry in entries:
        relative = entry["path"].replace("\\", "/")
        role, attention = roles[relative]
        target = (BASE / "kaynak" / Path(relative)).as_posix()
        label = relative[len(project) + 1:]
        lines.append(f"| [{label}](<{target}>) | {entry['lines']} | {role} | {attention} |")
    lines.append("")
lines.extend(["## İşlevsel giriş noktaları", "",
              "- `managers/device_manager.py` doğrudan çalıştırılırsa daemon başlar, HID tarar ve IPC açar. Bu incelemede çalıştırılmadı.",
              "- `cli.py` çalışan daemon'a bağlanır; daemon'ı kendi başlatmaz.",
              "- `managers/ipc_server.py` tek başına çalıştırıldığında device manager verilmez; cihaz kontrolü sağlayan tam daemon değildir.",
              "- `test/hardware/` altındaki altı dosya ve `test/manager/test_manager.py` gerçek donanım/manuel akışlardır. Toplu test keşfinde ayrı tutulmalıdır.",
              "- Diğer üç manager test dosyasındaki altı `unittest` yöntemi burada sahte HID importuyla geçirildi.",
              "- GUI, installer, servis/unit dosyası, udev kuralı, paket metadata dosyası, README ve LICENSE bu ZIP'lerde bulunmuyor.", ""])
(BASE / "DOSYA-HARITASI.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"mapped_files": len(roles), "report": str(BASE / "DOSYA-HARITASI.md")}, ensure_ascii=False))
