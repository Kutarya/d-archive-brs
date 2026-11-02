# Muvv 0.4 geliştirme ve doğrulama raporu

11 Ekim 2026 · Windows · Python 3.12.10

0.4 sürümü, cihaz bağlantısı değişirken, servis kapanırken ve profil listesi yenilenirken oluşan hataları giderir. 0.3'e göre 19 kaynak/not dosyası değişti; 17 test eklendi. Düzeltmelerden önce 15 başarısız senaryo kaydedildi. Son durumda kaynakta ve ayrı sanal ortama kurulan pakette **176 testin 162'si geçti; Linux/POSIX'e özgü 14 test atlandı; başarısızlık ve hata yok**. Gerçek Tk bileşenleriyle çalışan 33 arayüz senaryosu bu toplamın içindedir.

Bu sonuç yerel yazılım kabulüdür. Linux cihaz servisi, udev/systemd ve fiziksel Rival 3 Gen 2 kabulü henüz yapılmadı. Firmware'den geri okuma desteği yoktur; USB yazımı donanımda doğrulanmış ayar olarak gösterilmez.

## Proje ve kapsam

Uygulama deposu Python tabanlı fare kontrolünü içerir. `Driver` cihaz raporlarını üretir, `Runner` komutları ve animasyonu koordine eder, `Manager` bağlantıları ve profilleri yönetir. CLI ve dört sekmeli masaüstü arayüzü yerel IPC sözleşmesini kullanır. Vitray/Layer/ZoneMap yapısı RGB karelerini hesaplar. Desteklenen cihaz SteelSeries Rival 3 Gen 2 Wired, `1038:1870`, arayüz 3'tür.

İkinci depo geliştirme ortamı, protokol ve mimari notlarını tutar. Aktif çalışma, ilerleme ve mimari belgeleri 0.4 davranışıyla güncellendi. Mevcut mimari, komutlar, profil JSON şeması ve 64 bayt USB raporları korunur. Bu tur ek model, makro veya Windows cihaz servisi eklemez.

Başlangıç değerlendirmesi [ilk inceleme raporunda](inceleme/MUVV-INCELEME-RAPORU.md), dosyaların görevleri [dosya haritasında](inceleme/DOSYA-HARITASI.md) bulunur. Güncel kurulum ve kullanım [README](Muvv/README.md), sürüm değişiklikleri [CHANGELOG](Muvv/CHANGELOG.md) içindedir.

## Giderilen sorunlar

| Sorun ve etkisi | Yeni davranış | Doğrulama |
|---|---|---|
| Cihaz listesi alındıktan sonra başka cihaz bağlanınca seçim eski listede bulunmuyordu; sağlam servis yanıtı istemcide reddediliyordu. | Liste, seçim, runner referansı ve servis durumu birlikte alınır. USB beklenirken yönetici kilidi tutulmaz. | Kontrollü hotplug yarışı; seçimin listede kalması ve cihaz sayısının tutarlılığı. |
| Liste eski bağlantı oturumunu, durum yeni oturumu içerebiliyordu. | Durum yakalanan oturumla okunur. Bağlantı değişmişse geçici `device_changed` yanıtı verilir; istemci farklı oturumların birleştirilmesini reddeder. | Yeniden bağlantının liste/durum arasına sokulması; gerçek GUI'de kontrollerin kapanıp sonraki yenilemede düzelmesi. |
| `default` veya boşluk içeren gerçek ID, takma ad olarak çözülebiliyordu. | Tam ID takma adlardan önce eşleşir; ID'nin kendi boşlukları korunur. | Tam ID, varsayılan seçim ve takma ad çakışması. |
| Kapanış isteği geldiğinde başlamış çok raporlu işlem kalan paketleri gönderebiliyordu; paket arası bekleme kapanışı geciktiriyordu. | Başlamış yerel çağrı döndükten sonra kalan raporlar durur; gecikme kapanışla uyanır. Yarım işlem ve bekleyen işler hata döndürür. | Bloke ilk raporun ardından kapanış; üç rapordan yalnızca ilkine izin verilmesi; bir saniyelik beklemenin 0,2 saniyelik kapanış bütçesi içinde kesilmesi. |
| CLI iki farklı katalog sayfasını birleştirip başarı döndürebiliyor; bozuk sayfa ve tekrar eden adlar da kabul ediliyordu. | CLI ve GUI ortak sayfa doğrulamasını kullanır. Katalog değişimi, bozuk alan, tekrarlı ad ve ilerlemeyen sayfa reddedilir. | Değişen kimlik, geçersiz ikinci sayfa ve iki sayfada aynı profil adı. |
| Aynı adlı profil üzerine yazılınca dosya adları değişmediği için katalog kimliği değişmiyordu. | Kimlik dosya kimliği, boyutu, zamanları ve bağlantı/izin bilgilerini de kapsar. Okumanın başı ve sonu karşılaştırılır. | Üzerine yazma ve okuma ortasında dışarıdan dosya değişikliği. |
| Katalog bütünüyle okunamadığında arayüz önceki profil adlarını siliyordu. | Eksik liste açıkça bildirilir; son bilinen adlar ve kullanılabilir cihaz kontrolleri korunur. | Katalog hatasının gerçek Tk yenilemesine verilmesi. |
| Tarama ve cihaz açma hatası, kullanıcıya yalnızca cihaz bulunamadı olarak görünüyordu. | Hata nedeni ve kapanmakta olan eski bağlantı gösterilir. Tarama düzelince eski uyarı temizlenir. Tanı alanları görüntülemeden önce doğrulanır. | Erişim hatası, tarama hatası/iyileşmesi ve geçersiz tanı alanları. |
| Test araçlarındaki `assert` içinde çalışan kontrol ve kapatma işlemleri Python `-O` altında atlanıyordu. | Koşul kontrolleri normal çağrılar olarak çalışır; cihaz yöneticisi her durumda kapatılır. | Optimizasyon altında sanal senaryo ve gerçek arayüz araçlarının çalışması; işçi sızıntısı olmaması. |

Tekrar üretim kayıtları [ilk 10 senaryo](gelistirme-0.4/regresyon-oncesi.log), [üzerine yazma](gelistirme-0.4/katalog-oncesi.log), [tarama/erişim](gelistirme-0.4/tani-oncesi.log), [okuma yarışı](gelistirme-0.4/katalog-yarisi-oncesi.log) ve [katalog arayüzü](gelistirme-0.4/katalog-arayuz-oncesi.log) dosyalarındadır. Bu kayıtlar düzeltme öncesine aittir. Son karşılıkları [regresyon kaydı](gelistirme-0.4/regresyon-sonrasi.log) ve [tam test kaydında](gelistirme-0.4/test-kaydi.log) başarılıdır. Sayım ve 0.3'e göre dosya değişimleri [kanıt özetinde](gelistirme-0.4/kanit-ozeti.json) bulunur.

## Test ve kurulum sonucu

| Kontrol | Sonuç |
|---|---|
| Kaynak sanal ortamı | 176 test: 162 geçti, 14 atlandı, 0 hata/başarısızlık. |
| Ayrı sanal ortama kurulan wheel | Aynı 176 test ve aynı sonuç. Uygulama modülleri kaynak klasörden değil `site-packages` içinden yüklendi. |
| Gerçek Tk arayüzü | Toplamın içinde 33 senaryo; ayrıca dört sekmenin görselleri ve normal/optimizasyon modunda kullanım kontrolü. Callback hatası yok. |
| Parçalı mesajlar | 2.000 socketpair alışverişi: 667 geçerli, 1.333 hatalı mesaj reddedildi. İstemci slotları geri geldi. |
| Eşzamanlı USB simülasyonu | Sekiz üretici, 800 işlem, 2.400 rapor; işlemlerin raporları birbirine karışmadı. |
| Yeniden bağlantı | 200 ayrı oturum; 200 eski oturum komutu engellendi; 200 eski handle kapandı. |
| Profil dosyası işlemleri | 200 dosya aktarımı ve 400 yeniden adlandırma. |
| USB kesilmesi | Dört farklı rapor noktasında hata; yanlış başarı ve hatadan sonra yeni yazım yok. |
| Python optimizasyonu | Ek 20 döngülü senaryo ve arayüz kontrolü `-O` ile geçti; kalan Muvv işçisi yok. |
| Paketleme | Wheel/sdist oluşturuldu. Ayrı kurulumun 13 adımı beklenen çıkış kodlarıyla tamamlandı. GUI bağımlılığı kurulmadan demo denemesinin çıkış kodu 1 olması beklendi. |
| Kaynak ve biçim | Ruff denetimi ve 57 dosyanın biçim denetimi geçti. 64 Python dosyası 3.10 sözdizimiyle ayrıştırıldı. Bu, 3.10 çalışma zamanı testi değildir. |

Kurulu paket testleri [wheel test özetinde](gelistirme-0.4/wheel-test-sonuclari.json); her kurulum komutu ve çıktısı [paket doğrulamasında](gelistirme-0.4/paket-dogrulama.json) bulunur. Uzun senaryolar [sanal senaryo sonucunda](gelistirme-0.4/sanal-senaryolar.json), optimizasyon denemesi [ayrı kayıtta](gelistirme-0.4/optimize-senaryolar.json) yer alır. Bu testler fiziksel HID açmaz. Socketpair testi Linux eş UID, socket izinleri veya flock kabulü değildir.

Çekirdek kapsamı: 2.605 ifadenin 2.209'u (**%84,80**), 882 dalın 664'ü (**%75,28**) çalıştı. Birleşik değer **%82,39**. GUI kapsam yüzdesine dahil değildir; ayrı gerçek Tk testleriyle doğrulandı. Linux'ta çalışmayan dallar ve tüm hata yolları için tam kapsam iddiası yoktur. [Ham kapsam](gelistirme-0.4/coverage.json).

Sabit dört çalışma zamanı bağımlılığı için güncel bilinen açık taraması temizdir. Geliştirme ortamındaki yayımlanmış paketlerde de bilinen açık bulunmadı; yerel Muvv paketi PyPI'de olmadığı için o taramada atlanır. Bu sonuç uygulama ve firmware'in bütün açıklarının kapandığı anlamına gelmez. [Çalışma zamanı taraması](gelistirme-0.4/bagimlilik-denetimi.json), [geliştirme taraması](gelistirme-0.4/gelistirme-bagimlilik-denetimi.json).

Arayüzden [aydınlatma](gelistirme-0.4/arayuz/rgb.png), [RGB bölgeleri](gelistirme-0.4/arayuz/rgb-zones.png), [DPI](gelistirme-0.4/arayuz/dpi.png), [tuşlar](gelistirme-0.4/arayuz/buttons.png), [profiller](gelistirme-0.4/arayuz/profiles.png) ve [en küçük pencere](gelistirme-0.4/arayuz/minimum-size.png) görüntüleri alınmıştır. Görseller yalnızca uygulamanın demo penceresidir. Uzun sekmeler kaydırılabilir.

## Teslim ve korunan dosyalar

Yeni teslim `teslim/Muvv-0.4.0-20261011` altında ayrı oluşturulur. Kaynak ZIP'i uygulamadaki 83 dosyayı ve geliştirme notlarındaki 12 dosyayı içerir. İnceleme ZIP'i bunlara rapor, kanıt, görsel, iki yama ve kurulum paketlerini ekler. Sanal ortam, Git iç dosyaları, kişisel geliştirici notu ve kullanıcı profilleri kaynak paketine alınmaz.

Orijinal iki ZIP, 45 başlangıç dosyası ve 0.1/0.2/0.3 teslimleri SHA-256 değerleriyle kontrol edildi; değişmediler. Wheel içindeki 34 Python modülü kaynakla aynı, sdist kaynakları dosya bazında karşılaştırıldı. [Kaynak doğrulaması](gelistirme-0.4/kaynak-dogrulama.json).

Yamalar orijinal ZIP başlangıcına göredir; 0.3 üzerine uygulanacak artımlı yama değildir. Başlangıç kopyalarına `git apply --check` ve `git apply` uygulanıp 83 + 12 dosya birebir karşılaştırıldı. Repo sahibinin güncel özel kaynaklarıyla birleşim henüz denenmedi; ZIP'ler commit geçmişi sağlamaz. [Yama doğrulaması](gelistirme-0.4/yama-dogrulama.json).

## Bundan sonra yapılacaklar

1. Ayrı bir hedef Linux test kullanıcısında mevcut testleri çalıştır; Windows'ta atlanan 14 kontrolü gerçekten yürüt. Kullanıcı/izin, gerçek Unix socket, farklı UID, eski socket ve servis kilidi kabulünü kaydet. CI tanımı var; uzak CI bu oturumda çalıştırılmadı.
2. Udev ve kullanıcı systemd kurulumunu hedef dağıtımda doğrula. Servisi normal masaüstü kullanıcısı olarak çalıştır; başlatma, durdurma, hata sonrası yeniden başlama ve oturum sonunu ölç.
3. Gerçek Rival 3 Gen 2 için [donanım kabul listesini](Muvv/docs/HARDWARE-ACCEPTANCE.md) uygula. DPI, Hz, tuşlar, üç RGB bölgesi, fiziksel çıkarma/takma ve kalıcı kayıt sonrası güç döngüsü ayrı kabul sonuçlarıdır.
4. Repo sahibinin güncel koduna ayrı inceleme dalında birleştir; mevcut testleri tekrar çalıştır. Yayımlama öncesi lisans, üçüncü taraf kodun atfı ve paylaşım koşullarını netleştir.
5. Sistem tepsisi, otomatik profil yükleme, makro ve yeni cihaz desteği için ayrı gereksinim ve kabul ölçütü belirle. Bunlar mevcut sürümde tamamlanmış özellik değildir.

Servisi root çalıştırmayın; socket/klasör izinlerini herkese açmayın. Yerel HID çağrısını kesmek için aynı cihaz üzerinde ikinci yazıcı başlatmayın. Başarısı belirsiz USB komutunu otomatik tekrar etmeyin. Başlangıç değerlerini donanımdan alınmış yedek olarak sunmayın. Katalog kimliğini içerik hash'i veya dosya sisteminin işlemsel anlık görüntüsü saymayın. Demo ve sanal testlerden fiziksel cihaz kabulü çıkarmayın. Eski teslim ZIP'lerini üzerine yazmayın.
