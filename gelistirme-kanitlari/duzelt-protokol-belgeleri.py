from pathlib import Path

root = Path("D:/BRS/Muvv/docs/SteelSeries/Rival 3 Gen 2/tr")
buttons = root / "Tuş Atama Dökümanı.md"
text = buttons.read_text(encoding="utf-8")
text = text.replace("dahili hafızasını (EEPROM) yönetmek, tuş atamalarını değiştirmek ve makro yazmak", "tuş atamalarını değiştirmek ve kaydetme komutu göndermek")
text = text.replace("packet[6] = 0x01 # Fiziksel Sağ Tuş -> Sol Tık yapar\n", "packet[6] = 0x01 # Fiziksel Sağ Tuş -> Sol Tık yapar\n" + chr(96)*3 + "\n")
text = text.replace("h.write(bytes(save_packet))\n", "h.write(bytes(save_packet))\n" + chr(96)*3 + "\n")
marker = "## 5. Python Şablon Kodu (Skeleton)"
text = text[:text.index(marker)] + """## 5. Uygulama üzerinden deneme

Ham HID şablonu yerine doğrulama ve USB sonuç takibi yapan CLI kullanılabilir:

FENCEbash
muvv bind-key button5 0xE1 1 --initialize --no-persist
muvv restore-buttons 1 --no-persist
muvv save 1
FENCE

İlk komut okunamayan tüm tuş düzenini varsayılanlarla başlatır ve Button 5'i sol Shift yapar. Varsayılanlar fareden alınmış bir yedek değildir. Kalıcı kayıt ayrıca seçilir; sonucunu yeniden bağlantıdan sonra fiziksel cihazda kontrol edin.

Bu protokol notunda klavye tuşu ataması vardır; genel makro kaydetme/oynatma desteği uygulanmış değildir.
""".replace("FENCE", chr(96)*3)
buttons.write_text(text, encoding="utf-8")

color = root / "Renk dökümantasyonu.md"
text = color.read_text(encoding="utf-8")
marker = "## 3. Python Komut Örneği"
text = text[:text.index(marker)] + """## 3. Uygulama üzerinden deneme

FENCEbash
muvv set-color FF0080 1
muvv set-effect wave -d 1 --color 00FF00 --speed 0.5
muvv save 1
FENCE

İlk iki komut aydınlatmayı değiştirir. Kaydetme komutu ayrıca gönderilir; renk paketi tek başına kalıcı kayıt kanıtı değildir. Yazılım animasyonu servis çalışırken hesaplanır.

Tüm bölgeleri güncelleyen sürücü 0x07 maskesi kullanır. Tek bölgeye yönelik protokol denemesi ayrıca tam üç bölge baytlarını hazırlamalı ve yalnızca hedef maskeyi seçmelidir. Güncel GUI/CLI tüm bölgeler için efekt uygular.
""".replace("FENCE", chr(96)*3)
text = text.replace("ortansında", "ortasında")
color.write_text(text, encoding="utf-8")

dpi = root / "DPI dökümantasyonu.md"
text = dpi.read_text(encoding="utf-8")
marker = "Aşağıdaki script,"
offset = text.index(marker)
text = text[:offset] + """Beş kademe birlikte yazılır. Uygulama örneği:

FENCEbash
muvv set-dpi-stages 400 800 1200 2400 3200 -d 1 --active 1
muvv set-polling 500 1
muvv save 1
FENCE

Etkin kademe CLI'de 0–4 aralığındadır. İlk komut beş değeri açıkça değiştirir. Önceki slotlar firmware'den okunmadığı için kısmi seçim, bilinen slot düzeni veya açık varsayılan başlangıç gerektirir.

USB yazımının başarılı dönmesi sensör hızının ya da kalıcılığın fiziksel doğrulaması değildir. Donanım kabulünde her kademe ve güç döngüsü ayrıca denenir.
""".replace("FENCE", chr(96)*3)
dpi.write_text(text, encoding="utf-8")

