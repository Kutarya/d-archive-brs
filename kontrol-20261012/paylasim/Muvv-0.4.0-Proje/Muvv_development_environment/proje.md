# Muvv teknik tasarımı

11 Ekim 2026 geliştirme kopyası. Uygulama Linux üzerinde HID fare ayarlarını yönetir. Şu anda desteklenen cihaz SteelSeries Rival 3 Gen 2 Wired modelidir (`1038:1870`, HID arayüzü 3).

## Kapsam

Kullanıcı beş DPI kademesini, etkin kademeyi, yoklama hızını, üç RGB bölgesini ve klavye tuşu atamalarını yönetebilir. Sabit renk, nefes, dalga ve spektrum efektleri servis içinde hesaplanır. CLI ve masaüstü arayüzü aynı yerel servisi kullanır.

0.2 sürümünde bölgelere ayrı renk, son rengi koruyarak animasyonu durdurma ve fare işlevi atama vardır. Profil adları değiştirilebilir; profiller doğrulanmış JSON olarak içe/dışa aktarılabilir. Arayüz cihaz durumunu otomatik yeniler, uygulanmamış girişleri korur ve bozuk profil dosyalarını ayrı bildirir.

Bilgisayardaki isimli profiller ile farenin kalıcı belleğine kayıt ayrı işlemlerdir. Profil yalnızca Muvv oturumunda bilinen ayarları içerir; cihazdan okunmuş bir yedek değildir. Bağlantı açıldığında DPI ve tuş düzeni kendiliğinden değiştirilmez.

## Bileşenler

| Bileşen | Görev |
| --- | --- |
| `drivers/` | Cihaz protokolü, paket oluşturma ve tek USB yazıcısı |
| `animations/` | Vitray katmanları, LED koordinatları ve efektler |
| `managers/device_runner.py` | Bir cihazın komutlarını ve animasyon döngüsünü sıraya koyma |
| `managers/device_manager.py` | Cihaz tarama, bağlantı tekrarları ve doğru sürücüyü seçme |
| `ipc_protocol.py`, `managers/ipc_server.py` | Yerel mesaj çerçevesi, kullanıcı ve istek doğrulama |
| `managers/profile_store.py` | Sürümlü profil doğrulaması ve dosya işlemleri |
| `cli.py`, `gui.py` | Kullanıcı komutları ve sonuçların gösterimi |
| `ui_client.py`, `profile_io.py` | Durum yenileme akışı ve yerel profil aktarımı |
| `diagnostics.py`, `app_version.py` | Donanımsız ortam denetimi ve sürüm kaynağı |
| `demo.py` | Gerçek USB açmadan uygulama akışlarının denenmesi |

Vitray RGB karelerini standart Python veri yapılarıyla üretir. Bu sürümde NumPy ve Numba kullanılmaz. Yeni sürücü ve efektler açık kayıt işlevleriyle eklenir; klasör içindeki Python dosyaları kendiliğinden yüklenmez.

## İşlem sırası

Kullanıcı komutu önce doğrulanır, ardından cihazın komut kilidi alınır. Bir ayar ve ona bağlı kayıt raporu aynı USB işleminde gönderilir. Bir işlem sürerken araya animasyon paketi girmez. USB kontrol kuyruğu 64 işlemle sınırlıdır; animasyonda yalnızca son bekleyen kare tutulur.

USB yazımı başarılı dönmeden RAM'deki ayar tamamlanmış sayılmaz. İşlem yarıda kalırsa donanım durumu belirsiz olarak işaretlenir; güvenli bir donanım geri alma protokolü varmış gibi davranılmaz. Yerel RAM değişikliğinin geri alınması fiziksel fareyi geri aldığı anlamına gelmez.

## Erişim ve kalıcılık

Servis masaüstü kullanıcısının hesabında çalışır. Modeli eşleştiren udev kuralı aktif yerel oturuma erişim verir. Root ile sürekli servis çalıştırma veya tüm kullanıcılara `0666` cihaz erişimi verme önerilmez.

IPC soketi kullanıcıya özel dizindedir. Dizin 0700, soket 0600 olur; iki uç birbirinin UID'sini denetler. Bu koruma aynı kullanıcı hesabında çalışan güvenilmeyen kodu ayrı bir güvenlik alanına taşımaz.

Profiller `$XDG_CONFIG_HOME/muvv/profiles` altında, değişken yoksa `~/.config/muvv/profiles` altında tutulur. Kullanıcı açıkça kaydeder ve uygular. Açılışta otomatik profil uygulama bu sürümde yoktur.

## Doğrulama ve sonraki işler

Windows üzerinde sahte HID, mesaj çerçevesi, profil, CLI ve gerçek Tk bileşenleriyle demo testleri yapıldı. Linux Unix soketi/izin kontrolleri ve fiziksel fare kabulü henüz tamamlanmadı. Uygulama deposundaki `docs/HARDWARE-ACCEPTANCE.md` bu kabulün kaydını tutar.

Sonraki adım hedef Linux dağıtımında IPC, udev, systemd ve hotplug kontrollerini çalıştırmaktır. Ardından gerçek farede DPI, yoklama hızı, tuş davranışı ve güç döngüsü sonrası kalıcı kayıt doğrulanmalıdır.

Sistem tepsisi, Windows cihaz servisi, ek markalar, makro/evdev ve otomatik profil yükleme ayrı iş kalemleridir. Kaynak paketlerinde lisans dosyası bulunmadığından açık dağıtım koşulları repo sahibiyle netleştirilmelidir.
