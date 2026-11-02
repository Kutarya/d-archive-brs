# Muvv 0.3 çalışma planı

Bu tur, 0.2 kaynakları üzerinde sanal HID ve gerçek Tk pencereleriyle yürütülür. Önceki ZIP teslimleri ve indirilen kaynaklar korunur.

1. Aynı USB yolu üzerinde yeniden bağlantı ve bekleyen komut yarışını yeniden üret. Her başarılı bağlantıya ayrı oturum kimliği ver; güncel oturumla uyuşmayan korumalı komut hiçbir HID raporu göndermesin. Eski CLI çağrıları çalışmaya devam etsin.
2. Profil sayfası alınamadığında cihaz ekranını kullanılabilir tut. Eksik profil listesini açıkça göster; bozuk yanıtları doğrula, istemci yanıt nesnesini değiştirme.
3. Geçici meşgul cihazın bilinen ayarlarını koru; yeniden bağlantıda eski girişleri temizle. Bağlantı ve animasyon hata durumlarını doğru göster.
4. Kapanış, yeniden bağlantı, parçalı IPC mesajları, eşzamanlı ayarlar ve profil aktarımını tekrar eden sanal senaryolarla sınayarak kaynak/işçi sızıntılarını kontrol et.
5. Regresyon, Ruff, paket derleme ve temiz sanal ortam kurulumunu tamamla. Yeni rapor ve ayrı teslim paketi oluştur.

Kabul: Eski ve yeni testler geçmeli; bayt düzeyinde cihaz protokolü korunmalı; eski oturum hedefleyen testlerde yeni cihaza yazım sıfır olmalı; arayüz testlerinde Tk callback hatası olmamalı. Windows testleri Linux UID/izin/udev kabulü ve fiziksel USB doğrulaması olarak sunulmaz.
