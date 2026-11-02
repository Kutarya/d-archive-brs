# Linux ve fiziksel cihaz kabulü

Bu liste otomatik testlerden ayrıdır. Hedef dağıtım, Python sürümü, HIDAPI backend'i, fare modeli ve firmware sürümüyle birlikte sonuç tutulmalıdır.

## Ortam

- Normal kullanıcıyla servis açılır; root başlangıcı reddedilir.
- Udev kuralından sonra yalnızca uygun oturum cihazı açabilir.
- Gerçek Unix socket testleri çalışır; soket 0600 ve dizin 0700 görünür.
- İkinci servis mevcut soketi kaldırmadan hata verir.
- Süre sınırları ve sekiz istemci sınırı doğrulanır.
- Kullanıcı systemd servisi başlatılır, durdurulur ve oturum davranışı kontrol edilir.

```bash
python tools/check.py --json linux-test-results.json
python tools/hardware_check.py --list
python tools/hardware_check.py --device /dev/hidrawN --mode connect
```

## Fare

Yazma denemelerinde hedef HID yolunu açıkça seçin. DPI/tuş düzeni okunamadığından bunların eski ayarı otomatik geri yüklenemez; kullanılacak tam değerleri cihaz sahibinden alın.

```bash
python tools/hardware_check.py --device /dev/hidrawN --mode color --color FF0080 --allow-write
python tools/hardware_check.py --device /dev/hidrawN --mode dpi --stages 400 800 1200 2400 3200 --active 1 --allow-write
python tools/hardware_check.py --device /dev/hidrawN --mode buttons --button button5 --usage 0x04 --initialize-buttons --allow-write
python tools/hardware_check.py --device /dev/hidrawN --mode vitray --effect wave --duration 5 --allow-write
```

- Üç RGB bölgesinde renk ve efekt yönü gözlenir; sabit renk gereksiz sürekli yazım üretmez.
- Her DPI kademesi gerçek hareket davranışıyla, yoklama hızı uygun ölçümle kontrol edilir.
- A/Enter/modifier atamaları bir test editöründe denenir; en az bir sol tık kalır.
- Kalıcı kayıt ayrıca `--persist` ile seçilir; bağlantı kesilip yeniden açıldıktan sonra değerler kontrol edilir.
- Yazılım animasyonu servis kapanınca durur. Fare belleğine kayıt aynı animasyonu firmware'e aktarmış sayılmaz.
- Profilde bulunmayan alanlar değişmez; yanlış model veya bozuk profil hiçbir rapor yazmadan reddedilir.
- Komut sırasında fare çıkarılır; hata başarı gösterilmez, yeni bağlantıda eski oturum ayarları otomatik yazılmaz.
- Uzun native yazımda kapanış/yeniden bağlanma davranışı kaydedilir. Açık handle yerine ikinci yazıcı başlatılmaz.

## Kayıt tablosu

| Deneme | Beklenen | Sonuç / gözlem |
|---|---|---|
| Soket izinleri ve kullanıcı ayrımı | 0700/0600; farklı UID reddi | Bekliyor |
| Root olmadan HID açma | Başarılı | Bekliyor |
| DPI, Hz ve tuşlar | Fiziksel davranış doğru | Bekliyor |
| RGB ve canlı güncelleme | Beklenen renk/yön/hız | Bekliyor |
| Kalıcı kayıt ve güç döngüsü | Cihazda doğrulama | Bekliyor |
| Hotplug / komut sırasında çıkarma | Hata ve temiz yeniden bağlantı | Bekliyor |
| Servis kapanışı / native I/O | Ölçülen sınırlar ve handle temizliği | Bekliyor |

Eksik veya atlanan bir test geçti olarak işaretlenmez. Otomatik Linux CI'nin başarı sonucu da fiziksel fare kabulünün yerine geçmez.
