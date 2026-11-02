# Muvv 0.2.0 yerel teslimi

11 Ekim 2026. İki özel repo ZIP'i üzerinden hazırlanan geliştirme sürümü. Teslim revizyonu 2, arşiv içi belge bağlantılarını da doğrular.

- `Muvv-0.2.0-kaynak.zip`: iki güncel depo, 92 kaynak/belge dosyası.
- `Muvv-0.2.0-inceleme.zip`: aynı kaynaklar, rapor, başlangıç incelemesi, test kanıtları, altı ekran görüntüsü, yamalar ve kurulum paketleri.
- Wheel ve tar.gz: kurulum ve kaynak dağıtımı. Hashli bağımlılık kurulumu uygulama README'sinde.
- İki `.patch`: kendi orijinal ZIP başlangıçlarına göre değişiklikler; 0.1 üstüne uygulanan artımlı yama değildir.
- `DOSYA-MANIFEST.json` ve `SHA256SUMS.txt`: içerik ve hash denetimi.

İnceleme ZIP'ini ayrı klasöre açıp `GELISTIRME-0.2-RAPORU.md` ile başlayın. Komutlar `Muvv/README.md` içindedir. Demo `muvv-gui --demo` ile açılır ve USB kullanmaz. Windows'ta gerçek cihaz servisi desteklenmez.

134 testin 122'si geçti, Linux/POSIX'e özgü 12 test atlandı; hata/başarısızlık yok. Bu toplamda 23 GUI testi vardır; son GUI düzenlemesinden sonra ayrıca yeniden geçti. Temiz wheel kurulumu kaynak klasörü dışında doğrulandı. Linux IPC/izin, udev/systemd ve fiziksel fare kabulü bekliyor. GitHub CI veya yayın yapılmadı.

Yamaları repo sahibinin güncel özel reposunda ayrı inceleme dalında kontrol edin. ZIP sonrasında değişiklik varsa çakışmayı inceleyin; zorla veya `--reject` ile geçiştirmeyin. Satır sonu dönüşümünü önleyen örnek:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna ayrı uygulanır. İki yama başlangıç kopyalarına uygulanıp 92 dosyayla byte düzeyinde karşılaştırıldı. ZIP'ler Git geçmişini içermez; yerel indeks uzak geçmiş yerine geçmez. Orijinal ZIP'ler, 45 başlangıç dosyası ve önceki 0.1 teslimi hashleriyle korundu.

Profil şeması değişmedi; 0.1 profilleri kullanılabilir. `list-profiles` sayfalıdır, CLI'de `--all` ile tamamı alınır. `set-button` varsayılan olarak kalıcı kayıt yapmaz. İçe aktarma yalnızca bilgisayara kayıt yapar, cihaza uygulama ayrı komuttur.

ZIP içindeki SHA dosyası ZIP içeriğini, dış klasördeki SHA dosyası dış teslim dosyalarını kapsar. Manifest ve SHA dosyası kendisini kendi içeriğinde listelemez. İnceleme ZIP'i CRC ve tüm giriş baytlarıyla doğrulandı.

Kanıt yardımcıları bu Windows çalışma alanına aittir. Taşınabilir proje testleri `Muvv/tools/check.py` ve `Muvv/test/` içindedir. Sanal ortam, Git iç dosyaları, gerçek kullanıcı profilleri ve kişisel geliştirici notu kaynak ZIP'ine dahil değildir. Lisans/yayın koşulları repo sahibiyle netleştirilmelidir.
