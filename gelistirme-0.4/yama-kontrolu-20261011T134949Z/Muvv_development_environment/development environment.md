# Geliştirme düzeni

Uygulama kaynakları `Muvv`, tasarım ve çalışma notları `Muvv_development_environment` klasöründe tutulur. İki depo ayrı incelenir ve değişiklikleri ayrı teslim edilir.

## Dosyalar

- `proje.md`: mevcut kapsam ve teknik tasarım.
- `python_environment_setup.md`: kurulum ve test komutları.
- `memory-bank/activeContext.md`: aktif çalışma ve doğrulama sınırı.
- `memory-bank/progress.md`: tamamlanan ve bekleyen işler.
- `memory-bank/systemPatterns.md`: mimari kararlar.
- `memory-bank/techContext.md`: teknoloji ve bağımlılıklar.
- `Truemove_core.txt`: cihazın DPI protokol tablosu.

## Kaynak ve test politikası

Sanal ortam `Muvv/.venv` içinde tutulur ve kaynak teslimine alınmaz. Bağımlılıklar sürüm ve hashleriyle `requirements-lock.txt` içinde kayıtlıdır.

Otomatik testler `Muvv/test/unit` ve mevcut çekirdek test dosyalarındadır. `python tools/check.py` bu testleri toplar; gerçek USB cihazı açmaz. Donanım denemeleri `tools/hardware_check.py` üzerinden açık cihaz seçimiyle çalıştırılır. Yazma denemesi ayrıca `--allow-write` gerektirir.

Bir test sonucu kaydedilirken ortam, gerçek donanım kullanımı ve atlanan kontroller de belirtilir. Demo, Linux servis kabulü veya fiziksel fare ölçümü yerine geçmez.

## Bu yerel çalışma

Kaynak ZIP'leri `D:\BRS` içinde korunmuştur. `inceleme/kaynak` başlangıç görüntüsüdür; uygulama değişiklikleri bu kopyaya yazılmaz.

Aktif klasörlerde ZIP başlangıcını karşılaştırabilmek için yerel Git indeksi oluşturulmuştur. ZIP, uzak repo commit geçmişini içermez; bu indeks repo sahibinin geçmişi yerine geçmez. İnceleme yaması ve güncel kaynak paketi ayrı teslim edilir. Başka birinin kimliğiyle commit veya uzak repo işlemi yapılmaz.

Test kanıtları ve teslim raporu `D:\BRS` altında tutulur; kullanıcı profilleri, sanal ortam, önbellekler ve Git iç dosyaları kaynak ZIP'ine girmez.
