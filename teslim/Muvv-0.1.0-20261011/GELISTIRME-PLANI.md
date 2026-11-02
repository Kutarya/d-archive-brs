# Muvv geliştirme planı

11 Ekim 2026. Başlangıç: Muvv kaynak ZIP'i `b3466453ba3f8bdb697cd182832dae22318dfbf3` kimlikli anlık görüntü.

Kod `D:\BRS\Muvv`, geliştirme belgeleri `D:\BRS\Muvv_development_environment` içinde tutulur. Orijinal ZIP'ler ve `inceleme/kaynak` değişmez. Uzak repo erişimi ve yayın bu çalışmanın kapsamında değil.

## İş sırası

1. Yerel IPC: kullanıcıya özel soket, sahiplik/izin ve peer kontrolü, tek servis kilidi, süre/istemci sınırı, boyut sınırlı frame protokolü, temiz kapanış.
2. Komut doğrulama: katı türler, capability desteği, renk/buton/HID kod sınırları, atomik efekt değişimi, static factory, monoton saat ve wave hız düzeltmesi.
3. USB işlemleri: yazım sonucu, sınırlı kontrol kuyruğu, son RGB kareyi tutma, atomik paket grupları, durdurulabilir işçi, süreli kapanış ve belirsiz donanım durumunun doğru bildirimi.
4. Cihaz yönetimi: kilitli runner erişimi, başarısız bağlantıda tekrar deneme, güvenilir durum bilgisi, belirsiz cihaz seçimini reddetme ve mevcut ayarları koruma.
5. Ürün: DPI kademeleri, canlı efekt güncellemesi, Spectrum Cycle, sürümlü kullanıcı profilleri, CLI hata kodları ve mevcut API üzerinde masaüstü arayüzü.
6. Teslim: temiz kurulum, sabit bağımlılıklar, CI, dar Linux erişim/servis örnekleri, kullanım/değişiklik belgeleri, kaynak paketi ve test kanıtı.

## Kabul

- Mevcut komut isimleri ve JSON sonuç alanları korunur. Wire protokolü değişirse iki uç birlikte güncellenir ve geçiş belgelenir.
- Geçersiz istek hiçbir profil/efekt durumunu değiştirmez; takip eden geçerli istek çalışır.
- Kuyruğa kabul, USB yazımı ve cihazda kalıcılık ayrı bildirilir. Desteklenmeyen cihaz okuma/geri yükleme işlemi varmış gibi gösterilmez.
- Yavaş/hatalı yazım, boşta istemci, eşzamanlı komutlar, hotplug ve kapanış regresyonları sınanır.
- Otomatik testler fiziksel HID cihazına erişmez. Manuel cihaz testleri açık seçim gerektirir.
- Kaynak ZIP'leri ve inceleme kopyalarının hash değerleri korunur.
- Kod, belgeler ve kullanıcı mesajları kısa, tutarlı ve projenin mevcut üslubuna uygun olur.

## Doğrulama seviyeleri

Windows'ta donanımsız testler ve paket kurulumu; varsa mevcut Linux ortamında gerçek Unix soketi/izin testleri. Fiziksel fare ve firmware doğrulaması ayrıca kaydedilir. İşletim sistemi veya açık uygulamalar üzerinde ayar değişikliği yapılmaz.

## Teslim durumu — 11 Ekim 2026

Altı aşamanın yerel uygulaması tamamlandı. Son kontrol: 89 otomatik test, 78 geçen ve Linux gerektiren 11 atlanan test; sıfır hata/başarısızlık. Kaynak dışındaki temiz wheel kurulumu, hashli bağımlılıklar, GUI demo ve başlangıç kaynaklarının korunması ayrıca doğrulandı.

Hedef Linux IPC/izin kabulü, udev/systemd, fiziksel fare ölçümü ve güç döngüsü sonrası kalıcılık bekliyor. Uzak CI veya yayın yapılmadı. Ayrıntı ve teslim dosyaları GELISTIRME-RAPORU.md içindedir.
