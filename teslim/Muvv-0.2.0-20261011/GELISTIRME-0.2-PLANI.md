# Muvv 0.2 çalışma ve kabul planı

11 Ekim 2026. Önceki 0.1 teslimi korunur; uygulama ve geliştirme notları mevcut klasörlerde ilerletilir.

1. Kapanış ve zaman aşımı: runner kilidinde sonsuz beklemeyi kaldır; yazımı başlamayan işi cihazda belirsiz işlemden ayır; hatadan sonra bekleyen paketleri gönderme; kapanan IPC işçileri varken yeniden servis başlatma.
2. Profil deposu: tek bozuk dosya diğer profilleri veya cihaz kontrolünü engellemesin; dosya taraması ve IPC yanıtı sınırlı olsun; yeniden adlandırma ve doğrulanmış içe/dışa aktarma ekle.
3. Cihaz işlevleri: üç bölgeye ayrı renk; mevcut kareyi koruyarak animasyonu durdurma; yeniden bağlantıda önceki oturum durumunu temizleme.
4. Arayüz: doğru başarı/hata ayrımı; cihaz takma/çıkarma takibi; eski form değerlerinin temizlenmesi; kullanıcı düzenlemesini otomatik yenilemenin ezmemesi; cihaz yokken uygun düğme durumu; okunabilir tuş seçimi ve profil aktarımı.
5. Kurulum ve işletim: servis gerektirmeyen ortam tanısı, sürüm bilgisi, başlatma hataları, kaynak/wheel kabulü ve güncel kullanım belgeleri.
6. Teslim: hata senaryoları ve kullanıcı akışları testleri; temiz kurulum; yeni sürüm kaynakları ve iki yama; önceki teslim ve başlangıç hashlerini koruma.

Kabul, yalnızca özellik sayısıyla ölçülmez. Bozuk profil varken cihaz ayarı çalışmalı; başarılı yazım sonrası yenileme hatası yeniden yazma istememeli; bekleyen işlem iptal edilirse paket gitmemeli; belirsiz native çağrıda ikinci yazıcı açılmamalı; pencere açıkken cihaz kaybı gösterilmeli; profil dışa/içe aktarımı aynı ayarları korumalı.

Gerçek Linux/udev/systemd ve fiziksel fare kabulü bu Windows ortamında tamamlanmış sayılmaz. Yeni marka protokolü, makro ve donanım okuma desteği kanıt olmadan eklenmez.
