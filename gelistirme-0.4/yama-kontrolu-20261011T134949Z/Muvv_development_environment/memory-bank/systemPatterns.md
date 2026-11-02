# Mimari kararlar

## Katmanlar

1. Sürücü yalnızca modele ait HID paketlerini ve oturumda bilinen cihaz ayarlarını yönetir.
2. Vitray, Layer ve ZoneMap donanımdan bağımsız RGB kareleri hesaplar.
3. DeviceRunner cihaz komutunu, animasyonu ve tek USB yazıcısını koordine eder.
4. DeviceManager cihaz taraması, hotplug, kimlik çözümü ve profil işlemlerini yönlendirir.
5. CLI ve GUI aynı IPC komut sözleşmesini kullanır.

## Hata ve durum

İstek önce doğrulanır; kabul edilen yeni durum başarıyla USB'ye yazıldıktan sonra tutulur. Firmware'den geri okuma yoksa sonuç “written” olarak bildirilir, “donanımda doğrulandı” olarak bildirilmez.

Tuş değişikliği bir kopyada hazırlanır. En az bir sol tık korunur. İlk bağlantıda mevcut DPI/tuş düzeni bilinmediği için tam değer veya açık varsayılan başlangıç gerekir.

Kontrol raporları bir Future taşıyan işlem içinde sıralanır. RGB tek bekleyen son kareyi tutar. Komut ile render aynı cihaz kilidini paylaşır. Native I/O bloke olursa yeni yazıcı başlatılmaz.

Yazımı başlamadan süre aşan Future iptal edilir; başlamış çağrının zaman aşımı donanımı belirsiz bırakır ve bağlantıyı yeni yazıma kapatır. Runner kapanışı render, komut kilidi ve USB işçisi için tek süre bütçesi kullanır. Kapanış isteğinden sonra dönen açma işlemi render başlatmaz.

Arayüz komut başarısı ile durum yenilemesini ayrı değerlendirir. Her form grubunun düzenleme sayacı vardır; arka plan yanıtı daha yeni girişi değiştirmez. Arka plan okumasının arkasına en fazla bir açık kullanıcı işi konur. Tk callback'leri ana döngüde tutulur, işçi yalnızca sonuç token'ını aktarır.

## Güvenlik

Unix socket aynı UID ile sınırlıdır; dizin ve dosya izinleri denetlenir. İstemci sayısı, mesaj boyutu, JSON yapısı ve süre sınırları uygulanır. Root servis yerine udev üzerinden normal kullanıcı erişimi kullanılır.

Efekt parametreleri açık listeden seçilir. Driver/effect kaydı açık modül listesidir; klasördeki her Python dosyası import edilmez. Yeni eklenti güvenilen kod sayılır.

Profil adları dosya yoluna çevrilmez; hashli dosya adı ve atomik kayıt kullanılır. Profil alanlarının modeli ve değerleri USB işleminden önce doğrulanır.

Katalog en fazla 32 dosyalık sayfalarla alınır. Bozuk dosya diğer profilleri engellemez, fakat kaynak sınırlarında sayılır. Aktarım dosyasını istemci doğrular; servis keyfi dosya yolu almaz. Ad değişikliği iki dosyalı bir işlemdir; güç kesilmesinde iki kopya kalabileceği belgelenir.

Cihaz listesi, seçim ve servis durumu tek yönetici kilidiyle alınır; cihaz bilgisi bu kilidin dışında oturum kontrolüyle okunur. Katalog kimliği dosya adları ve dosya bilgilerini kapsar; okuma sırasında değişim reddedilir. CLI sayfa hatasında başarısız çıkar, GUI cihaz kontrolünü koruyup eksik listeyi gösterir. Kapanış yeni raporu engeller ve raporlar arası beklemeyi uyandırır; başlamış native çağrı zorla kesilmez.

## Doğrulama

Otomatik testler gerçek cihazı açmaz. Linux izin/soket, GUI ve fiziksel fare kabulü ayrı sonuçlardır. Yeni özellik, ancak ölçülen sınırıyla tamamlandı olarak yazılır.
