# Muvv geliştirme raporu

11 Ekim 2026 · Yerel geliştirme sürümü 0.1.0

Muvv'un yerel erişim, komut doğrulama, USB işlem sırası ve durum yönetimindeki tespit edilmiş sorunları düzeltildi. Aynı yapı üzerine masaüstü arayüzü, canlı efekt düzenleme, spektrum efekti, beş DPI kademesi yönetimi ve isimli bilgisayar profilleri eklendi. Kurulabilir wheel ve kaynak paketi oluşturuldu; temiz bir sanal ortamda ayrıca denendi.

Son otomatik çalıştırmada **89 testin 78'i geçti, 11'i Linux gerektirdiği için atlandı; hata ve başarısız test yok.** Gerçek Linux servis/izin kabulü ile fiziksel fare kabulü bekliyor. Bu iki kabul tamamlanmadan sürümün sahada doğrulandığı söylenemez.

## 1. Kaynak ve çalışma sınırı

Başlangıç iki özel repo ZIP'idir. GitHub erişimi ve commit geçmişi kullanılmadı. ZIP yorumlarında bulunan kimlikler başlangıç referansıdır; repo geçmişi olarak değerlendirilmez:

| Kaynak | ZIP içindeki dosya | Referans |
| --- | ---: | --- |
| Muvv-main.zip | 34 | b3466453ba3f8bdb697cd182832dae22318dfbf3 |
| Muvv_development_environment-main.zip | 11 | addec62756896737c2ea23e85070e575a28bc8f6 |

Güncel uygulama `D:\BRS\Muvv`, geliştirme notları `D:\BRS\Muvv_development_environment` içindedir. Orijinal ZIP'ler ve `inceleme/kaynak` altındaki 45 kaynak dosyanın hashleri tekrar kontrol edildi; değişiklik yok. Teslime alınan iki güncel depoda toplam 84 dosya vardır. Sanal ortamlar, Git iç dosyaları, önbellekler ve başlangıçta Git tarafından dışlanan kişisel not dosyası kaynak paketine alınmadı.

Mevcut sınıf ve klasör ayrımı korundu: sürücüler, Vitray efektleri, cihaz yöneticisi, CLI. Rival 3 Gen 2'nin 64 baytlık paketleri ve DPI/tuş tabloları temel alındı. Değişiklikler yerel Git farkı ve iki ayrı yama üzerinden incelenebilir. Başka birinin kimliğiyle commit, uzak repo değişikliği veya yayın yapılmadı.

İlk incelemenin ayrıntıları [inceleme raporunda](inceleme/MUVV-INCELEME-RAPORU.md), bu sürümün kullanımı [uygulama README'sinde](Muvv/README.md) bulunur.

## 2. Güvenlik bulgularının durumu

| Bulgu | Uygulanan değişiklik | Doğrulama ve kalan sınır |
| --- | --- | --- |
| G01 — Soket erişimi ve eş kimliği | Kullanıcıya ait özel dizin, 0700/0600 izinleri, iki uçta UID kontrolü, güvenli kilit ve mevcut soket denetimi | Kaynak ve hata yolları kontrol edildi. Gerçek Unix soketi ve kullanıcı ayrımı Linux kabulünde çalıştırılmalı. |
| G02 — Sınırsız istemci ve bekleme | En fazla 8 istemci, başlık/gövde için toplam süre, 16 KiB istek ve 64 KiB yanıt sınırı, kapanışta istemcileri kapatma | Parçalı mesaj, bozuk JSON, büyük yanıt ve süre sınırı donanımsız testlerde geçti. Gerçek sunucu kapasite testleri Linux'a ayrıldı. |
| G03 — Efekt iç alanlarına yazma | Her efektin açık parametre listesi, katı değer sınırları ve atomik güncelleme | Yöntem/özel alan değiştirme, geçersiz sayı ve hatalı renk reddediliyor. Önceki efekt korunuyor. |
| G04 — Reddedilen tuş ayarının RAM'i bozması | Önce ayrı kopyada tam doğrulama, en az bir sol tık kuralı, başarılı yazımdan sonra durum güncelleme | Reddedilen atamadan sonra geçerli işlem çalışıyor. Geçersiz tuş/HID kodu paket üretmiyor. |
| G05 — Kuyruğa kabulün başarı sayılması | Future ile USB yazma sonucunu bekleme; eksik/başarısız yazımı istemciye hata olarak dönme | Sıfır, kısa ve hatalı yazım testleri geçti. USB teslimi firmware doğrulaması olarak gösterilmiyor. |
| G06 — Sınırsız kuyruk ve işçi ömrü | 64 kontrol işlemi sınırı, yalnızca son RGB kareyi tutma, kapanış sinyali, sınırlı işçi beklemesi ve bloke olmuş işçiyi takip etme | Yavaş yazım, kuyruk dolması ve kapanış testleri geçti. Native HID çağrısı Python tarafından zorla kesilemiyor. |
| G07 — Ayar/kayıt işlemlerinin karışması | Paket grupları tek USB işleminde; komut ve render ortak kilidi; eski bekleyen RGB karesini kaldırma | Tuş ayarı ve kayıt arasına başka paket girmiyor. Yarım USB işleminden sonra belirsiz durum bildiriliyor. |
| G08 — Gevşek şema ve capability kontrolü | Boolean/tam sayı ayrımı, sonlu sayı, tam RGB biçimi, bilinen komut/alanlar ve destek denetimi | Geçersiz istek yazmadan reddediliyor; eksik capability desteğe izin vermiyor. |
| G09 — Kendiliğinden Python importu | Sürücü ve efektlerin açık kayıt listesine geçiş; kimlik çakışmasını reddetme | Klasöre dosya bırakmak tek başına kod yüklemiyor. Bilerek eklenen eklenti hâlâ güvenilen uygulama kodudur. |
| G10 — Bağımlılık ve paketleme | Sabit sürümler, çalışma zamanı hash kilidi, paket girişleri, wheel/sdist, CI tanımı ve tarama | 4 çalışma zamanı ve 38 geliştirme ortamı paketi için son taramada bilinen açık bulunmadı. Bu sonuç uygulamanın tamamı için güvenlik garantisi değildir. |

Bu uygulama ağdan yönetilen bir web servisi değildir. Ayrı kullanıcılar arasındaki yerel erişimi sınırlar; aynı kullanıcı hesabının ele geçirilmesine veya root erişimine karşı bir sandbox sağlamaz. G01 ve G09'un etkisi dağıtım izinlerine bağlıdır; ilk incelemede uzaktan kod çalıştırma kanıtı bulunmamıştı.

## 3. İşlev ve güvenilirlik düzeltmeleri

**Cihaz ayarları korunuyor.** Bağlantı ve normal kapanış sırasında kendiliğinden siyah RGB paketi gönderilmiyor. Cihazdan okunamayan DPI/tuş değerleri başlangıç varsayılanlarıyla biliniyormuş gibi gösterilmiyor. İlk kısmi ayar açık başlatma ister; tam beş DPI değeri veya tam tuş düzeni verilebilir. Fareden geri okuma uygulanmadığı için gerçek eski ayarın otomatik yedeği yoktur.

**Bağlantı durumu gerçeğe daha yakın.** Açılamayan cihaz aktif listede tutulmuyor; tekrar deneme aralığı artıyor. Aynı isim birden fazla fareye uyarsa açık cihaz kimliği isteniyor. Yeniden bağlanma ile tarama aynı anda ikinci sürücü açmıyor. Kapanış sırasında tamamlanan bağlantının yazıcısı bloke kalırsa ayrı takip ediliyor; aynı yol için ikinci yazıcı başlatılmıyor.

**Efekt davranışı tutarlı.** Sabit efektin adı ve varsayılan rengi düzeltildi. Dalga hızının iki kez uygulanması ve sıfır dalga boyu giderildi. Monoton saat kullanılıyor. Canlı hız değişimi efekti yeniden kurmuyor; aynı efekt örneği ve zaman fazı korunuyor. Geçersiz yeni efekt veya USB hatası mevcut katmanı silmiyor.

**İşlem sonucu ayrıldı.** Kuyruk kabulü, başarılı USB yazımı ve cihaz belleğinde kalıcılık aynı şey olarak gösterilmiyor. Bir grup raporun yarısı yazılıp kalanı başarısız olursa RAM'de işlem tamamlandı denmiyor. Donanım durumu belirsiz işaretleniyor ve yeniden bağlantı isteniyor. Çok raporlu işlem fiziksel cihaz açısından geri alınabilir bir veritabanı işlemi değildir.

**Tuş düzeni doğrulanıyor.** Bilinmeyen buton, hatalı HID usage ve sol tık bırakmayan tam düzen reddediliyor. Klavye ataması ile fare tuş işlevleri ayrı doğrulanıyor. Ayar ve isteğe bağlı kayıt raporu bölünmeden gönderiliyor.

**Arayüz iş kuyruğu sınırlı.** USB/IPC işlemi sürerken yeni kullanıcı işi eklenmiyor. Sonuçlar ana Tk döngüsünde işleniyor. Pencere zamanlayıcıları kapanışta kaldırılıyor; eski Tk kaynaklarının I/O işçisi içinde temizlenmesiyle oluşan aralıklı bekleme düzeltildi. Hatalar durum alanında görünür kalıyor.

## 4. Eklenen ürün özellikleri

Masaüstü arayüzü dört sekmede çalışır: aydınlatma, DPI ve hız, tuşlar, profiller. Aydınlatmada üç bölgenin önizlemesi, renk seçimi, hız, dalga yönü ve spektrum parlaklığı vardır. DPI bölümünde beş değer ve etkin kademe birlikte uygulanır. Tuş düzeni okunabilir isimlerle gösterilir; varsayılan başlatma ve fare belleğine kayıt açık seçimdir.

İsimli bilgisayar profilleri sürümlü JSON olarak tutulur. Profil adı dosya yolu olarak kullanılmaz; SHA-256 dosya adına dönüşür. Model, ayarlar ve efekt USB işleminden önce doğrulanır. Kayıt atomik dosya işlemiyle tamamlanır; bozuk, aşırı büyük veya uygunsuz bağlantılı dosya kabul edilmez. Profiller yalnızca bilinen alanları taşır; eksik alanlar uygulanmaz.

CLI'ye durum, efekt listesi, canlı efekt güncelleme, beş DPI değeri, varsayılan tuşlara dönüş, yeniden bağlantı ve profil komutları eklendi. Çıkış kodları betik kullanımına uygundur: başarı 0, servis/cihaz hatası 1, ayrıştırma hatası 2. USB kullanan servis Linux'a özgüdür; Windows'ta donanımsız masaüstü demo çalışır.

Demo gerçek HID açmaz ve kullanıcı profillerini kullanmaz. Geçici profiller kapanışta kaldırılır. Ekran görüntüleri bu demo oturumuna aittir; fiziksel farenin ölçüm veya kullanım kanıtı değildir.

## 5. Test ve kurulum kanıtları

| Kontrol | Sonuç |
| --- | --- |
| Otomatik testler | 89 toplam; 78 geçti, 11 atlandı, 0 hata/başarısızlık |
| Önceki çekirdek testler | 6 mevcut test korundu ve geçti |
| GUI birim testleri | Gerçek Tk bileşenleriyle 9 akış geçti |
| Masaüstü smoke | 4 sekme, efekt/DPI akışları; callback hatası yok |
| Python söz dizimi | 53 kaynak dosya Python 3.10 söz dizimi hedefiyle ayrıştırıldı |
| Ruff | 46 dosya için kontrol ve biçim denetimi geçti |
| Belgeler | Kod blokları, 10 yerel belge bağlantısı ve Git whitespace kontrolü geçti |
| Wheel / sdist | İki paket başarıyla oluşturuldu; wheel içindeki 29 Python modülü kaynakla birebir eşleşiyor |
| Temiz kurulum | Kaynak dışında yeni venv, yerel wheel, hashli bağımlılıklar ve pip check geçti |
| Paket içindeki demo | DPI değişimi ve profil kaydı geçti; HID modülü açılmadı |
| Kaynak koruma | 2 orijinal ZIP ve 45 başlangıç dosyası hashleri aynı |
| Yama kontrolü | İki yama başlangıç kaynaklarının ayrı kopyasına uygulandı; 84 güncel dosya birebir eşleşti |

Kapsama ölçümü çekirdek, sürücüler, yöneticiler, CLI, IPC, daemon ve demoyu içerir: satır kapsamı **%80,35**, dal kapsamı **%68,18**, birleşik ölçüm **%77,35**. GUI bu kapsam yüzdesinin dışında olup kendi davranış testleriyle kontrol edilmiştir. Linux'ta atlanan yollar özellikle IPC kapsamını düşürür. Yüzde tek başına donanım doğruluğu veya tüm hataların bulunması anlamına gelmez.

Sonuç dosyaları:

- [Test özeti](gelistirme-kanitlari/test-sonuclari.json) ve [ayrıntılı test kaydı](gelistirme-kanitlari/test-kaydi.log).
- [Temiz paket kurulumu](gelistirme-kanitlari/paket-dogrulama.json).
- [Kaynak ve paket bütünlüğü](gelistirme-kanitlari/kaynak-dogrulama.json).
- [Yamadan kaynak oluşturma kontrolü](gelistirme-kanitlari/yama-dogrulama.json).
- [Çalışma zamanı bağımlılık taraması](gelistirme-kanitlari/bagimlilik-denetimi.json) ve [son geliştirme ortamı taraması](gelistirme-kanitlari/gelistirme-bagimlilik-denetimi-son.json).
- [Arayüz smoke sonucu](gelistirme-kanitlari/arayuz-smoke.json) ve [arayüz görüntüleri](gelistirme-kanitlari/arayuz/).

İlk geliştirme ortamı taraması venv içindeki eski pip sürümünde bilinen açıklar bildirdi. Yalnızca proje sanal ortamındaki pip 26.2.1'e yükseltildi; son tarama temiz. Sistem Python'u ve işletim sistemi ayarları değiştirilmedi. Özel kaynak veya profil içerikleri bağımlılık denetim servisine gönderilmedi; tarama yayımlanmış paket adları/sürümleri üzerindedir.

GitHub Actions dosyası Linux üzerinde Python 3.10/3.12/3.14 çekirdek işlerini ve ayrı Xvfb masaüstü işini tanımlar. Action referansları commit SHA ile sabitlendi. Bu çalışma sırasında uzak CI çalıştırılmadı; dosyanın varlığı başarılı CI çalışması olarak sayılmadı.

## 6. Kullanım ve geçiş

Yerel Windows demosu mevcut geliştirme ortamından şu komutla açılır:

```powershell
D:\BRS\Muvv\.venv\Scripts\muvv-gui.exe --demo
```

Hedef Linux kurulumu, udev ve kullanıcı servisi adımları [README](Muvv/README.md) ve [donanım kabul listesinde](Muvv/docs/HARDWARE-ACCEPTANCE.md) bulunur. Hash kilidiyle kurulum önerilir; kısa editable kurulum yolu tüm geçişli bağımlılıkları hash ile sabitlemez.

Önemli geçiş noktaları:

- CLI komut adları korunmuştur; IPC artık 4 bayt uzunluk başlıklı mesaj kullanır. CLI ve servis aynı sürümden güncellenmelidir.
- Eski `set-color` JSON `hex` alanı desteklenir. Aynı istekte hem `hex` hem `color` kabul edilmez.
- Sayısal DPI kademesi ile sayısal cihaz sırasını karıştırmamak için `-d` kullanılır. CLI kademesi 0–4, GUI kademesi 1–5'tir.
- İlk kısmi DPI/tuş değişikliği bilinmeyen eski ayarın üzerine sessizce varsayılan yazmaz. `--initialize` etkisi belgelenmiştir.
- CLI tuş komutlarının eski varsayılan kayıt davranışı korunur. Geçici işlem için `--no-persist`; GUI'de ayrı kayıt kutusu kullanılır.
- Eklenti dosyasını klasöre kopyalamak artık otomatik yüklemez. Güvenilen başlangıç kodu kayıt işlevini çağırmalıdır.
- Yeni bağlantıda donanımdan okunamayan ayarlar yeniden bilinmiyor olur. Önceki profil kendiliğinden uygulanmaz.

## 7. Bundan sonra yapılması gerekenler

1. Repo sahibi bu değişiklikleri özel repoda ayrı inceleme dalına alsın. Başlangıç ZIP'iyle uyumsuz yeni uzak değişiklikler varsa yama doğrudan zorlanmadan birleştirilsin. Kaynak paketinde sahip/commit geçmişi varsayımı yoktur.
2. Hedef Linux dağıtımında otomatik testler çalıştırılsın. Atlanan 11 izin/soket kontrolünün sonucu, Python sürümü ve backend ile kaydedilsin. GUI için Tk/Xvfb veya gerçek masaüstü kullanılsın.
3. Udev erişimi ve kullanıcı systemd servisi normal masaüstü hesabında denensin. Farklı kullanıcı, ikinci servis, bozuk istek, boşta istemci ve kapanış senaryoları doğrulansın.
4. Gerçek Rival 3 Gen 2 üzerinde RGB, beş DPI değeri, yoklama hızı ve tuş davranışı ölçülsün. Ayar sırasında çıkarma, tekrar bağlantı ve yazıcı kapanışı kaydedilsin.
5. Kalıcı kayıt ayrı denenip güç döngüsünden sonra kontrol edilsin. Yazılım animasyonunun firmware animasyonu olmadığı kabul ölçütüne yazılsın. Eski ayarlar okunamadığı için cihaz sahibinin kullanacağı tam değerler önceden alınsın.
6. Bu kabulden sonra otomatik profil yükleme politikasına ve sistem tepsisine karar verilsin. Ek cihazlar kendi protokolü ve fiziksel kabulüyle ayrı sürücü olarak eklensin.
7. Yayın düşünülüyorsa repo sahibi lisans ve protokol kaynaklarının dağıtım koşullarını netleştirsin. Başlangıçta lisans dosyası yoktu; bu çalışmada hayali lisans veya sahiplik bilgisi eklenmedi.

## 8. Kaçınılması gerekenler

- Tüm hidraw cihazlarına `0666` vermek, root servisini kalıcı çözüm yapmak veya uygulamaya genel TCP yönetim portu eklemek.
- Bilinmeyen fare ayarlarını gerçek yedek diye sunmak; her bağlantıda kullanıcıya sormadan tam varsayılan profil yazmak.
- USB yazımı tamamlanmadan başarı bildirmek; yarım işlemi donanım geri alınmış gibi göstermek.
- Aynı cihaz için ikinci yazıcı açmak, sınırsız iş/kare biriktirmek veya native bloklanmayı yeni thread açarak çözmeye çalışmak.
- Geçersiz komutu kabul etmek için boolean/string değerleri sayıya sessizce çevirmek; parametre adı üzerinden yöntem veya iç alan değiştirmek.
- Genel makro/evdev veya bütün fare markaları desteğini hazır saymak. Bunlar uygulanmış özellik değildir.
- Demo, sahte HID veya CI sonucunu fiziksel sensör/firmware kabulü olarak sunmak; atlanan testi geçti olarak işaretlemek.
- Özel kaynakları, kişisel profil içeriklerini veya lisans koşulları belirlenmemiş paketleri izin olmadan yayımlamak.

## 9. Şirket incelemesinde gösterilebilecek çalışma

Kısa bir inceleme, demo üzerinden efekt/DPI/profil akışını; kod üzerinden geçersiz girdinin durum değiştirmediğini; testler üzerinden kısa yazım ve eşzamanlı kayıt hatalarının yakalandığını gösterebilir. Ardından temiz wheel kurulum kaydı ve iki yama açılabilir. Her değişiklik için sorun, düzeltilen davranış ve test kanıtı görülebilir.

Teknik sunumda üç sınır net tutulmalı: USB yazma sonucu cihazdan geri okuma değildir; bilgisayar profili eski fare ayarının yedeği değildir; Linux ve gerçek cihaz kabulü henüz yapılmamıştır. Bu sürüm, inceleme ve bu kabul çalışmalarına hazır yerel geliştirme teslimidir.
