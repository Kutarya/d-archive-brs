"""Prepare a new delivery builder; keep previous builders and artifacts untouched."""

from pathlib import Path

root = Path("D:/BRS")
content = (root / "gelistirme-0.2/teslim-paketi.py").read_text(encoding="utf-8")
content = content.replace("0.2", "0.3").replace("-20261011-r2", "-20261011")
content = content.replace("== 134", "== 159").replace("== 122", "== 145").replace("== 92", "== 94")
content = content.replace('len(tests["skipped"]) == 12', 'len(tests["skipped"]) == 14')
content = content.replace("def relocate(match):", "def relocate(match, name=name):")
start = content.index('    assert (\n        "Ran 23 tests"')
end = content.index('    wheel =', start)
content = content[:start] + '''    wheel_tests = json_file("wheel-test-sonuclari.json")
    assert wheel_tests["successful"]
    assert all(wheel_tests[key] == tests[key] for key in ("tests", "passed", "errors", "failures"))
    assert len(wheel_tests["skipped"]) == 14
    log = (EVIDENCE / "test-kaydi.log").read_text(encoding="utf-8")
    assert sum("test_gui.GUITests." in line for line in log.splitlines()) == 29
    simulation = json_file("sanal-senaryolar.json")
    assert simulation["successful"] and not simulation["physical_hid_access"]
    assert simulation["remaining_workers"] == []
    assert simulation["scenarios"]["reconnect_and_profiles"]["cycles"] == 200
''' + content[end:]
content = content.replace('        "gui-test-kaydi.log",\n', '')
content = content.replace('        "test-sonuclari.json",', '''        "test-sonuclari.json",
        "wheel-test-sonuclari.json",
        "wheel-test-kaydi.log",
        "sanal-senaryolar.json",
        "sanal-senaryolar.log",
        "arayuz-once.log",
        "yeniden-baglanti-once.log",
        "yama-dogrulama-kaydi.log",
        "bagimlilik-denetimi.log",
        "gelistirme-bagimlilik-denetimi.log",
        "yama-olustur.py",''')
start = content.index('        """# Muvv')
end = content.index('""",\n        encoding=', start)
handoff = '''# Muvv 0.3.0 yerel teslimi

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
'''
content = content[:start] + '        """' + handoff + content[end:]
(root / "gelistirme-0.3/teslim-paketi.py").write_text(content, encoding="utf-8", newline="\n")
