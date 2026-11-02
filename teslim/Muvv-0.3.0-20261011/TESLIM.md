# Muvv 0.3.0 yerel teslimi

11 Ekim 2026. İki özel repo ZIP'i üzerinden geliştirilmiş ayrı sürüm.

- `Muvv-0.3.0-kaynak.zip`: uygulama ve geliştirme notları, toplam 94 dosya.
- `Muvv-0.3.0-inceleme.zip`: aynı kaynak, rapor, test kayıtları, altı görsel, iki yama ve kurulum paketleri.
- Wheel, tar.gz, manifest ve SHA256 dosyaları ayrıca verilir.

İnceleme ZIP'ini ayrı klasöre açıp `GELISTIRME-0.3-RAPORU.md` ile başlayın. Kurulum `Muvv/README.md` içinde. Demo `muvv-gui --demo` ile çalışır ve USB açmaz.

Kaynak ortamında ve ayrı klasöre kurulan wheel'de 159 test: 145 geçti, Linux/POSIX'e özgü 14 test atlandı, hata yok. Toplamda 29 gerçek Tk senaryosu var. Kurulan paketten 2.000 parçalı mesaj, 800 eşzamanlı işlem, 200 yeniden bağlantı ve dört USB kesilme noktası da sınandı. Linux UID/izin/flock/udev, gerçek fare ve uzak CI kabulü henüz yapılmadı.

Yeni oturum koruması, arayüzde bekleyen komutun yeniden bağlanan cihaza yazmasını önler. Meşgul cihaz son değerleri korur. Kapanış işçiler bitene kadar servis kilidini tutar. Profil sayfalarındaki hata cihaz ekranını silmez. Profil şeması ve USB rapor biçimi korunur.

İki yama kendi orijinal ZIP başlangıcına göredir; 0.2 üstüne artımlı yama değildir. Repo sahibinin güncel kaynakları üzerinde ayrı inceleme dalında önce kontrol edin:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna uygulanır. Yamalar yerel başlangıç kopyalarına uygulanıp 82 + 12 dosya byte düzeyinde karşılaştırıldı. Git geçmişi eklenmedi. Orijinal ZIP'ler, 45 başlangıç dosyası ve önceki 0.1/0.2 teslimleri hashleriyle korunur.

Kaynak ZIP'i sanal ortam, Git iç dosyaları, kullanıcı profilleri ve kişisel geliştirici notunu içermez. İnceleme kopyasındaki geçmiş raporların bağlantıları taşınabilirdir; pakette olmayan özgün kaynak satır referansları düz metin olarak tutulur.

İç SHA dosyası inceleme arşivinin girişlerini, dış SHA dosyası teslim klasörünü doğrular. Manifest ve checksum dosyası kendi içeriğinde kendisini listelemez. Kanıt yardımcıları bu Windows çalışma alanına aittir; proje testleri `Muvv/tools/check.py` ve `Muvv/tools/simulation_check.py` ile tekrar çalıştırılır. Lisans ve paylaşım koşulları repo sahibiyle netleştirilmelidir.
