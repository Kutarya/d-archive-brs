# Aktif çalışma

## 2026-10-11

İndirilen kaynak üzerinden güvenlik ve ürün geliştirmesi yapıldı. Çalışan kod ayrı `Muvv` klasöründe; bu depo tasarım ve geliştirme notlarını tutuyor.

Tamamlanan işler: yerel IPC'nin kullanıcı/izin sınırları, katı komut ve efekt doğrulaması, USB sonucunun istemciye aktarılması, sınırlı kuyruk, cihaz yaşam döngüsü, canlı efekt güncelleme, spektrum, bilgisayar profilleri ve dört sekmeli masaüstü arayüzü.

0.2 sürümünde kapanış kilidine süre sınırı, başlamamış USB işleminin iptali ve hata sonrası kuyruğun durdurulması eklendi. Profil kataloğu sayfalı; bozuk dosya cihaz kontrolünü kesmiyor. Yeniden adlandırma ve doğrulanmış JSON aktarımı kullanılabilir. Arayüz otomatik yeniliyor, kullanıcı taslağını koruyor ve USB başarısını yenileme hatasından ayırıyor. Tuş adı/fare işlevi seçimi, bağımsız bölge renkleri, animasyonu durdurma ve yerel ortam tanısı eklendi.

Mevcut Driver → Runner → Manager ve Vitray/Layer/ZoneMap yapısı korunuyor. Yeni cihaz ya da genel giriş yakalama servisi eklenmedi. Makro desteği ilan edilmiyor.

## Sıradaki kabul

Linux soket/izin testlerinin hedef ortamda çalıştırılması, udev/systemd doğrulaması ve gerçek Rival 3 Gen 2 üzerinde sensör, tuş, RGB, hotplug ve kalıcılık denemesi.

Windows'ta geçen otomatik ve GUI demo testleri bu kabulün yerine geçmiyor. Native HID çağrısının bloke olması ayrı izleniyor; program bu çağrıyı zorla kesebildiğini varsaymıyor.

Kaynak depodaki `docs/HARDWARE-ACCEPTANCE.md` ölçüm listesini, `SECURITY.md` güvenlik sınırlarını, `CHANGELOG.md` uyumluluk değişikliklerini içeriyor.
