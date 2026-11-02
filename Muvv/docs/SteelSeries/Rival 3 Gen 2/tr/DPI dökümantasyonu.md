# SteelSeries Rival 3 (Gen 2) - DPI & Performans Protokol Detayları

Bu belge, SteelSeries Rival 3 (Gen 2 - Wired) faresinin **DPI (CPI)**, **Polling Rate (Hz)** ve **Dahili Hafıza Kayıt** protokollerini tersine mühendislik yöntemleriyle açıklayan teknik bir dokümandır.

---

## 1. Donanım ve Bağlantı Bilgileri

| Parametre | Değer |
| :--- | :--- |
| **Cihaz Adı** | SteelSeries Rival 3 (Wired) |
| **Vendor ID (VID)** | `0x1038` |
| **Product ID (PID)** | `0x1870` |
| **Kritik Arayüz (Interface)** | 3 (HID Output Report) |
| **Paket Boyutu** | 64 Byte |
| **İletişim Yöntemi** | `HID write()` |

---

## 2. DPI / Hassasiyet Kontrol Protokolü

Farenin DPI ayarları `0x34` komutu ile yönetilir. Rival 3, hafızasında 5 farklı DPI slotu (Level) tutar. Protokol, sadece tek bir slotu değiştirmek yerine, **o anki aktif slotu ve diğer tüm slotların değerlerini toplu halde** gönderir.

### 2.1. DPI Paket Yapısı (13 Byte Aktif)

Bu komut, farenin hassasiyet seviyelerini yapılandırır. X ve Y eksenleri için bağımsız değer atanabilir (genellikle X=Y kullanılır).

**Temel Komut:** `0x34 05`

| Byte Index | Parametre | Açıklama | Örnek |
| :--- | :--- | :--- | :--- |
| **0** | Header | DPI Konfigürasyon Başlığı | `0x34` |
| **1** | Sub-Header | Yazma İşlemi | `0x05` |
| **2** | Active Slot | O an seçili olacak slot (0-4 arası) | `0x00` (Slot 1) |
| **3** | Slot 1 (X) | 1. Slotun X Ekseni Değeri | `0x12` (800 DPI) |
| **4** | Slot 1 (Y) | 1. Slotun Y Ekseni Değeri | `0x12` |
| **5** | Slot 2 (X) | 2. Slotun X Ekseni Değeri | `0x19` (1100 DPI) |
| **6** | Slot 2 (Y) | 2. Slotun Y Ekseni Değeri | `0x19` |
| **7** | Slot 3 (X) | 3. Slotun X Ekseni Değeri | `0x24` (1600 DPI) |
| **8** | Slot 3 (Y) | 3. Slotun Y Ekseni Değeri | `0x24` |
| **9** | Slot 4 (X) | 4. Slotun X Ekseni Değeri | `0x49` (3200 DPI) |
| **10** | Slot 4 (Y) | 4. Slotun Y Ekseni Değeri | `0x49` |
| **11** | Slot 5 (X) | 5. Slotun X Ekseni Değeri | `0x96` (6500 DPI) |
| **12** | Slot 5 (Y) | 5. Slotun Y Ekseni Değeri | `0x96` |
| **13-63**| Padding | Boş veri (Zero Padding) | `0x00`... |

### 2.2. DPI Değer Tablosu (Lookup Table)

 DPI değerleri rivalcfg projesinden (WTFPL Lisanslı) alınmıştır.

 https://github.com/flozz/rivalcfg

DPI değerleri algoritmik olarak hesaplanmaz, sensörün desteklediği belirli HEX karşılıkları vardır. (TrueMove Core Sensor)

| DPI | Hex Değeri | DPI | Hex Değeri | DPI | Hex Değeri |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **200** | `0x04` | **1000** | `0x16` | **3200** | `0x49` |
| **400** | `0x08` | **1200** | `0x1B` | **4000** | `0x5C` |
| **800** | `0x12` | **1600** | `0x24` | **6500** | `0x96` |
| **900** | `0x14` | **2400** | `0x37` | **8500** | `0xC5` |

*(Tam liste bu adrestedir: https://github.com/flozz/rivalcfg/blob/master/rivalcfg/devices/dpi/truemove_core.py)*

---

## 3. Polling Rate (Raporlama Hızı) Protokolü

Farenin bilgisayara veri gönderme sıklığı `0x2B` komutu ile ayarlanır. Bu ayar tüm slotlar için globaldir.

**Temel Komut:** `0x2B`

| Byte Index | Parametre | Açıklama |
| :--- | :--- | :--- |
| **0** | Header | Polling Rate Komutu (`0x2B`) |
| **1** | Hz Value | İstenilen Hz değerinin Hex karşılığı |

### 3.1. Hz Değer Tablosu

| Polling Rate | Gecikme | Hex Değeri |
| :--- | :--- | :--- |
| **1000 Hz** | 1ms | `0x01` |
| **500 Hz** | 2ms | `0x02` |
| **250 Hz** | 4ms | `0x03` |
| **125 Hz** | 8ms | `0x04` |

---

## 4. Kayıt Protokolü (Save to On-Board Memory)

Yapılan değişikliklerin (DPI, Hz) kalıcı olması ve farenin dahili hafızasına yazılması için ayar paketlerinden hemen sonra bu komut gönderilmelidir. Aksi takdirde ayarlar ya hiç ayarlanmaz yada fare güç kesilip geldiğinde eski ayarlarına döner.

| Byte Index | Değer | Açıklama |
| :--- | :--- | :--- |
| **0** | `0x11` | Kayıt Komutu |
| **1** | `0x00` | Alt Komut |

---

## 5. CLI kullanım örnekleri

Beş kademe birlikte yazılır. Uygulama örneği:

```bash
muvv set-dpi-stages 400 800 1200 2400 3200 -d 1 --active 1
muvv set-polling 500 1
muvv save 1
```

Etkin kademe CLI'de 0–4 aralığındadır. İlk komut beş değeri açıkça değiştirir. Önceki slotlar firmware'den okunmadığı için kısmi seçim, bilinen slot düzeni veya açık varsayılan başlangıç gerektirir.

USB yazımının başarılı dönmesi sensör hızının ya da kalıcılığın fiziksel doğrulaması değildir. Donanım kabulünde her kademe ve güç döngüsü ayrıca denenir.
