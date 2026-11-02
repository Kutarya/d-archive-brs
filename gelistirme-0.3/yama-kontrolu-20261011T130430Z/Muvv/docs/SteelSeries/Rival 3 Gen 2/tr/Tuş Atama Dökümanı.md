# SteelSeries Rival 3 (Gen 2) - EEPROM Protokol Dokümantasyonu

Bu belge, SteelSeries Rival 3 (Gen 2 - Wired) faresinin tuş atamalarını değiştirmek ve kaydetme komutu göndermek için gerekli teknik verileri içerir.

---

## 1. Cihaz Kimlik Bilgileri
| Parametre | Değer |
| :--- | :--- |
| **Cihaz Adı** | SteelSeries Rival 3 (Wired) |
| **Vendor ID (VID)** | `0x1038` |
| **Product ID (PID)** | `0x1870` |
| **İletişim Arayüzü** | Interface 3 (HID API üzerinden) |
| **Paket Boyutu** | 64 Byte |
| **Paket Tipi** | Output Report (Write) |

---

## 2. Byte Adres Haritası (Memory Map)

Farenin konfigürasyon paketi 64 byte uzunluğundadır. Tuşlar belirli "Index" (Offset) adreslerine yerleştirilmiştir. Tuşlar arasında **5 byte'lık** düzenli bir artış vardır.

> [!CAUTION]
> **KRİTİK UYARI 1:** `Scroll Up (31)` ve `Scroll Down (36)` adreslerindeki değerler silinirse (0x00 olursa) farenin tekerleği çalışmayı durdurur.

> [!WARNING]
> **KRİTİK UYARI 2:** Sol Tık (`Index 1`) değerini değiştirmeden önce, fare üzerinde tıklama yapabilecek başka bir tuş atadığınızdan emin olun. Aksi takdirde işletim sisteminde tıklama yapamazsınız.

| Byte Index | Fonksiyon | Varsayılan (Hex) | Açıklama |
| :--- | :--- | :--- | :--- |
| **0** | Header | `2A` | Sabit. Komut başlangıcı. |
| **1** | Sol Tık | `01` | Fiziksel Sol Tuş. |
| **6** | Sağ Tık | `02` | Fiziksel Sağ Tuş. |
| **11** | Orta Tık | `03` | Tekerleğe basma (Middle Click). |
| **16** | Button 4 | `04` | Yan taraf, arka tuş (Geri). |
| **21** | Button 5 | `05` | Yan taraf, ön tuş (İleri). |
| **26** | DPI Tuşu | `30` | Üstteki küçük tuş. |
| **31** | Scroll Up | `31` | Tekerlek yukarı. |
| **36** | Scroll Down | `32` | Tekerlek aşağı. |

*Not: Kalan boşluklar (`0x00`) dolgu (padding) olarak kullanılır.*

*Her tuş bloğu 5 byte yer kaplar (Örn: Index 1-5 Sol Tık bloğudur)*

---

## 3. Değer Yazma Mantığı

Bir adrese yazılacak değer, o tuşun **Fare Fonksiyonu** mu yoksa **Klavye Tuşu** mu olacağına göre değişir.

### A. Standart Fare Fonksiyonu (1 Byte)
Sadece ilgili index'e buton kodunu yazın.
* **Sol Tık:** `0x01` | **Sağ Tık:** `0x02` | **Orta Tık:** `0x03`
* **Geri (Back):** `0x04` | **İleri (Forward):** `0x05`

**Örnek (Solak Modu):** Sol ve Sağ tıkın yerini değiştirmek:
```python
packet[1] = 0x02 # Fiziksel Sol Tuş -> Sağ Tık yapar
packet[6] = 0x01 # Fiziksel Sağ Tuş -> Sol Tık yapar
```

### B. Klavye Tuşu Atama (2 Byte)
Bir tuşu klavye tuşuna çevirmek için **Type ID** ve **Key Code** kullanılır.

* **Adres [Index]:** `0x51` (Type ID: Klavye Modu)
* **Adres [Index + 1]:** `KeyCode` (Tuş Kodu)

**Örnek:** Button 5'i (Index 21) "Shift" yapmak:
`packet[21] = 0x51`, `packet[22] = 0xE1`

---

## 4. Kaydetme (Commit) Protokolü
Yapılan değişikliklerin kalıcı olması ve cihaz yeniden başlatıldığında (plug/unplug) hatırlanması için, konfigürasyon paketinden sonra mutlaka **Save paketi** gönderilmelidir. Bu paket gönderilmezse ayarlar geçici kalabilir veya hiç uygulanmayabilir.

* **Save Paketi Yapısı:** `0x11` ile başlar, geri kalan 63 byte `0x00` olur.

```python
# Python ile Save komutu
save_packet = bytearray(64)
save_packet[0] = 0x11
h.write(bytes(save_packet))
```


## 5. Uygulama üzerinden deneme

Ham HID şablonu yerine doğrulama ve USB sonuç takibi yapan CLI kullanılabilir:

```bash
muvv bind-key button5 0xE1 1 --initialize --no-persist
muvv restore-buttons 1 --no-persist
muvv save 1
```

İlk komut okunamayan tüm tuş düzenini varsayılanlarla başlatır ve Button 5'i sol Shift yapar. Varsayılanlar fareden alınmış bir yedek değildir. Kalıcı kayıt ayrıca seçilir; sonucunu yeniden bağlantıdan sonra fiziksel cihazda kontrol edin.

Bu protokol notunda klavye tuşu ataması vardır; genel makro kaydetme/oynatma desteği uygulanmış değildir.
