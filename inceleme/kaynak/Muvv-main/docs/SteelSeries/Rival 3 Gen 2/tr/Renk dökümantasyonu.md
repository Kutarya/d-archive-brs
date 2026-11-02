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
| **Zone 2** | `0x02` (Bit 1) | Orta | Farenin ortansında bulunan led. |
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

## 3. Python Komut Örneği

### Alt şeridi beyaz yapmak için örnek:

```python
import hid
import time

VENDOR_ID = 0x1038
PRODUCT_ID = 0x1870
INTERFACE_NUM = 3

def set_mouse_color(red, green, blue):
    """
    Tüm bölgeleri (Tekerlek, Orta, Alt) verilen RGB rengine boyar.
    Bölge maskesinde hangi bölgelerin boyanacağı yazılır
    red, green, blue: 0-255 arası tam sayı.
    """
    print(f"Renk ayarlanıyor: R={red}, G={green}, B={blue}")

    # 1. Paketi Hazırla
    packet = bytearray(64)
    packet[0] = 0x21  # Renk Komutu
    packet[1] = 0x04  # Bölge Maskesi (Sadece Alt Şerit)
    
    # Bölge 1 (Tekerlek)
    packet[2] = red
    packet[3] = green
    packet[4] = blue
    
    # Bölge 2 (Orta)
    packet[5] = red
    packet[6] = green
    packet[7] = blue
    
    # Bölge 3 (Alt Şerit)
    packet[8] = red
    packet[9] = green
    packet[10] = blue

    try:
        # Cihazı Bul
        path = None
        for d in hid.enumerate(VENDOR_ID, PRODUCT_ID):
            if d.get('interface_number') == INTERFACE_NUM:
                path = d['path']
                break
        
        if not path:
            print("Cihaz bulunamadı.")
            return

        h = hid.device()
        h.open_path(path)
        
        # 2. Renk Paketini Gönder
        h.write(bytes(packet))
        time.sleep(0.1)
        
        print("Renk değiştirildi ve kaydedildi.")
        h.close()

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    # ÖRNEK: Rengi beyaz yapar
    set_mouse_color(255, 255, 255)
