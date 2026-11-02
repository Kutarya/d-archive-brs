# SteelSeries Rival 3 (Gen 2) - RGB Protokol Detayları.

Bu belge, SteelSeries Rival 3 (Gen 2 - Wired) faresinin RGB protokolünü tersine mühendislik yöntemleriyle açıklayan bir dokümandır.

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

## 2. RGB / LED Kontrol Protokolü (Detaylı)

Farenin aydınlatma sistemi `0x21` komutu ile yönetilir. Rival 3 üzerinde bağımsız kontrol edilebilen 3 adet aydınlatma bölgesi (Zone) bulunur.

### 2.1. Aydınlatma Bölgeleri (Zones)

| Bölge ID | Bit Maskesi | Donanım Karşılığı | Açıklama |
| :--- | :--- | :--- | :--- |
| **Zone 1** | `0x01` (Bit 0) | Tekerlek (Scroll Wheel) | Farenin tekerlek ışığı. |
| **Zone 2** | `0x02` (Bit 1) | Orta | Farenin ortasında bulunan led. |
| **Zone 3** | `0x04` (Bit 2) | Alt Şerit (Underglow) | Farenin alt kısmındaki LED şerit. |

### 2.2. RGB Paket Yapısı (11 Byte Aktif)

Renk paketi toplam 64 byte'tır ancak sadece ilk 11 byte aktiftir. Geri kalanı `0x00` olmalıdır. Aşağıda bir örnek var. Bu örnek tüm bölgeleri kırmızı yapar.

| Byte Index | Parametre | Açıklama | Örnek (Kırmızı) |
| :--- | :--- | :--- | :--- |
| **0** | Header | Sabit Renk Komutu | `0x21` |
| **1** | Zone Mask | Hedef Bölgeler (Maske Toplamı) | `0x07` (Hepsi) |
| **2** | Z1 Red | Tekerlek - Kırmızı | `0xFF` (255) |
| **3** | Z1 Green | Tekerlek - Yeşil | `0x00` |
| **4** | Z1 Blue | Tekerlek - Mavi | `0x00` |
| **5** | Z2 Red | Orta - Kırmızı | `0xFF` (255) |
| **6** | Z2 Green | Orta - Yeşil | `0x00` |
| **7** | Z2 Blue | Orta - Mavi | `0x00` |
| **8** | Z3 Red | Alt Şerit - Kırmızı | `0xFF` (255) |
| **9** | Z3 Green | Alt Şerit - Yeşil | `0x00` |
| **10** | Z3 Blue | Alt Şerit - Mavi | `0x00` |

### 2.3. Maskeleme Mantığı (Zone Masking)

Byte 1 (`Zone Mask`), gönderilen renk verisinin hangi LED'lere uygulanacağını belirler.
* **Sadece Tekerlek:** `0x01`
* **Sadece Orta:** `0x02`
* **Sadece Alt Şerit:** `0x04`
* **Tekerlek + Orta:** `0x01 + 0x02 = 0x03`
* **Tüm Işıklar (Hepsi):** `0x01 + 0x02 + 0x04 = 0x07`

---

## 3. Uygulama üzerinden deneme

```bash
muvv set-color FF0080 1
muvv set-effect wave -d 1 --color 00FF00 --speed 0.5
muvv save 1
```

İlk iki komut aydınlatmayı değiştirir. Kaydetme komutu ayrıca gönderilir; renk paketi tek başına kalıcı kayıt kanıtı değildir. Yazılım animasyonu servis çalışırken hesaplanır.

Tüm bölgeleri güncelleyen sürücü 0x07 maskesi kullanır. Tek bölgeye yönelik protokol denemesi ayrıca tam üç bölge baytlarını hazırlamalı ve yalnızca hedef maskeyi seçmelidir. Güncel GUI/CLI tüm bölgeler için efekt uygular.
