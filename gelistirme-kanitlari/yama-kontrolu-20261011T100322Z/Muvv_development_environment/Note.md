# 🚀 Muvv Projesi - Geliştirme Notları ve Eksikler Listesi

## 📌 Mevcut Durum Özeti
- **Driver Katmanı (Alt Katman):** Tamamen hazır. `rival3_gen2.py` içerisinde DPI, Polling Rate, Tuş Atama (Makro) ve On-board Memory'ye kaydetme (`save_profile`) gibi tüm donanım fonksiyonları yazılmış durumda.
- **Animasyon Katmanı (Vitray & Layer):** Kusursuz çalışıyor. Asenkron render döngüsü, katmanlı yapı (blending) ve bölgesel filtreleme (`target_zones`) aktif.
- **Manager, IPC & CLI (Üst Katmanlar):** **[TAMAMLANDI]** Alt katmandaki donanım fonksiyonlarına giden tüm köprüler (`DeviceRunner`, `DeviceManager`, `IPCServer` ve `cli.py`) kuruldu. Artık `list`, `set-effect`, `set-color`, `set-dpi`, `set-polling`, `bind-key` ve `save` komutları uçtan uca destekleniyor.

---

## 🛠️ Yapılacaklar (To-Do List)

### 1. CLI (`cli.py`) Genişletilecek
CLI'ın `argparse` menüsüne farenin donanım özelliklerini kontrol edecek yeni komutlar eklendi:
- [x] `set-dpi <device_id> <level>`: Farenin DPI kademesini değiştirmek için.
- [x] `set-polling <device_id> <hz>`: Yenileme hızını (125, 250, 500, 1000) değiştirmek için.
- [x] `bind-key <device_id> <button> <key_code>`: Fare tuşlarına klavye makrosu atamak için.
- [x] `save <device_id>`: Mevcut ayarları farenin kendi hafızasına (`CMD_SAVE_MEMORY`) yazmak için.
- [x] `info <device_id>`: Farenin desteklediği DPI, Polling, RGB ve Tuş yeteneklerini dökümlemek için.


### 2. Santral (`ipc_server.py`) Yönlendirmeleri Eklendi
CLI'dan gelen yeni JSON komutlarını anlayıp Manager'a ileten if-elif blokları eklendi:
- [x] `_process_command` metodu içine "set-dpi", "set-polling", "bind-key", "save" komutları için yönlendirme şartları yazıldı.

### 3. Manager (`device_manager.py` & `device_runner.py`) Köprüleri Kuruldu
Manager ve DeviceRunner katmanında donanım emirlerini ilgili driver'a ileten güvenli yönlendirme metotları tanımlandı:
- [x] `DeviceRunner` köprü metotları (`set_dpi`, `set_polling`, `bind_key`, `save_profile`) eklendi.
- [x] `DeviceManager` yönlendirme metotları (`set_device_dpi`, `set_device_polling`, `bind_device_key`, `save_device_profile`) eklendi.


### 4. Gelecek Fikirleri (Vision)
- [ ] Olay (Event) tabanlı entegrasyonlar: Oyun içi durumlara (can azalması, bomba kurulması) göre IPC server'a otomatik `set-effect` JSON'u fırlatacak harici bir Python scripti yazılabilir.
- [ ] GUI (Arayüz): İleride yazılacak bir masaüstü arayüzü, doğrudan bu yapının CLI/IPC sistemine entegre edilebilir.