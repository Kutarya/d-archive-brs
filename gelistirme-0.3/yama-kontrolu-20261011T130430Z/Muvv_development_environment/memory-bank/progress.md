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
- [x] Komut kilidi dahil süreli kapanış, geç açılışın durdurulması ve eski işçi takibi.
- [x] Kuyrukta iptal ile belirsiz USB yazımının ayrılması; hatadan sonra yeni paket gönderilmemesi.
- [x] Bozuk profil yalıtımı, sayfalı katalog, ad değişikliği ve JSON aktarımı.
- [x] Bağımsız RGB renkleri, son kareyi koruyarak animasyonu durdurma, fare işlevi atama.
- [x] Otomatik arayüz yenilemesi, taslak koruma, bağlantıya göre işlem düğmeleri ve okunabilir tuş seçimi.
- [x] Donanıma erişmeyen ortam tanısı ve tek sürüm kaynağı.

## Yerel doğrulama

Windows / Python 3.12 üzerinde otomatik çekirdek testleri ve gerçek Tk bileşenleriyle demo akışları çalıştırıldı. USB taşıması testlerde bellek içi sahte handle kullanıyor. Paket oluşturma ayrıca kontrol edildi.

Güncel toplam ve atlanan testler teslim kanıtlarındaki JSON kaydındadır. Linux kontrolleri bu bilgisayarda atlanır; donanım denemeleri otomatik olarak yapılmaz.

0.2 regresyon sonucu: Windows / Python 3.12.10 üzerinde 134 test; 122 geçti, Linux/POSIX'e özgü 12 test atlandı, başarısızlık ve hata yok. Gerçek Tk arayüzünde 23 akış/senaryo bu toplama dahildir. Paket ve teslim doğrulama sonuçları ayrı kaydedilir.

## Bekleyenler

0.3 kaynak değişiklikleri: bağlantı oturumu koruması, USB kapanışı bitene kadar servis kilidinin tutulması, kısmi profil yenilemesi, istemci yanıt doğrulaması, geçici meşgul durumda ekran değerlerinin korunması ve sanal senaryo aracı. Windows / Python 3.12.10 üzerinde 159 testin 145'i geçti, Linux/POSIX'e özgü 14 test atlandı; hata yok. Bu toplamda 29 gerçek Tk arayüz senaryosu bulunur. Önceki 0.2 sonucu tarihsel olarak korunur.

- [ ] Hedef Linux dağıtımında gerçek Unix socket / izin kabulü.
- [ ] Udev ve kullanıcı systemd servisinin sahada doğrulanması.
- [ ] Gerçek fare üzerinde DPI, Hz, tuş ve RGB ölçümü.
- [ ] Kalıcı kayıt sonrası güç döngüsü ve hotplug kabulü.
- [ ] Profil otomatik yükleme politikasının ayrıca tasarlanması.
- [ ] Sistem tepsisi ve ek cihaz sınıfları.
- [ ] Makro/evdev gereksiniminin kapsam ve izinlerle ele alınması.
- [ ] Windows cihaz servisi araştırması.

Geçmiş notlardaki fiziksel deneme veya “thread-safe tamamlandı” ifadeleri bu geliştirme sürümünün kabul sonucu değildir.
