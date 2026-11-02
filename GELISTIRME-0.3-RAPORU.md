# Muvv 0.3 geliştirme ve sanal kabul raporu

11 Ekim 2026. İndirilen iki özel repo ZIP'i üzerinde sürdürülen geliştirme. Bu tur, 0.2 kaynaklarından devam eder; orijinal dosyalar ve önceki teslimler korunur.

## Sonuç

Sıraya alınmış arayüz komutunun yeniden bağlanan cihaza yazılması ve geçici meşgul yanıtının ekrandaki bilinen ayarları silmesi testte tekrar üretildi. İkisi düzeltildi. Kapanış kilidi, profil sayfalama ve istemci yanıt doğrulaması da geliştirildi. Cihaz protokolü, profil şeması ve mevcut CLI kullanımı korunuyor.

Kaynak sanal ortamında ve kaynak klasörü dışında kurulan wheel paketinde **159 testin 145'i geçti**. Linux/POSIX gerektiren **14 test atlandı**; başarısızlık ve hata yok. Toplamın içinde **29 gerçek Tk arayüz senaryosu** ve başlangıç deposundan korunan altı test vardır. Ek olarak temiz kurulumdan 200 yeniden bağlantı, 2.000 parçalı mesaj ve sekiz üreticiden 800 işlem çalıştırıldı. Fiziksel HID cihazı açılmadı.

Bu, Windows / Python 3.12.10 üzerinde yerel kabul sonucudur. Hedef Linux'ta UID, izin, flock, udev/systemd ve gerçek fare kabulü henüz yapılmadı. GitHub CI tanımı güncellendi; uzakta çalıştırılmadı veya yayın yapılmadı.

## Düzeltilen davranışlar

| Konu | Önceki davranış | 0.3 davranışı ve kanıt |
|---|---|---|
| Bekleyen komut ve yeniden bağlantı | Arka plan yenilemesinin arkasındaki 500 Hz komutu, aynı yolda yeniden açılan fareye yazılıyordu. | Her bağlantı ayrı oturum. Eski oturum isteği `device_changed` ile yazmadan reddediliyor. [Önceki başarısız test](gelistirme-0.3/yeniden-baglanti-once.log), [regresyon](Muvv/test/unit/test_session_safety.py). |
| Aynı cihaz ID'sinde oturum değişimi | Dışarıdan yeniden bağlantı yapıldığında uygulanmamış eski girişler korunuyordu. | Oturum değişikliği tespit edilip önceki girişler temizleniyor. Aynı oturumdaki normal yenileme taslakları koruyor. [Arayüz testleri](Muvv/test/unit/test_gui.py). |
| Geçici meşgul cihaz | Bilgi alınamayınca 1000 Hz değeri “Bilinmiyor” oluyor, son durum siliniyordu. | Son değerler korunuyor; bilgi tekrar alınana kadar yazımlar kapanıyor. Yeniden bağlantı düğmesi kullanılabilir. [Önceki başarısız test](gelistirme-0.3/arayuz-once.log). |
| Servis kapanışı | IPC kapanışı, USB/tarama bitmeden süreç kilidini bırakabiliyordu. | Manager dinleyiciyi kapatıyor; kilit USB, tarama ve IPC işçileri bitince bırakılıyor. Bloke kaynak varken aynı manager yeniden başlatılamıyor. Windows'ta sıralama ve tutma test edildi; gerçek Linux flock testi eklendi ve burada atlandı. [Yaşam döngüsü testleri](Muvv/test/unit/test_lifecycle.py), [Linux testleri](Muvv/test/unit/test_linux_ipc.py). |
| Sonraki profil sayfası | Sayfa bağlantı hatası ilk cihaz bilgilerini de kullanılamaz yapıyordu. | Cihaz bilgisi korunuyor; liste eksik olarak işaretleniyor. Önceden yüklenen profil adları kaybolmuyor. [İstemci akışları](Muvv/test/unit/test_client_workflows.py). |
| Değişen profil kataloğu | Farklı dosya adları kataloglarına ait sayfalar birleştirilebiliyordu. | Dosya adları için katalog kimliği var. Değişen katalogda sonraki sayfa birleştirilmiyor, yenileme uyarısı gösteriliyor. Bu kontrol dosya içeriklerini dondurmaz. |
| Bozuk servis yanıtı | Eksik alan veya bozuk DPI listesi ekranda yarım güncelleme ve callback hatası üretebiliyordu. | Cihaz, oturum, ayar, efekt, profil ve sayfa biçimi ekrana ulaşmadan doğrulanıyor. Yanıt nesnesi kopyalanıyor; istemcinin asıl nesnesi değişmiyor. [İstemci](Muvv/ui_client.py). |
| Profil açılış yarışı | Profil deposunda lstat sonrası dosyanın FIFO'ya dönüşmesi bloklayan açılışa yol açabilirdi. | Desteklenen platformda nonblocking/no-follow açılış ve fstat kontrolü birlikte kullanılıyor. Gerçek FIFO yarışı testi Linux'a eklendi; Windows'ta çalıştırıldığı iddia edilmiyor. |
| Animasyon ve bağlantı bilgisi | Geçici render hatası iyileşse de eski hata kalıyor; kapalı bağlantı “hazır” görünebiliyordu. | Başarılı karede render hatası temizleniyor; kapalı bağlantı ve güncel render hatası doğru gösteriliyor. |

Oturum kontrolü yalnızca ilk çözümleme sırasında yapılmaz: komut kilidinde beklerken yeniden bağlantı olursa, kilit alındıktan sonra tekrar kontrol edilir. Aynı USB yoluna yeni runner konması ve iki eşzamanlı yeniden bağlantı isteği de test edilir. Bir istek başarılı olduğunda önceki oturumu kullanan diğer istek reddedilir.

`expected_session` isteğe bağlıdır. Arayüz otomatik gönderir; alanı göndermeyen mevcut CLI çağrıları çalışır. Kimlik, bir bağlantı neslinin etiketidir; cihazın kriptografik kimliği veya kimlik doğrulama anahtarı değildir. Profil JSON sürümü 1 ve Rival 3 Gen 2'nin 64 bayt raporları korunur.

## Test ve kurulum kanıtı

| Kontrol | Sonuç | Kayıt |
|---|---|---|
| Kaynak sanal ortamı | 159 toplam, 145 geçti, 14 atlandı; 0 hata/başarısızlık | [JSON](gelistirme-0.3/test-sonuclari.json), [ayrıntılı günlük](gelistirme-0.3/test-kaydi.log) |
| Temiz wheel kurulumu | Aynı 159/145/14 sonuç; modüller ayrı sanal ortamın site-packages dizininden yüklendi | [Wheel testleri](gelistirme-0.3/wheel-test-sonuclari.json), [günlük](gelistirme-0.3/wheel-test-kaydi.log) |
| Paket akışı | 13 kontrol: bağımlılıksız import/CLI, eksik GUI bağımlılığında kontrollü çıkış, hashli bağımlılık kurulumu, pip check, gerçek Tk demo, tüm testler ve sanal senaryolar | [Kurulum kaydı](gelistirme-0.3/paket-dogrulama.json) |
| Parçalı IPC | 2.000 socketpair turu: 667 geçerli, 1.333 hatalı istek reddedildi; sekiz istemci hakkı geri kazanıldı | [Sanal senaryolar](gelistirme-0.3/sanal-senaryolar.json) |
| Eşzamanlı raporlar | Sekiz üretici, 800 işlem, 2.400 rapor; işlem paketleri birbirine karışmadı | Aynı sanal kayıt |
| Yeniden bağlantı ve profiller | 200 farklı oturum; 200 eski istek engellendi; 200 dosya aktarımı, 400 ad değişikliği; eski handle'lar kapandı | Aynı sanal kayıt |
| USB kesilmesi | Dört rapor konumu; yanlış başarı ve hatadan sonra yazım yok; yeni bağlantıda eski ayarlar bilinmiyor | Aynı sanal kayıt |
| İşçi temizliği | Senaryo sonunda yeni Muvv işçisi kalmadı | Aynı sanal kayıt |
| Gerçek Tk görsel kontrolü | Dört sekme, dar pencere ve altı ekran görüntüsü; callback hatası yok | [Smoke kaydı](gelistirme-0.3/arayuz-smoke.json), [profiller](gelistirme-0.3/arayuz/profiles.png), [dar pencere](gelistirme-0.3/arayuz/minimum-size.png) |
| Ruff | Kod denetimi ve biçim kontrolü geçti | [Denetim](gelistirme-0.3/ruff-check.log), [biçim](gelistirme-0.3/ruff-format.log) |
| Bağımlılıklar | Dört kilitli çalışma zamanı paketi ve 38 yayımlanmış geliştirme paketi tarandı; bilinen açık bulunmadı | [Çalışma zamanı](gelistirme-0.3/bagimlilik-denetimi.json), [geliştirme](gelistirme-0.3/gelistirme-bagimlilik-denetimi.json) |
| Kaynak ve arşiv koruması | İki orijinal ZIP/45 dosya ile 0.1 ve iki 0.2 tesliminin hashleri değişmedi; 63 Python dosyası 3.10 söz dizimiyle ayrıştırıldı; wheel'deki 34 modül kaynakla eşleşti | [Kaynak denetimi](gelistirme-0.3/kaynak-dogrulama.json) |
| Başlangıca göre yamalar | İki özgün başlangıca uygulandı; uygulama 82, notlar 12 dosya olarak byte düzeyinde eşleşti | [Yama kabulü](gelistirme-0.3/yama-dogrulama.json) |

Geliştirme ortamında toplam 39 paket listelenir. Özel yerel `muvv 0.3.0` PyPI'de bulunmadığı için bağımlılık denetiminden atlanır; 39 paketin tamamının tarandığı söylenmez. Kaynak kod testleri bu rapordaki ayrı kabul kanıtıdır. Tarama sonucunun bilinen açık bulmaması, uygulamanın veya firmware'in hatasız olduğu anlamına gelmez.

Çekirdek coverage ölçümü: statement **%84,65** (2168/2561), branch **%74,88** (647/864), birleşik **%82,19**. GUI modülü bu ölçüme dahil değildir; gerçek Tk akışları ayrı testlenir. [Ham coverage](gelistirme-0.3/kapsama.json) atlanan/ulaşılmayan satırları da içerir. Python 3.10 söz dizimi kontrolü, bu makinede gerçek 3.10/3.14 çalıştırma kanıtı değildir.

Sanal uzun senaryolar kurulan wheel'den ve ayrı klasöre kopyalanan test araçlarından çalıştırıldı; kaynak klasöründeki uygulama modülleri kullanılmadı. HID modülü engellenerek yalnızca bellek içi taşıma kullanıldı. Windows socketpair turu, Linux Unix socket yolu/UID/izin kabulü olarak sunulmaz.

## Çalıştırma

Projenin kendi sanal ortamında:

```powershell
.\.venv\Scripts\python.exe tools\check.py --json test-results.json
.\.venv\Scripts\python.exe tools\simulation_check.py --cycles 200 --json simulation-results.json
.\.venv\Scripts\muvv-gui.exe --demo
```

Kurulum ve Linux kullanım ayrıntısı [README](Muvv/README.md), oturum alanları [IPC sözleşmesi](Muvv/docs/IPC.md), fiziksel ölçüm adımları [donanım kabul listesinde](Muvv/docs/HARDWARE-ACCEPTANCE.md).

## Bundan sonra yapılacaklar

1. Hedef Linux dağıtımında atlanan 14 kontrolü ve CI'nin Python 3.10/3.12/3.14 koşularını gerçekten çalıştırın. Bloke işçi varken ikinci servis kilidi ve FIFO açılış yarışına yeni testler eklendi.
2. Şirkette kullanılan Rival 3 Gen 2 Wired üzerinde DPI, Hz, tuş, üç RGB bölgesi, hotplug ve güç döngüsünden sonra kalıcı kaydı ölçün. Sanal HID gerçek sensör/firmware davranışını doğrulamaz.
3. Özel reponun güncel haline ayrı inceleme dalında yamaları uygulayın. Elimizdeki başlangıç ZIP'lerinin sonraki değişikliklerini veya commit geçmişini göremiyoruz.
4. Ürün gereksinimine göre otomatik profil seçimi, sistem tepsisi ve ek cihaz desteğini ayrı kabul kriterleriyle ele alın. Otomatik profil uygulama, başlangıçta mevcut ayarları değiştireceği için açık ürün kararı gerektirir.

## Korunacak sınırlar

- USB sonucu belirsizse komutu otomatik tekrarlamayın; bilgileri ve bağlantıyı yenileyin. Başarılı yazım sonrası bilgi yenileme hatası tekrar yazma gerekçesi değildir.
- Fareden okunamayan ayarları bilinen değer veya gerçek yedek olarak göstermeyin. Varsayılan başlangıç ve kalıcı kayıt kullanıcı seçimi olarak kalsın.
- Makro, başka marka/model ve Windows cihaz servisini desteklenmiş ilan etmeyin. Servisi root veya herkese açık socket/USB izinleriyle çalıştırmayın.
- Native açma/yazma/kapama çağrısını Python'un güvenle zorla kesebildiğini varsaymayın. Kapanış tamamlanamadığında aynı manager ile temizliği yeniden deneyin; bloke kaynağı ikinci yazıcıyla aşmayın.
- Orijinal ZIP, yayımlanmış teslim ve kişisel geliştirici notunu değiştirmeyin; gerçek profil/secrets dosyalarını inceleme paketine eklemeyin. Lisans ve paylaşım koşullarını repo sahibiyle netleştirin.

## Teslim

Yeni teslim ayrı `Muvv-0.3.0-20261011` klasöründe hazırlanır. Kaynak ZIP'i iki güncel depodaki 94 dosyayı; inceleme ZIP'i bunları, raporu, test kayıtlarını, görselleri, iki yamayı ve kurulum paketlerini taşır. Önceki 0.1/0.2 dosyaları yeniden yazılmaz. İç/dış manifest, CRC, bayt karşılaştırması ve arşiv içi belge bağlantıları son teslim kontrolünde doğrulanır.

Yerel kanıt yardımcıları bu Windows çalışma alanının yollarını kullanır; taşınabilir test araçları proje içindeki `tools/check.py` ve `tools/simulation_check.py` dosyalarıdır. Yeni sürüm yerel geliştirme teslimidir; canlı yayın veya şirketin fiziksel kabulü tamamlanmış sayılmaz.
