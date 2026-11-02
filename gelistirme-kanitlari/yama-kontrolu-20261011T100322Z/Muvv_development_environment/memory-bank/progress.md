# İlerleme

## Kaynakta tamamlananlar

- [x] Rival 3 Gen 2 Wired sürücüsü ve 64 bayt paket oluşturma.
- [x] DPI, yoklama hızı, RGB ve klavye tuşu atama doğrulaması.
- [x] USB yazma sonucu, işlem sırası, kuyruk baskısı ve sınırlı kapanış.
- [x] Kilitli cihaz listesi, başarısız bağlantıyı tekrar deneme ve kapanamayan işçi takibi.
- [x] Kullanıcıya özel Unix socket, eş UID kontrolü ve mesaj çerçevesi.
- [x] CLI çıkış kodları, durum ve capability bilgisi.
- [x] Statik, nefes, dalga, spektrum ve aynı efekt örneğinde canlı parametre güncelleme.
- [x] İsimli bilgisayar profilleri; bilinmeyen alanların korunması.
- [x] CustomTkinter arayüzü ve donanımsız demo.
- [x] Paket girişleri, bağımlılık sürüm/hashleri, test aracı ve Linux CI tanımı.
- [x] Fiziksel testlerin otomatik testlerden ayrılması.

## Yerel doğrulama

Windows / Python 3.12 üzerinde otomatik çekirdek testleri ve gerçek Tk bileşenleriyle demo akışları çalıştırıldı. USB taşıması testlerde bellek içi sahte handle kullanıyor. Paket oluşturma ayrıca kontrol edildi.

Güncel toplam ve atlanan testler teslim kanıtlarındaki JSON kaydındadır. Linux kontrolleri bu bilgisayarda atlanır; donanım denemeleri otomatik olarak yapılmaz.

## Bekleyenler

- [ ] Hedef Linux dağıtımında gerçek Unix socket / izin kabulü.
- [ ] Udev ve kullanıcı systemd servisinin sahada doğrulanması.
- [ ] Gerçek fare üzerinde DPI, Hz, tuş ve RGB ölçümü.
- [ ] Kalıcı kayıt sonrası güç döngüsü ve hotplug kabulü.
- [ ] Profil otomatik yükleme politikasının ayrıca tasarlanması.
- [ ] Sistem tepsisi ve ek cihaz sınıfları.
- [ ] Makro/evdev gereksiniminin kapsam ve izinlerle ele alınması.
- [ ] Windows cihaz servisi araştırması.

Geçmiş notlardaki fiziksel deneme veya “thread-safe tamamlandı” ifadeleri bu geliştirme sürümünün kabul sonucu değildir.
