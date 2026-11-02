# Muvv

Linux üzerinde fare ayarlarını ve yazılım tabanlı RGB efektlerini yöneten Python uygulaması. Mevcut sürücü SteelSeries Rival 3 Gen 2 Wired modelini destekler (`1038:1870`, HID arayüzü 3).

CLI ve masaüstü arayüzü aynı kullanıcıya ait yerel servise bağlanır. USB paketlerini sürücü, aydınlatma karelerini Vitray motoru üretir.

## Özellikler

- Beş DPI kademesi ve etkin kademe seçimi; 125/250/500/1000 Hz yoklama hızı.
- Üç RGB bölgesine ayrı renk; sabit renk, nefes, dalga ve spektrum efekti. Animasyonu durdururken son renkler korunur.
- Efekti yeniden oluşturmadan renk ve hız güncelleme.
- Adlarıyla klavye tuşu/fare işlevi seçimi ve varsayılan tuş düzenine dönüş.
- Bilgisayarda isimli profiller; yeniden adlandırma, JSON içe/dışa aktarma ve isteğe bağlı fare belleğine kaydetme.
- Cihaz takma/çıkarma takibi, başarısız bağlantıyı yeniden deneme ve işlem durumu.
- Tarama ve USB erişim hatalarının ekranda gösterilmesi; bağlantı yenilendiğinde eski işlemlerin engellenmesi.
- Donanıma erişmeyen, geçici profiller kullanan masaüstü demosu.
- Donanıma erişmeden sürüm, bağımlılık ve özel dizin denetimi (`muvv doctor`).

Faredeki mevcut DPI ve tuş düzeni okunamaz. Program bu alanları **bilinmiyor** olarak gösterir. İlk kısmi değişiklik için tam değerleri vermek veya varsayılanlarla başlamayı açıkça seçmek gerekir.

## Kurulum

Python 3.10 veya üzeri gerekir. Linux masaüstü arayüzü için dağıtımın `python3-tk` paketi kurulmalıdır.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.2.1
python -m pip install --require-hashes -r requirements-lock.txt
python -m pip install --no-deps -e .
```

`requirements-lock.txt` çalışma zamanı ve arayüz bağımlılıklarını sürüm ve SHA-256 ile sabitler. Yalnızca CLI kurulacaksa `pip install -e .`, arayüz de isteniyorsa `pip install -e ".[gui]"` kullanılabilir; bu iki kısa yol geçişli bağımlılıkların hashlerini kilitlemez.

### Linux cihaz erişimi

Servisi masaüstü kullanıcısı olarak çalıştırın. Örnek udev kuralı sadece desteklenen fare modelini eşleştirir ve aktif yerel oturuma erişim verir:

```bash
sudo install -m 0644 packaging/70-muvv.rules /etc/udev/rules.d/70-muvv.rules
sudo udevadm control --reload-rules
```

Fareyi çıkarıp yeniden takın. Masaüstü oturumunda `muvvd` komutunu çalıştırın. Başka terminalden `muvv list` ile bağlantıyı kontrol edin. SSH veya oturumsuz servis erişimi için sistem yöneticisi ayrı cihaz grubu/ACL politikası belirlemelidir.

Kuralın kapsamı VID/PID'dir; uygulama ayrıca HID arayüzü 3'ü seçer. `ATTRS` eşleşmelerinin aynı üst aygıta ait olması gerektiğinden arayüz numarası farklı üst aygıttan aynı kurala eklenmemiştir. [udev kural söz dizimi](https://manpages.debian.org/unstable/udev/udev.7.en.html).

### Servis ve arayüz

```bash
muvvd
muvv-gui
```

`packaging/muvvd.service` kullanıcı servisi örneğidir. `ExecStart` yolunu kendi kurulumunuza uyarlayıp `~/.config/systemd/user/` altına kopyalayın; ardından `systemctl --user daemon-reload` ve `systemctl --user enable --now muvvd` çalıştırılabilir. Örnek yol `~/.local/share/muvv/.venv/bin/muvvd` şeklindedir.

### Donanımsız demo

```bash
muvv-gui --demo
```

Demo Linux veya Windows'ta Tk ile açılabilir. USB cihazı açmaz, kalıcı kullanıcı profillerini kullanmaz ve pencere kapandığında geçici verilerini kaldırır. Gerçek cihaz servisi bu sürümde Linux'a özgüdür.

Arayüz bağlı cihazları yaklaşık üç saniyede bir yeniler. Aynı cihazdaki uygulanmamış girişler korunur; ayar gönderilirken yeniden düzenlenen alanlar da eski yanıtla değiştirilmez. Cihaz değiştiğinde formlar yeni oturuma geçer. USB yazımı başarılı olup bilgi yenilemesi başarısız olduğunda, uygulama yazımın tamamlandığını ayrıca bildirir. Bu bildirim ayarı tekrar göndermeyi gerektirmez.

Aynı USB yolunda yeniden bağlantı da yeni oturum sayılır. Arayüz komutu seçildiği oturumla birlikte gönderir; o sırada cihaz yeniden açılmışsa işlem yazmadan reddedilir. Bilgileri yenileyip yeni oturum için ayarı tekrar seçin. Geçici meşgul yanıtında son bilinen değerler korunur, yeni yazımlar bilgi alınana kadar kapatılır.

Bozuk profil dosyaları cihaz ekranını kapatmaz; dosya adı ve hata Profiller sekmesinde gösterilir. Bilgisayardaki profil işlemleri fare bağlı olmadan da kullanılabilir. Sekmeler dar veya ölçeklenmiş ekranda kaydırılabilir.

Profil sayfalarından biri alınamaz veya klasör yenileme sırasında değişirse liste eksik olarak işaretlenir. Önceki profil adları ekranda korunur; cihaz ayarları bağımsız kullanılabilir. Dosya adı kataloğunun değişmediği, dosya içeriklerinin aynı kaldığı anlamına gelmez; profil ayrıntısı ve uygulama sırasında içerik yeniden okunur.

## CLI kullanımı

```bash
muvv list
muvv info 1
muvv status
muvv effects
muvv --version
muvv doctor
muvv set-effect wave -d 1 --color 4AD2B1 --speed 0.5 --direction vertical
muvv update-effect -d 1 --color FF0080 --speed 2
muvv set-effect spectrum -d 1 --speed 1 --brightness 0.6
muvv set-color FF0000 1
muvv set-colors -d 1 --wheel FF0000 --middle 00FF00 --underglow 0000FF
muvv stop-effect 1
```

DPI kademeleri CLI'de **0–4**, arayüzde **1–5** olarak gösterilir:

```bash
muvv set-dpi-stages 400 800 1200 2400 3200 -d 1 --active 1
muvv set-dpi 2 -d 1
muvv set-polling 500 1
```

İlk bağlantıda yalnızca bir kademe seçilecekse `muvv set-dpi 2 -d 1 --initialize` beş kademeyi Muvv varsayılanlarıyla değiştirir. Mevcut fare değerlerinin yedeği alınmaz.

Tuş kodu HID Keyboard/Keypad usage değeridir; A `0x04`, Enter `0x28`, sol Shift `0xE1`:

```bash
muvv bind-key button4 0xE1 1 --initialize --no-persist
muvv restore-buttons 1 --no-persist
muvv set-button button4 0x30 -d 1
muvv save 1
```

`--initialize` ilk kullanımda diğer tuşları varsayılanlarla başlatır. En az bir sol tık korunur. `bind-key` ve `restore-buttons` uyumluluk için varsayılan olarak fare belleğine kayıt gönderir; yalnızca oturumluk değişiklikte `--no-persist` kullanın. Arayüzde kalıcı kayıt ayrı kutuyla seçilir.

`set-button` fare işlevi atar: `0` devre dışı, `1–5` sol/sağ/orta/geri/ileri, `0x30` DPI, `0x31` yukarı kaydırma, `0x32` aşağı kaydırma. Bu yeni komut varsayılan olarak yalnızca oturuma yazar; fare belleği için `--persist` gerekir. Bilinmeyen düzeni başlatmak için `--initialize` kullanılır.

```bash
muvv save-profile Çalışma -d 1
muvv list-profiles --all
muvv show-profile Çalışma
muvv apply-profile Çalışma -d 1
muvv apply-profile Çalışma -d 1 --persist
muvv rename-profile Çalışma Oyun
muvv export-profile Oyun ./oyun.json
muvv import-profile ./oyun.json --name Çalışma
muvv delete-profile Çalışma
muvv --json info 1
```

Profilde yalnızca oturumda bilinen alanlar bulunur. Eksik alanlar uygulanmaz. Yazılım efektleri servis çalışırken üretilir; fare belleğine kayıt, mevcut renk karesini kaydeder ve animasyon motorunu firmware'e taşımaz.

`list-profiles` en fazla 32 dosyalık sayfa döndürür; `--offset`, `--limit` veya `--all` ile diğer sayfalar alınır. Bozuk dosyalar atlanır ve ayrıca bildirilir; profil sayısı sınırında onlar da hesaba katılır. Profil JSON'u en fazla 32 KiB olabilir. İçe aktarma önce dosyayı doğrular, USB'ye yazmaz; uygulamak için ayrı `apply-profile` gerekir. Aynı adlı profil veya dışa aktarma dosyası için `--overwrite` açıkça verilmelidir. Dosya yolu servise iletilmez.

Başarılı komut çıkış kodu `0`, servis/cihaz hatası `1`, argüman hatası `2` döndürür. `muvv reconnect 1` bağlantıyı yeniden açar; yeni bağlantıda okunamayan ayarlar tekrar bilinmiyor olur.

`muvv doctor` HID cihazı açmaz, servis başlatmaz ve dizin oluşturmaz. Tk modülünün bulunması grafik ekranın veya gerçek USB bağlantısının çalıştığını kanıtlamaz. Windows'ta Linux cihaz desteği uyarısı beklenir.

## Geliştirme ve test

```bash
python -m pip install -e ".[gui,dev]"
python tools/check.py --json test-results.json
python tools/simulation_check.py --cycles 50 --json simulation-results.json
ruff check .
ruff format --check .
python -m build
pip-audit --require-hashes --disable-pip -r requirements-lock.txt
```

Otomatik testler gerçek HID açmaz. Linux'a özgü soket/izin testleri Windows'ta, GUI testleri ekran veya arayüz bağımlılığı yoksa atlanır. Linux CI dosyası çekirdek ve masaüstü kontrollerini ayırır.

Sanal senaryo aracı bellek içi USB, geçici profil dizini ve yerel socketpair kullanır. Varsayılan koşu 500 parçalı mesaj, sekiz eşzamanlı üreticiden 400 işlem, 50 yeniden bağlantı/profil aktarımı ve dört USB kesilme noktasını denetler. Linux UID/izin veya fiziksel fare kabulünü çalıştırmaz. `--cycles` 1–200, `--seed` tekrar üretilebilir mesaj parçalamayı belirler.

Gerçek cihaz testleri için [donanım kabul listesi](docs/HARDWARE-ACCEPTANCE.md) ve `tools/hardware_check.py --help` kullanılır. Eski `test/hardware/` dosyaları bu araca yönlendiren manuel girişlerdir; otomatik test olarak toplanmazlar.

## Teknik belgeler

- [Mimari ve genişletme](docs/ARCHITECTURE.md)
- [IPC sözleşmesi ve geçiş](docs/IPC.md)
- [Güvenlik sınırları](SECURITY.md)
- [Değişiklikler](CHANGELOG.md)
- [Rival 3 protokol notları](docs/SteelSeries/Rival%203%20Gen%202/tr/)

USB yazma sonucu, verinin sürücüye teslim edildiğini gösterir. Sensör davranışı ve firmware'de kalıcılık gerçek fareyle ayrıca doğrulanmalıdır.
