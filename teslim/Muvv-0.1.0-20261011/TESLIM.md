# Muvv 0.1.0 yerel teslimi

11 Ekim 2026. Kaynak ZIP'inden hazırlanan özel geliştirme kopyası.

- `Muvv-0.1.0-kaynak.zip`: iki güncel kaynak deposu, 84 dosya.
- `Muvv-0.1.0-inceleme.zip`: aynı kaynaklar, raporlar, test kanıtları, arayüz görüntüleri, yamalar ve kurulum paketleri.
- Wheel ve tar.gz: Python kurulumu ve kaynak dağıtımı. Kaynak README'sindeki hashli kurulum yolu önerilir.
- İki `.patch`: kendi depolarının başlangıç ZIP'ine göre değişiklikler.
- `SHA256SUMS.txt`: bu klasördeki teslim dosyalarının SHA-256 değerleri.

İnceleme ZIP'ini ayrı bir klasöre açıp `GELISTIRME-RAPORU.md` ile başlayın. Uygulama komutları `Muvv/README.md` içindedir. Demo `muvv-gui --demo` ile açılır; USB cihazı kullanmaz.

Yerel test sonucu: 89 toplam, 78 geçti, Linux gerektiren 11 atlandı; hata/başarısızlık yok. Linux IPC/izin, udev/systemd ve fiziksel fare kabulü bekliyor. GitHub CI çalıştırılmadı ve yayın yapılmadı.

Yamayı ilgili özel repo için ayrı inceleme dalında kontrol edin. Başlangıçtan sonra repo değiştiyse çakışmaları ayrıca çözün; `--reject` veya zorla uygulama ile hatayı geçiştirmeyin. Windows'ta satır sonu dönüşümünü önleyen kontrol örneği:

```bash
git -c core.autocrlf=false -c core.eol=lf apply --check /path/to/Muvv.patch
git -c core.autocrlf=false -c core.eol=lf apply /path/to/Muvv.patch
```

Diğer yama geliştirme notları deposuna ayrı uygulanır. İki yama başlangıçların ayrı kopyalarına uygulanıp 84 güncel dosyayla birebir karşılaştırıldı. ZIP'ler Git geçmişi içermez. Kaynaklarda yayın lisansı belirlenmediğinden paylaşım/yayın koşullarını repo sahibi netleştirmelidir.

İnceleme ZIP'indeki `DOSYA-MANIFEST.json` paketlenen dosyaları listeler. ZIP içindeki `SHA256SUMS.txt` yalnızca ZIP içindeki dosyaları, dış klasördeki aynı isimli dosya ise dış teslim dosyalarını doğrular; her biri kendisini kapsam dışı tutar.

`gelistirme-kanitlari/gelistirme-bagimlilik-denetimi.json` ilk pip taramasıdır. Son durum `gelistirme-bagimlilik-denetimi-son.json` içindedir. Test kaydındaki root/başlangıç hata mesajları beklenen negatif senaryolardır; son toplamda başarısız test yoktur.

Kanıt yardımcıları bu Windows çalışma klasörüne aittir. Taşınabilir proje testleri `Muvv/tools/check.py` ve `Muvv/test/` içindedir. Orijinal ZIP'ler ve başlangıç kopyaları yerel inceleme alanında korunmuştur.
