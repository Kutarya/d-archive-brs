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

USB kontrol kuyruğu 64 işlemle sınırlıdır. Bir işlemde en fazla 16 rapor bulunur; bir işlem başladıktan sonra raporları arasına RGB yazımı girmez. Kullanıcı komutu cihaz kilidini en fazla bir saniye, USB sonucunu 1,5 saniye bekler. Bekleme dolduğunda sonuç belirsiz olarak bildirilir.

RGB için eski kareler biriktirilmez. Yeni açık renk işlemi, bekleyen eski RGB karesini kaldırır. İşlemin tamamlandığı ancak USB yazımı başarılı döndüğünde bildirilir; firmware'den ayar doğrulaması yapılmaz. [HIDAPI yazma sözleşmesi](https://libusb.info/hidapi/group__API.html).

Native HID sürücüsü bir yazma veya açma çağrısında kalırsa Python o çağrıyı zorla durduramaz. Kapanışta USB işçisi için bekleme sınırı vardır; bloke olmuş yazıcı yerine ikinci yazıcı açılmaz. İşçi çağrı döndüğünde handle'ı kapatır. Bu durum fiziksel cihazda ve hedef Linux dağıtımında ayrıca denenmelidir.

VID/PID bir cihaz eşleştirme bilgisidir, kriptografik cihaz kimliği değildir. Udev kuralı desteklenen modeli daraltır; uygulama HID arayüzü 3'ü seçer.

## Profil ve eklentiler

Profiller kullanıcıya ait 0700 dizinde, 0600 JSON dosyalarında tutulur. Dosya adı profil adının SHA-256 değerinden üretilir; ad yol olarak kullanılmaz. Dosya boyutu 32 KiB, profil sayısı 128 ile sınırlıdır. Kayıt önce geçici dosyaya yazılır ve atomik dosya işlemiyle tamamlanır.

Profil yalnızca oturumda bilinen alanları kaydeder. Başlangıç varsayılanları kullanıcının gerçek fare ayarları olarak gösterilmez. Bilinmeyen alanlar uygulanmaz. USB işlemi yarıda kalırsa donanım geri alınmış sayılmaz.

Sürücü ve efekt kayıtları açık modül listesi kullanır. Klasöre bırakılmış herhangi bir Python dosyası kendiliğinden import edilmez. `register_driver` / `register_effect` ile eklenen kod uygulama yetkisiyle çalışır; yeni eklenti güvenilen kaynak kodudur.

## Bağımlılıklar ve bildirim

Çalışma zamanı paketleri `requirements-lock.txt` ile sürüm ve hash olarak sabitlenir. Bilinen açık taraması:

```bash
pip-audit --require-hashes --disable-pip -r requirements-lock.txt
```

Bu tarama uygulama kodunun veya cihaz firmware'inin hatasız olduğunu göstermez. Özel repo bulgularını mevcut yetkili bakım kanalında; sürüm, dosya/satır, tekrar üretim ve etkiyle bildirin. Cihaz kimlikleri veya kişisel profil içerikleri gerekmiyorsa paylaşılmamalıdır.
