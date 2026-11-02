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

## 5. Python Komut Örnekleri

Aşağıdaki script, 5 slotun tamamını yapılandırır, aktif slotu seçer, Polling Rate'i ayarlar ve hafızaya kaydeder.

```python
import hid
import time

# Cihaz Bilgileri
VENDOR_ID = 0x1038
PRODUCT_ID = 0x1870
INTERFACE_NUM = 3

# DPI Lookup Tablosu
DPI_MAP = {
    200: 0x04, 400: 0x08, 800: 0x12, 1000: 0x16,
    1200: 0x1B, 1600: 0x24, 2400: 0x37, 3200: 0x49,
    6500: 0x96, 8500: 0xC5
}

def send_packet(device, packet):
    # 64 Byte'a tamamla
    if len(packet) < 64:
        packet.extend([0x00] * (64 - len(packet)))
    device.write(bytes(packet))
    time.sleep(0.05) # Buffer için küçük bekleme

def configure_mouse(active_slot, dpi_list, polling_rate_hz):
    """
    active_slot: 0-4 arası (0=Slot1)
    dpi_list: 5 elemanlı liste. Örn: [400, 800, 1200, 1600, 3200]
    polling_rate_hz: 125, 250, 500 veya 1000
    """
    try:
        # Cihazı Bul
        path = None
        for d in hid.enumerate(VENDOR_ID, PRODUCT_ID):
            if d.get('interface_number') == INTERFACE_NUM:
                path = d['path']
                break
        
        if not path:
            print("Rival 3 bulunamadı.")
            return

        h = hid.device()
        h.open_path(path)
        print(f"Bağlandı: {path}")

        # -------------------------------------------------
        # ADIM 1: DPI ve Slot Ayarlarını Gönder (0x34 05)
        # -------------------------------------------------
        dpi_packet = [0x34, 0x05, active_slot]
        
        for dpi in dpi_list:
            hex_val = DPI_MAP.get(dpi, 0x12) # Varsayılan 800
            dpi_packet.append(hex_val) # X Ekseni
            dpi_packet.append(hex_val) # Y Ekseni
            
        send_packet(h, dpi_packet)
        print(f"DPI Ayarlandı. Aktif Slot: {active_slot+1}")

        # -------------------------------------------------
        # ADIM 2: Polling Rate Ayarla (0x2B)
        # -------------------------------------------------
        hz_map = {1000: 0x01, 500: 0x02, 250: 0x03, 125: 0x04}
        hz_val = hz_map.get(polling_rate_hz, 0x01)
        
        hz_packet = [0x2B, hz_val]
        send_packet(h, hz_packet)
        print(f"Polling Rate ayarlandı: {polling_rate_hz}Hz")

        # -------------------------------------------------
        # ADIM 3: Hafızaya Kaydet (0x11)
        # -------------------------------------------------
        save_packet = [0x11, 0x00]
        send_packet(h, save_packet)
        print("Ayarlar dahili hafızaya kaydedildi.")
        
        h.close()

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    # Slot 1: 400, Slot 2: 800, Slot 3: 1600, Slot 4: 3200, Slot 5: 6500
    # Aktif Slot: 1 (İndis 1, yani 2. sıradaki 800 DPI aktif olur)
    # Hz: 1000
    my_dpis = [400, 800, 1600, 3200, 6500]
    configure_mouse(active_slot=1, dpi_list=my_dpis, polling_rate_hz=1000)