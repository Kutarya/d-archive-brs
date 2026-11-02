"""Prepare validation and delivery helpers in the new evidence directory."""

import re
from pathlib import Path

previous = Path("D:/BRS/gelistirme-0.3")
current = Path("D:/BRS/gelistirme-0.4")
for name in ("paket-dogrulama.py", "kaynak-dogrulama.py", "yama-dogrulama.py", "yama-olustur.py", "teslim-paketi.py", "son-kontrol.py"):
    content = (previous / name).read_text(encoding="utf-8")
    content = content.replace("0.3.0", "0.4.0").replace("gelistirme-0.3", "gelistirme-0.4").replace("GELISTIRME-0.3", "GELISTIRME-0.4")
    if name == "kaynak-dogrulama.py":
        content = content.replace('("Muvv-0.2.0-20261011", "Muvv-0.2.0-20261011-r2")', '("Muvv-0.2.0-20261011", "Muvv-0.2.0-20261011-r2", "Muvv-0.3.0-20261011")')
        content = content.replace('"previous_0_2_deliveries_unchanged"', '"previous_0_2_and_0_3_deliveries_unchanged"')
    if name == "teslim-paketi.py":
        content = content.replace('== 159', '== 176').replace('== 145', '== 162').replace('== 29', '== 33').replace('== 94', '== 95')
        evidence_names = (
            "test-sonuclari.json", "test-kaydi.log", "coverage.json", "coverage.txt",
            "wheel-test-sonuclari.json", "wheel-test-kaydi.log",
            "sanal-senaryolar.json", "sanal-senaryolar.log", "optimize-senaryolar.json",
            "optimize-senaryolar.log", "regresyon-oncesi.log", "regresyon-sonrasi.log",
            "katalog-oncesi.log", "tani-oncesi.log", "tani-sonrasi.log",
            "katalog-yarisi-oncesi.log", "katalog-arayuz-oncesi.log", "katalog-arayuz-sonrasi.log",
            "bagimlilik-denetimi.json", "bagimlilik-denetimi.log", "ortam-tanisi.json",
            "arayuz-smoke.json", "arayuz-smoke.log", "optimize-arayuz.json",
            "derleme.log", "ruff-check.log", "ruff-format.log",
            "paket-dogrulama.json", "paket-kontrol-kaydi.log", "paket-dogrulama.py",
            "kaynak-dogrulama.json", "kaynak-dogrulama-kaydi.log", "kaynak-dogrulama.py",
            "yama-dogrulama.json", "yama-dogrulama-kaydi.log", "yama-dogrulama.py",
            "yama-olustur.py", "teslim-paketi.py", "son-kontrol.py",
            "Muvv.patch", "Muvv_development_environment.patch",
        )
        content, count = re.subn(r'    evidence_names = \(.*?\n    \)', '    evidence_names = ' + repr(evidence_names), content, count=1, flags=re.S)
        assert count == 1
        start = content.index('        """# Muvv ')
        end = content.index('""",\n        encoding="utf-8",', start) + 3
        handoff = '''# Muvv 0.4.0 yerel teslimi

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
'''
        content = content[:start] + '        """' + handoff + '"""' + content[end:]
    if name == "son-kontrol.py":
        content = content.replace('== 143', '== len(manifest["review_files"]) + 2')
    (current / name).write_text(content, encoding="utf-8", newline="\n")
