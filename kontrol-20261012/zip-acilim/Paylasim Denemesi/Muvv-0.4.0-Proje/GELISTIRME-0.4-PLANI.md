# Muvv 0.4 çalışma planı

Başlangıç: 11 Ekim 2026. Önceki teslimler ve indirilen iki ZIP korunur.

Bu tur, bağlantı değişimleri ile kapanış ve profil yenileme hatalarını ele alır. Mevcut sürücü, komutlar ve arayüz korunur.

1. Cihaz listesi ile seçimin farklı bağlantı anlarından gelmesini kontrollü bir testte oluştur. Liste, seçim ve cihaz oturumunu tutarlı döndür; tarama sırasında USB bekleme işlemini yönetici kilidinin dışında tut.
2. Kapanış isteği sırasında başlayan çok paketli USB işleminde sonraki paketlerin gönderilmesini ve uzun paket arası gecikmeyi test et. Devam eden yerel HID çağrısı döndüğünde işlemi kes, kalan işlemleri reddet; belirsiz durumu başarı olarak bildirme.
3. CLI profil sayfalamasında değişen katalog ve bozuk yanıtları test et. Eksik veya birleşmiş iki katalog için başarı bildirilmesini engelle; GUI ile aynı doğrulamayı kullan.
4. Test araçlarını Python optimizasyonu altında çalıştır. Kontroller ve kapatma işlemleri optimizasyon sırasında atlanmasın.
5. Yeni sürümü derle; ayrı ve temiz Python sanal ortamına kurarak testleri ve masaüstü akışlarını kurulu paketten çalıştır. Kaynak, yamalar, kanıtlar ve taşınabilir raporu ayrı bir teslim klasöründe doğrula.

Kabul: yeni hata senaryoları düzeltme öncesinde başarısız, sonrasında başarılı olmalı; mevcut testlerde hata olmamalı. Test raporları atlanan Linux kontrollerini ve fiziksel donanım kullanılmadığını belirtmeli. Eski sürümlerin SHA-256 değerleri korunmalı. Linux hizmeti ve gerçek cihaz testleri bu Windows oturumunda tamamlanmış sayılmaz.
