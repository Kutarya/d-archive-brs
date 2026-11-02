# Güvenlik sınırları

Muvv aynı Linux hesabındaki CLI ve arayüzün bir HID servisine erişmesini sağlar. Farklı kullanıcıların erişimini sınırlar; aynı hesabın ele geçirilmesine veya yönetici erişimine karşı ayrı bir güvenlik alanı oluşturmaz.

## Yerel erişim

- Soket `$XDG_RUNTIME_DIR/muvv/muvv.sock` altında; değişken yoksa `/tmp/muvv-UID/muvv.sock` altında oluşturulur.
- Dizin kullanıcıya ait ve 0700, soket 0600 olmalıdır. Yol bileşenlerinde sembolik bağlantı kabul edilmez.
- Sunucu ve istemci Linux `SO_PEERCRED` ile diğer ucun UID'sini doğrular.
- Servis kilidi ikinci örneğin yaşayan soketi silmesini önler. Normal dosya veya başka kullanıcıya ait soket kaldırılmaz.
- Sunucu en fazla sekiz istemci işçisi açar. İstek 16 KiB, yanıt 64 KiB ile sınırlıdır.
- İstek başlığı/gövdesi için toplam beş saniye okuma süresi vardır. JSON derinliği ve düğüm sayısı sınırlıdır.
- `muvvd` root olarak çalışmayı reddeder. TCP dinleyicisi, web servisi veya ağdan yönetim API'si yoktur.

Soket izinleri ve eş kimliği davranışı [Linux Unix socket belgesine](https://manpages.debian.org/bookworm/manpages/unix.7.en.html), dizin seçimi [XDG tanımına](https://specifications.freedesktop.org/basedir/latest/) dayanır.

## Komut ve USB sınırı

Efektler yalnızca tanımlı seçeneklerini değiştirebilir; yöntem adları ve özel alanlar parametre değildir. DPI, renk, yoklama hızı, tuş adı ve HID kodları yazmadan önce doğrulanır. Eksik capability desteğe izin vermez.

USB kontrol kuyruğu 64 işlemle sınırlıdır. Bir işlemde en fazla 16 rapor bulunur; rapor üreten iterable da bu sınırda durdurulur. Raporlar arasındaki gecikme sonlu ve 0–1 saniye olmalıdır. Bir işlem başladıktan sonra raporları arasına RGB yazımı girmez. Kullanıcı komutu cihaz kilidini en fazla bir saniye, USB sonucunu 1,5 saniye bekler. Henüz başlamamış işlem süre dolunca iptal edilir. Başlamış yazımın süresi dolarsa sonuç belirsizdir; bağlantı yazıma kapatılır. USB hatasından sonra diğer bekleyen paketler gönderilmez.

RGB için eski kareler biriktirilmez. Yeni açık renk işlemi, bekleyen eski RGB karesini kaldırır. İşlemin tamamlandığı ancak USB yazımı başarılı döndüğünde bildirilir; firmware'den ayar doğrulaması yapılmaz. [HIDAPI yazma sözleşmesi](https://libusb.info/hidapi/group__API.html).

Native HID sürücüsü bir yazma veya açma çağrısında kalırsa Python o çağrıyı zorla durduramaz. Kapanışta USB işçisi için bekleme sınırı vardır; bloke olmuş yazıcı yerine ikinci yazıcı açılmaz. İşçi çağrı döndüğünde handle'ı kapatır. Bu durum fiziksel cihazda ve hedef Linux dağıtımında ayrıca denenmelidir.

Kapanış istendiğinde işlem içindeki henüz gönderilmemiş raporlar da durur; paket arası gecikme kesilir. O anda başlamış yerel HID çağrısı geri alınamaz. Yarım kalan işlem belirsiz durum olarak bildirilir; kalan raporların gönderilmesi veya donanımın geri alınması başarı varsayılmaz.

Runner kapanışında komut kilidi de aynı süre bütçesiyle alınır. Açma işlemi kapanış talebinden sonra dönerse render yeniden başlatılmaz. Tam kapanmayan runner, USB işçisi henüz oluşmamış olsa da takip edilir. Aynı IPC nesnesi önceki istemci işçileri kapanmadan yeniden başlatılamaz.

Kapanış dinleyiciyi kapatır; servis dosya kilidi ancak tarama, USB ve IPC işçileri bitince bırakılır. Bloke USB/tarama varsa kilit aynı süreçte tutulur; ikinci servis bu sürede açılmaz. Kapanış `False` döndüyse çağrı çözüldükten sonra aynı manager'ın `stop()` işlemiyle temizlik tamamlanabilir. Süreç çıkışı işletim sistemi kaynaklarını bırakır; native çağrıyı Python'un zorla durdurduğu varsayılmaz.

Her başarılı bağlantı rastgele bir `session_id` üretir. İsteğe bağlı `expected_session` taşıyan komut oturumu cihaz komut kilidi alındıktan sonra kontrol eder; eski oturum `device_changed` alır ve cihaza yazılmaz. Arayüz bu korumayı kullanır. Alanı göndermeyen eski CLI çağrıları mevcut davranışı korur. Bu kimlik kimlik doğrulama anahtarı veya firmware kimliği değildir.

VID/PID bir cihaz eşleştirme bilgisidir, kriptografik cihaz kimliği değildir. Udev kuralı desteklenen modeli daraltır; uygulama HID arayüzü 3'ü seçer.

## Profil ve eklentiler

Profiller kullanıcıya ait 0700 dizinde, 0600 JSON dosyalarında tutulur. Dosya adı profil adının SHA-256 değerinden üretilir; ad yol olarak kullanılmaz. Dosya boyutu 32 KiB, profil sayısı 128 ile sınırlıdır. Kayıt önce geçici dosyaya yazılır ve atomik dosya işlemiyle tamamlanır.

Profil taraması sınırlıdır; bozuk dosyalar sayımda tutulur ve geçerli profilleri engellemez. Katalog sayfaları en fazla 32 dosyayı işler. Bilinmeyen alan listesi ayar içeriğiyle tutarlı olmalıdır. Aktarılan dosyada geçersiz JSON, tekrar eden alanlar, büyük dosya, dizin ve sembolik bağlantı reddedilir. POSIX'te FIFO açılmadan kontrol edilir; sonrasındaki dosya açma da nonblocking/no-follow seçenekleriyle yapılır. Dışa aktarma geçici dosyadan tamamlanır; mevcut çok bağlantılı dosya veya sembolik bağlantı üzerine yazılmaz.

Yeniden adlandırma önce yeni doğrulanmış kopyayı kaydeder, sonra eski dosyayı kaldırır. İki dosyayı kapsayan atomik işlem değildir; arada güç kesilirse iki kopya kalabilir. Kaynak kaldırma hatasında yeni kopyayı geri kaldırarak eski profil korunur. Dosya sistemi bu geri alma işlemini de reddederse klasörün elle kontrol edilmesi gerekir. Bozuk dosyalar kendiliğinden silinmez.

Profil yalnızca oturumda bilinen alanları kaydeder. Başlangıç varsayılanları kullanıcının gerçek fare ayarları olarak gösterilmez. Bilinmeyen alanlar uygulanmaz. USB işlemi yarıda kalırsa donanım geri alınmış sayılmaz.

Katalog kimliği dosya adları ve dosya bilgilerini kapsar. Üzerine yazma ve sayfa okunurken değişen dosyalar algılanır; dosya içeriğinin hash'i veya dosya sisteminin işlemsel anlık görüntüsü değildir. Sayfalar farklı kataloğa aitse CLI başarı döndürmez. GUI eksik listeyi bildirirken son bilinen profil adlarını korur; uygulama sırasında profil yeniden doğrulanır.

Sürücü ve efekt kayıtları açık modül listesi kullanır. Klasöre bırakılmış herhangi bir Python dosyası kendiliğinden import edilmez. `register_driver` / `register_effect` ile eklenen kod uygulama yetkisiyle çalışır; yeni eklenti güvenilen kaynak kodudur.

## Bağımlılıklar ve bildirim

Çalışma zamanı paketleri `requirements-lock.txt` ile sürüm ve hash olarak sabitlenir. Bilinen açık taraması:

```bash
pip-audit --require-hashes --disable-pip -r requirements-lock.txt
```

Bu tarama uygulama kodunun veya cihaz firmware'inin hatasız olduğunu göstermez. Özel repo bulgularını mevcut yetkili bakım kanalında; sürüm, dosya/satır, tekrar üretim ve etkiyle bildirin. Cihaz kimlikleri veya kişisel profil içerikleri gerekmiyorsa paylaşılmamalıdır.
