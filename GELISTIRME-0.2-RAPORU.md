# Muvv 0.2.0 geliştirme ve kabul raporu

11 Ekim 2026. İki özel repo ZIP'i üzerinden yerel geliştirme; Windows / Python 3.12.10.

## Sonuç

Mevcut uygulama 0.2.0 sürümüne ilerletildi. Cihaz yaşam döngüsünde, USB işlemlerinin hata davranışında, profil deposunda ve masaüstü akışlarında yeni düzeltmeler yapıldı. Profil aktarımı, bağımsız RGB renkleri, fare işlevi seçimi ve ortam tanısı eklendi. Önceki 0.1 teslimi, iki orijinal ZIP ve 45 başlangıç dosyası hashleriyle korundu.

Yerel otomatik kabul: **134 test; 122 geçti, 12 Linux/POSIX testi atlandı; başarısızlık ve hata yok.** Bu toplamda gerçek Tk bileşenleriyle çalışan 23 arayüz testi var. Son arayüz düzenlemesinden sonra bu 23 test ayrıca yeniden geçti. Wheel kaynak dışında temiz sanal ortama kuruldu; CLI, GUI ve yeni profil/cihaz akışları doğrulandı. Test taşıması bellektedir; fiziksel USB cihazı açılmadı.

Linux soket/izin, udev/systemd ve gerçek fare kabulü halen bekliyor. Bu rapor üretim ortamının veya firmware davranışının doğrulandığı iddiasını taşımıyor.

## İki depoda ne var?

`Muvv` çalıştırılabilir Python uygulamasıdır. Mevcut sürücü yalnızca **SteelSeries Rival 3 Gen 2 Wired**, `1038:1870`, HID arayüzü 3 için tanımlıdır. DPI 200–8500 arasında 100'lük adımlarla; beş kademe, 125/250/500/1000 Hz, sekiz tuş/kaydırma ataması ve üç RGB bölgesi yönetilir. HID raporları 64 bayt olarak korunur.

`Muvv_development_environment` ayrı bir uygulama değildir. Protokol referansı, geliştirme ortamı, mimari ve ilerleme notlarını tutar. Notlar güncel kaynakla eşleştirildi; tasarlanan özelliklerle uygulanmış özellikler ayrıldı.

Veri yolu CLI/GUI → yerel IPC → DeviceManager → DeviceRunner → sürücüdür. Vitray, Layer ve ZoneMap donanımdan bağımsız ışık karelerini üretir. Sürücüde tek USB yazıcısı bulunur. Profiller kullanıcı bilgisayarında doğrulanmış JSON olarak saklanır. Web servisi, bulut, hesap sistemi veya TCP yönetimi bulunmaz.

İlk dosya analizi ve bulgu envanteri [inceleme raporunda](inceleme/MUVV-INCELEME-RAPORU.md), dosya rolleri [dosya haritasında](inceleme/DOSYA-HARITASI.md) bulunur. Kodun temel yapısı korunarak ilerletildi; farklı bir mimariyle baştan yazılmadı.

## Bu turda düzeltilen hatalar

| Sorun ve etkisi | 0.2 davranışı | Kabul kanıtı |
| --- | --- | --- |
| Runner kapanışı komut kilidinde süresiz bekleyebiliyordu. | Render, kilit ve USB kapanışı aynı süre bütçesiyle sınırlı. | Kilit başka iş parçacığındayken 30 ms kapanış bütçesiyle dönüş testi. |
| Açma işlemi kapanış isteğinden sonra tamamlanabiliyordu. | Stop isteği tekrar kontrol ediliyor; render başlamadan cihaz kapatılıyor. | Geciktirilmiş connect ve stop yarışı. |
| USB işçisi henüz oluşmamış runner kapanmış sanılabiliyordu. | Takipten çıkarma yalnızca tam runner kapanışıyla yapılır. | Worker yokken hâlâ kilitli runner testi. |
| Kuyrukta bekleme ile başlamış USB yazımının zaman aşımı aynı bildiriliyordu. | Başlamamış Future iptal edilir; başlamış çağrı `operation_uncertain` olur. | İptal edilen paketin hiç yazılmaması ve bağlantının belirsiz sayılmaması testi. |
| USB hatasından sonra başka bekleyen paketler devam edebilirdi. | İşçi yazımı durdurur, bekleyen Future'lara hata verir ve handle'ı kapatır. | Hata sonrasında kontrol/RGB kuyruğundan sıfır ek yazım. |
| Eski IPC istemci işçileri kapanmadan aynı servis nesnesi yeniden başlatılabilirdi. | Yeniden başlatma reddedilir. | Yaşayan eski handler ile restart testi. |
| Tek bozuk profil bütün profil listesini ve cihaz ekranını bozuyordu. | Katalog bozuk dosyayı ayrı bildirir, sağlam profiller ve cihaz kontrolü kullanılabilir. | JSON/dizin hatasına rağmen snapshot ve yoklama ayarı; GUI uyarısı. |
| Profil listesinin tamamı yanıt boyutunu aşabiliyordu; dosya taraması sınırsızdı. | En fazla 32 dosyalık sayfalar, sınırlı tarama ve 128 profil kotası. | Maksimum uzunlukta Unicode adlı 128 profil; sayfaların çerçeve limitine sığması. |
| Başarılı USB yazımından sonra ekran yenilemesi hata verirse ayar başarısız görünüyordu. | Komut sonucu korunur; yenileme sorunu ayrıca bildirilir. | Yazılmış 500 Hz ayarının başarı olarak kalması, tekrar yazım yapılmaması. |
| Otomatik yenileme kullanıcının girişini veya geç cevap yeni düzenlemeyi ezebilirdi. | DPI, hız, efekt ve bölge renkleri ayrı düzenleme sayaçları kullanır. | Arka plan okuması, işlem sırasında düzenleme ve DPI taslağı korunurken hız uygulama. |
| Yeniden bağlantıda önceki oturumun değerleri formda kalabiliyordu. | Bilinen ayarlar temizlenir; okunamayan alanlar tekrar bilinmiyor gösterilir. | Reconnect sonrası boş known state, başlangıç DPI önerisi ve bilinmeyen hız. |
| Pencere kapandıktan sonra işçi Tk callback'lerini tutabiliyordu. | Callback ana döngüde kalır; işçi token/queue kullanır. Geç sonuç kapanışta atılır. | I/O devam ederken pencere kapanışı ve sıfır geç callback. |
| JSON `1e999` taşması, yanlış efekt seçenek nesnesi ve sonlu olmayan USB gecikmesi kabul edilebilirdi. | Katı tip/sonluluk kontrolü; rapor iterable'ı 17. öğede reddedilir. | Float taşması, false/list seçenek ve sınırsız üretici negatif testleri. |

Bu düzeltmeler [sürücü](Muvv/drivers/base_mouse.py), [runner](Muvv/managers/device_runner.py), [manager](Muvv/managers/device_manager.py), [IPC](Muvv/managers/ipc_server.py), [profil deposu](Muvv/managers/profile_store.py) ve [istemci akışları](Muvv/ui_client.py) içinde uygulanmıştır.

## Kullanılabilir yeni işlevler

- Üç RGB bölgesine ayrı renk; animasyonu son kareyi koruyarak durdurma. Tam renk haritası doğrulanmadan yazım yapılmaz.
- Klavye tuşunu adıyla seçme ve fare işlevi atama. Ham HID kodu gelişmiş seçenek altında; en az bir sol tık korunur.
- Profil yeniden adlandırma; bilgisayardaki profilleri fare bağlı olmadan yönetme.
- JSON içe/dışa aktarma. Yerel dosya en fazla 32 KiB ve geçerli profil olmalıdır; yol servise gönderilmez. İçe aktarma USB yazımı yapmaz. Üzerine yazma açıkça seçilir.
- Arayüzde yaklaşık üç saniyelik cihaz yenilemesi; bağlantı/belirsizlik durumuna göre işlem düğmeleri; kaydırılabilir sekmeler.
- `muvv doctor` ile cihaz açmadan ve dosya oluşturmadan ortam kontrolü. `--version` ve paket sürümü aynı kaynaktan üretilir.

Komutlar ve kurulum [README](Muvv/README.md), API alanları ve sayfalama [IPC sözleşmesi](Muvv/docs/IPC.md), sınırlar [SECURITY](Muvv/SECURITY.md) içinde günceldir. Profil JSON şeması sürüm 1 olarak kalır; 0.1 profilleri kullanılabilir. `list-profiles` artık sayfalıdır; tüm liste için CLI'de `--all`, doğrudan IPC'de `next_offset` izlenmelidir.

Yeniden adlandırma iki dosyayı kapsayan atomik işlem değildir. Önce doğrulanmış yeni kopya, sonra eski dosyanın kaldırılması vardır. Kaldırma hatasında geri alma uygulanır; güç kesilmesi veya geri almayı da engelleyen dosya sistemi hatası iki kopya bırakabilir. Bu sınırlama gizlenmedi.

## Doğrulama

| Kontrol | Sonuç / kayıt |
| --- | --- |
| Otomatik çekirdek, CLI, profil, zamanlama ve GUI testleri | [134 testin JSON sonucu](gelistirme-0.2/test-sonuclari.json), [tam kayıt](gelistirme-0.2/test-kaydi.log) |
| Son GUI kaynağının 23 testi | [GUI test kaydı](gelistirme-0.2/gui-test-kaydi.log); geçti |
| Görünür Tk demo ve ekran kontrolü | [Demo sonucu](gelistirme-0.2/arayuz-smoke.json); callback hatası yok. Dört sekme, bölge renkleri ve 920×710 minimum pencere 125% ölçekli Windows ekranında kontrol edildi. |
| Ruff | [Lint](gelistirme-0.2/ruff-check.log) ve [biçim](gelistirme-0.2/ruff-format.log) geçti |
| Kaynak söz dizimi / dağıtım içeriği | [61 Python dosyası Python 3.10 söz dizimiyle ayrıştırıldı; 34 wheel modülü kaynağa birebir uydu](gelistirme-0.2/kaynak-dogrulama.json) |
| Test kapsamı | [Satır %83,46; dal %72,66; birleşik %80,83](gelistirme-0.2/kapsama.json). GUI bu yüzdeye dahil değil; ayrı akış testleri var. |
| Temiz wheel kurulumu | [Kaynak dışı temiz sanal ortamda 11 kontrol](gelistirme-0.2/paket-dogrulama.json); metadata, CLI, bağımlılıksız GUI hatası, hashli kurulum, pip check, DPI/profil/RGB/tuş akışları geçti |
| Çalışma zamanı güvenlik taraması | [Dört paket](gelistirme-0.2/bagimlilik-denetimi.json); bilinen açık bulunmadı |
| Geliştirme ortamı taraması | [38 public paket denetlendi, bilinen açık bulunmadı](gelistirme-0.2/gelistirme-bagimlilik-denetimi.json). Özel `muvv` paketi PyPI'de bulunmadığından atlandı; uygulama kodu bu taramayla doğrulanmış sayılmaz. |
| Orijinal ve önceki teslim korunması | Başlangıçta 34+11 dosya ve iki ZIP; 0.1 teslimindeki 10 dosya hash kontrolü geçti. [Kayıt](gelistirme-0.2/kaynak-dogrulama.json) |
| Yamaların uygulanabilirliği | [İki başlangıç kopyasına uygulanıp 80+12 güncel dosyayla byte düzeyinde eşleşti](gelistirme-0.2/yama-dogrulama.json) |

GUI görüntüleri: [aydınlatma](gelistirme-0.2/arayuz/rgb.png), [bölge renkleri](gelistirme-0.2/arayuz/rgb-zones.png), [DPI](gelistirme-0.2/arayuz/dpi.png), [tuşlar](gelistirme-0.2/arayuz/buttons.png), [profiller](gelistirme-0.2/arayuz/profiles.png), [minimum boyut](gelistirme-0.2/arayuz/minimum-size.png).

Kapsam yüzdesi, sahte HID veya demo fiziksel kabulün yerine geçmez. Yerel testler bellekteki taşımanın rapor baytlarını, sırasını ve hata davranışını ölçer. Linux CI tanımı kaynakta vardır; private GitHub'a erişilmediği için bu çalışmada uzak CI çalıştırılmadı. Yayın veya deploy yapılmadı.

## Bundan sonra ne yapmalı?

1. Değişiklikleri repo sahibinin mevcut dalına körlemesine kopyalamadan, iki özel repo için ayrı inceleme dallarında yama kontrolü yapın. ZIP sonrasında upstream değişmişse çakışmaları mevcut kodla çözün. ZIP'lerin commit geçmişi olmadığı için burada oluşturulan yerel indeks uzak geçmiş yerine geçmez.
2. Hedef Linux dağıtımında tüm 134 testi GUI bağımlılığı ve Xvfb ile çalıştırın. Windows'ta atlanan 12 testin sonucu özellikle görülmeli. Soket 0600/dizin 0700, farklı UID reddi, ikinci servis ve stale socket davranışını doğrulayın.
3. Gerçek Rival 3 Gen 2 üzerinde [donanım kabul listesini](Muvv/docs/HARDWARE-ACCEPTANCE.md) tamamlayın: DPI ve Hz ölçümü, sol tık güvenliği, tuş/modifier, RGB, yeniden takma ve güç döngüsünden sonra kalıcılık. Yazım denemeleri açık cihaz ID'si ve `--allow-write` ister.
4. Udev ve kullanıcı systemd örneğini hedef masaüstü oturumunda deneyin. Tanı komutu ortamı gösterir; ACL veya HID erişimini gerçek bağlantı olmadan kanıtlamaz.
5. Repo sahibiyle lisans ve dağıtım koşullarını netleştirin. Ardından kabul edilen sürümü şirketin mevcut bakım/yayın sürecine alın. Ek cihazlar, sistem tepsisi ve otomatik profil yükleme ayrı kapsam olarak ele alınabilir.

## Ne yapmamalı?

- Servisi root altında sürekli çalıştırmayın; cihazı veya soketi herkese `0666/0777` açmayın.
- USB zaman aşımından sonra sonucu biliniyormuş gibi kabul etmeyin ve yazma komutunu otomatik tekrar etmeyin. Önce işçinin kapanmasını ve yeniden bağlantıyı ele alın.
- Yeni bağlantıdaki başlangıç değerlerini gerçek fareden alınmış yedek olarak göstermeyin; bilinmeyen DPI/tuşları sessizce değiştirmeyin.
- Bozuk profil dosyalarını kullanıcıdan habersiz silmeyin. Sağlam profiller kullanılabilir; hatalı dosya ayrıca incelenmeli.
- Klasöre bırakılan Python dosyasını kendiliğinden çalıştıran eklenti yüklemesine dönmeyin. Yeni sürücü/efekt güvenilen kod ve kendi testleriyle kaydedilmeli.
- Rival protokolünü farklı model veya markaya kopyalayıp destek ilan etmeyin. Macro/evdev ve Windows cihaz servisi uygulanmış değildir.
- Sahte HID, statik inceleme, paket kurulumu veya demo sonucunu gerçek donanım/üretim sonucu olarak sunmayın. İşlev ve yetki sınırları ayrı kabul edilmelidir.

## Teslim

Güncel kaynaklar `D:\BRS\Muvv` ve `D:\BRS\Muvv_development_environment` içinde; güncel teslim klasörü `D:\BRS\teslim\Muvv-0.2.0-20261011-r2` olarak ayrılmıştır. Kaynak ZIP'i 92 dosyayı kapsar. İnceleme ZIP'inde bu rapor, ilk incelemenin taşınabilir kopyası, test kanıtları, ekran görüntüleri, yamalar, wheel ve kaynak dağıtımı birlikte bulunur. Her teslim dosyası SHA-256 ile kayıtlıdır. Revizyon 2'de arşiv içindeki bütün yerel Markdown bağlantıları da doğrulanır; orijinal inceleme belgeleri ve ilk paket korunur.

Wheel: `muvv-0.2.0-py3-none-any.whl`, SHA-256 `16a9421c4d5045f424db3cb00add69cb37e3280a8dbd3184990f0ba9c5221da8`.

Kaynak dağıtımı: `muvv-0.2.0.tar.gz`, SHA-256 `3f08a9a6127c1cd7685c3197ba8056385cf8339629047e1d6cedc55049d2bb2d`.

Özel kod, kullanıcı profilleri veya kaynak ZIP'leri harici servise yüklenmedi. Sanal ortam, Git iç dosyaları, önbellekler ve kişisel geliştirici notu kaynak teslimine alınmadı. Orijinal dosyalar ve 0.1 paketleri yerel koruma alanında kaldı.
