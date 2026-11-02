# Değişiklik kaydı

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
