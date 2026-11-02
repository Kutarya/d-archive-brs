# Muvv 0.4.0 yerel teslimi

11 Ekim 2026. İki özel repo ZIP'i üzerinden geliştirilmiş ayrı sürüm.

- `Muvv-0.4.0-kaynak.zip`: uygulama ve geliştirme notları, 83 + 12 kaynak dosyası.
- `Muvv-0.4.0-inceleme.zip`: kaynak, rapor, test kayıtları, altı arayüz görseli, yamalar ve kurulum paketleri.
- Wheel, tar.gz, manifest ve SHA256 dosyaları ayrıca verilir.

İnceleme ZIP'ini ayrı klasöre açıp `GELISTIRME-0.4-RAPORU.md` ile başlayın. Kurulum `Muvv/README.md` içinde. `muvv-gui --demo` USB açmadan çalışır.

Kaynakta ve ayrı sanal ortama kurulan wheel'de 176 test: 162 geçti, Linux/POSIX'e özgü 14 test atlandı, hata yok. Bu toplamda 33 gerçek Tk senaryosu bulunur. Kurulu paketten 2.000 parçalı mesaj, 800 eşzamanlı işlem, 200 yeniden bağlantı ve dört USB kesilme noktası sınandı. Linux izin/UID/flock/udev, gerçek fare ve uzak CI kabulü yapılmadı.

0.4, bağlantı değişirken cihaz listesi/oturum tutarlılığını, USB kapanışında kalan raporları durdurmayı, profil kataloğunun değişim denetimini ve görünür cihaz erişim hatalarını düzeltir. Test araçları Python optimizasyonunda da kontrolleri ve kapanışı çalıştırır. Profil şeması ve USB rapor biçimi korunur.

Yamalar orijinal ZIP başlangıcına göredir; önceki geliştirme sürümlerinin üstüne artımlı yama değildir. Repo sahibinin güncel kaynakları üzerinde ayrı inceleme dalında önce kontrol edin:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna uygulanır. Yamalar başlangıç kopyalarına uygulanıp 83 + 12 dosya byte düzeyinde karşılaştırıldı. Git geçmişi eklenmedi. Orijinal ZIP'ler, 45 başlangıç dosyası ve önceki 0.1/0.2/0.3 teslimleri hashleriyle korunur.

Kaynak ZIP'i sanal ortam, Git iç dosyaları, kullanıcı profilleri ve kişisel geliştirici notunu içermez. Geçmiş raporların teslim kopyaları taşınabilirdir; pakette bulunmayan özgün kaynak referansları düz metindir.

İç SHA dosyası inceleme arşivini, dış SHA dosyası teslim klasörünü doğrular. Manifest ve checksum dosyası kendi içeriğinde kendisini listelemez. Kanıt yardımcıları bu Windows çalışma alanına aittir; proje testleri `Muvv/tools/check.py`, `Muvv/tools/simulation_check.py` ve `Muvv/tools/gui_smoke.py` ile tekrar çalıştırılır. Lisans ve paylaşım koşulları repo sahibiyle netleştirilmelidir.
