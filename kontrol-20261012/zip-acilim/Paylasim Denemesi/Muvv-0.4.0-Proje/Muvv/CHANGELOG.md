# Değişiklik kaydı

## 0.4.0 — 2026-10-11

- Cihaz listesi ve seçimi aynı yönetici kilidi altında alınır. Liste ile cihaz durumu arasında bağlantı yenilenirse yeni oturum eski bilgiyle birleştirilmez.
- Tam cihaz ID'si varsayılan takma adlarından önce çözülür; ID içindeki boşluklar korunur.
- Kapanış isteği devam eden USB işleminin kalan raporlarını durdurur; paketler arasındaki bekleme kapanışta kesilir.
- CLI profil sayfalaması GUI ile ortak doğrulama kullanır. Değişen katalog, tekrar eden profil adı ve bozuk sayfa başarı olarak gösterilmez.
- Profil katalog kimliği dosya bilgilerini de içerir; aynı adla üzerine yazılan profil algılanır. Okuma sırasında dışarıdan değişen katalog yeniden okuma gerektirir.
- Katalog okunamazken önceki profil adları ve kullanılabilir cihaz kontrolleri korunur; eksik liste uyarısı gösterilir.
- USB tarama, cihaz açma ve kapanmakta olan bağlantıların nedenleri arayüzde görünür. Tarama düzeldiğinde eski uyarı temizlenir.
- Sanal senaryo ve arayüz kontrol araçları Python `-O` altında da kontrolleri ve kapatma işlemlerini çalıştırır.

Profil JSON şeması, 64 bayt USB raporları ve mevcut komutlar korunur.

## 0.3.0 — 2026-10-11

- Aynı USB yolu üzerindeki yeni bağlantıya eski bekleyen komut yazılmasını önleyen oturum koruması. `expected_session` isteğe bağlıdır; eski CLI kullanımı korunur.
- Yeniden bağlantı sonrası önceki oturum taslaklarının temizlenmesi, geçici meşgul yanıtta son değerlerin korunması ve yazımların bekletilmesi.
- USB/tarama/IPC işçileri bitmeden servis kilidinin bırakılmaması. Kapanamayan işçiler varken aynı manager yeniden başlatılmaz.
- Profil sayfalama hatasının cihaz bilgilerini silmemesi; değişen dosya adları kataloğu, eksik liste ve eski profil adlarının korunması.
- Ekrana ulaşmadan servis yanıtı doğrulaması; bozuk ayarların ekranı yarım güncellemeyle bırakmaması.
- Profil deposunda FIFO değişimi yarışına karşı nonblocking açılış. Kurtarılan animasyon hatasının temizlenmesi ve kapalı bağlantının doğru gösterilmesi.
- Parçalı IPC, eşzamanlı raporlar, yeniden bağlantı, profil dosyası aktarımı ve USB kesilmesi için tekrar üretilebilir sanal senaryo aracı; Linux CI tanımına eklenmesi.

Profil şeması ve USB rapor biçimi korunur. Sanal HID/Tk kabulü, gerçek Linux ve fiziksel cihaz kabulünden ayrı tutulur.

## 0.2.0 — 2026-10-11

### Düzeltmeler

- Kapanış artık komut kilidinde sınırsız beklemiyor; geç tamamlanan açma işlemi cihazı yeniden çalıştırmıyor.
- Kuyrukta iptal edilmiş işlem ile başlamış fakat sonucu belirsiz yazım ayrı bildiriliyor. USB hatasından sonra bekleyen işler durduruluyor.
- Kapanamayan runner, USB işçisi oluşmamış olsa da takip ediliyor; eski IPC işçileri varken aynı servis nesnesi yeniden başlatılamıyor.
- Tek bozuk profil cihaz ekranını engellemiyor. Profil katalogları, dosya taraması ve yanıt boyutu sınırlandırılıyor.
- Başarılı yazımdan sonraki yenileme hatası başarısız ayar olarak gösterilmiyor. Pencere kapandıktan sonra geç gelen sonuçlar Tk'ya erişmiyor.
- Arka plan yenilemesi ve önceki komut yanıtı kullanıcının yeni girişlerini ezmiyor. Yeniden bağlantı eski oturum değerlerini temizliyor.
- JSON float taşması, geçersiz efekt seçenek nesnesi ve sonlu olmayan USB gecikmeleri reddediliyor.

### Eklenenler

- Bölgelere bağımsız renk, son kareyi koruyarak animasyonu durdurma ve fare işlevi atama.
- Profil yeniden adlandırma ve doğrulanmış JSON içe/dışa aktarma; cihaz bağlı olmadan profil yönetimi.
- Adlarıyla klavye tuşu/fare işlevi seçimi, kaydırılabilir sekmeler, otomatik cihaz yenilemesi ve bağlantıya uygun düğme durumları.
- Donanıma erişmeyen `doctor`, `--version` ve tek sürüm kaynağı.
- Kapanış, hata sonrası davranış, profil sınırları, dosya aktarımı ve arayüz akışları için regresyon testleri.

Profil şeması sürüm 1 olarak kalır. `list-profiles` artık sayfalıdır; tüm liste için CLI'de `--all`, IPC'de `next_offset` kullanılır. `set-button` varsayılan olarak kalıcı kayıt yapmaz. Gerçek Linux ve fiziksel fare kabulü ayrı yapılmalıdır.

## 0.1.0 — 2026-10-11

Bu sürüm indirilen özel repo kaynakları üzerinden hazırlanan geliştirme kopyasıdır.

### Düzeltmeler

- IPC, kullanıcıya özel dizine ve izinlere taşındı; aynı UID kontrolü, tek servis kilidi, mesaj sınırları ve zaman aşımı eklendi.
- Parçalı mesajlar uzunluk başlığıyla birleştiriliyor; geçersiz UTF-8, yinelenen JSON anahtarı ve sayısal özel değerler reddediliyor.
- Efekt seçenekleri açık parametre listesiyle doğrulanıyor. Hatalı istek mevcut efekti silmiyor.
- Dalga hızının iki kez uygulanması ve sıfır dalga boyu hatası düzeltildi. Sabit efektin varsayılanı ve adı kullanılabilir hale geldi.
- Tuş atamaları önce ayrı kopyada doğrulanıyor; reddedilen sol tık değişikliği veya hatalı kod sonraki işlemleri bozmuyor.
- USB işlemleri gerçek yazma sonucunu bekliyor. Eksik yazım, bağlantı kaybı ve zaman aşımı başarı sayılmıyor.
- Komut kuyruğu sınırlandı; RGB tarafında yalnızca son bekleyen kare tutuluyor. Tuş yapılandırması ve kayıt raporu tek işlemde gönderiliyor.
- Yeni bağlantı ve normal kapanış artık kendiliğinden siyah RGB karesi yazmıyor.
- Başarısız bağlantı aktif cihaz olarak listelenmiyor; tekrar deneme ve bloke olmuş işçi takibi eklendi.
- Belirsiz cihaz adı ilk eşleşmeye yönlendirilmek yerine hata döndürüyor.
- Yeniden bağlantı ile cihaz taraması aynı kilidi kullanıyor; tarama geçici kapanışı yeni cihaz gibi açmıyor.
- Arayüzün işlem sonuçları ana Tk döngüsünde işleniyor; kapanış zamanlayıcıları ve pencere kaynakları temizleniyor.

### Eklenenler

- CustomTkinter arayüzü ve USB kullanmayan demo.
- Spektrum efekti ve canlı efekt güncelleme.
- Beş DPI değerini birlikte ayarlama komutu.
- İsimli bilgisayar profilleri, profil önizleme ve isteğe bağlı kalıcı uygulama.
- Durum, efekt listesi, tuş düzenini geri yükleme ve yeniden bağlanma komutları.
- Paket giriş noktaları, sabit bağımlılıklar/hashler, Linux CI ve otomatik hata senaryoları.
- Açık cihaz seçimi ve yazma izni gerektiren manuel donanım kontrolü.

### Uyumluluk

Eski CLI komut adları korunur. IPC taşıması uzunluk başlığına geçtiği için eski CLI ile yeni servis birlikte çalışmaz; ikisi aynı sürümden kullanılmalıdır. `set-color` hem eski `hex` alanını hem yeni `color` alanını kabul eder.

Okunamayan DPI ve tuş düzeni ilk kısmi değişiklikte açık başlangıç ister. Sayısal cihaz ve kademe argümanları karışmasın diye `-d` önerilir. Belgelerde geçmiş donanım denemeleriyle bu sürümün doğrulaması ayrı tutulur.
