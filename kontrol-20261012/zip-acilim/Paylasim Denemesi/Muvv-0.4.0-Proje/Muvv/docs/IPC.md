# IPC sürüm 1

Linux Unix stream socket üzerinde her bağlantı bir istek ve bir yanıt taşır. Soket yolu CLI ve servis için aynı XDG kurallarıyla hesaplanır.

## Çerçeve

İlk dört bayt, big-endian işaretsiz gövde uzunluğudur. Ardından belirtilen sayıda UTF-8 JSON baytı gelir. İstek en fazla 16384, yanıt en fazla 65536 bayttır. Başlık ve gövde parçalı gelebilir; alıcı tam uzunluk tamamlanana kadar okur.

JSON özel sayıları ve `1e999` gibi float taşmaları, yinelenen anahtarlar, nesne olmayan üst değer, geçersiz UTF-8 ve aşırı derin veri reddedilir. Stream socket'te bir `recv` çağrısı mesaj sınırı değildir. [Python socket açıklaması](https://docs.python.org/3.12/howto/sockets.html).

```json
{"version":1,"command":"set-dpi-stages","args":{"device":"1","stages":[400,800,1200,2400,3200],"active":1}}
```

`version` yoksa sürüm 1 varsayılır; başka sürüm reddedilir. Bilinmeyen üst alanlar ve komut argümanları hata döndürür.

## Sonuç

```json
{"status":"ok","transport":"written","reports":1,"bytes_written":64,"readback_verified":false}
```

```json
{"status":"error","code":"unknown_device_state","message":"DPI slots have not been read. Set all five slots or explicitly initialize defaults."}
```

`transport: written` HID yazımının başarıyla döndüğünü bildirir. Cihaz firmware'inden geri okuma yapılmaz. `persistence_requested: true` kaydetme komutunun gönderildiğini söyler; yeniden açılışta kalıcılık kanıtı değildir.

Hata kodları: `invalid_request`, `invalid_argument`, `device_not_found`, `ambiguous_device`, `device_busy`, `unknown_device_state`, `transport_error`, `operation_uncertain`, `busy`, `response_too_large`, `internal_error`.

0.3 bağlantı koruması için `device_changed` eklenir. `list` cihazlarında ve `info`/`snapshot` durumunda `session_id`, her başarılı bağlantıda değişen 32 küçük hex karakterdir. USB yolunun aynı olması oturumun aynı olduğu anlamına gelmez.

Cihazı değiştiren komutlar, `save-profile` ve `reconnect`, isteğe bağlı `expected_session` kabul eder. Kontrol cihaz komut kilidi alındıktan sonra yapılır; uyuşmazlık hiçbir rapor göndermeden `device_changed` döndürür. Diğer komutlarda alan reddedilir. Arayüz alanı kullanır; eski CLI çağrıları alanı göndermediği için uyumlu kalır. Bu alan UID kontrolünün yerine geçmez.

```json
{"version":1,"command":"set-polling","args":{"device":"/dev/example","hz":500,"expected_session":"0123456789abcdef0123456789abcdef"}}
```

Kuyrukta beklerken yazımı başlamadan iptal edilen işlem `device_busy` döndürür; bu işlem cihaza gönderilmez. Başlamış USB çağrısı süreyi aşarsa `operation_uncertain` döner, yeni yazımlar durur ve yeniden bağlantı gerekir. İşlem tamamlandığı halde yanıt 64 KiB sınırını aşarsa küçük bir `response_too_large` yanıtı ve `operation_completed: true` verilir. Yazma komutunu otomatik tekrarlamayın.

## Komutlar

| Komut | Argümanlar |
|---|---|
| list, status, effects | Yok |
| list-profiles | İsteğe bağlı offset (0–128), limit (1–32) |
| snapshot | İsteğe bağlı device |
| info, save, reconnect, stop-effect | device |
| set-color | device ve color veya hex |
| set-colors | device, colors (wheel/middle/underglow tam RGB haritası) |
| set-effect | device, effect ve efektin ilan ettiği seçenekler |
| update-effect | device ve mevcut efektin seçenekleri |
| set-dpi | device, level, isteğe bağlı initialize |
| set-dpi-stages | device, stages, isteğe bağlı active |
| set-polling | device, hz |
| bind-key | device, button, key_code, isteğe bağlı initialize/persist |
| restore-buttons | device, isteğe bağlı persist |
| set-button | device, button, assignment; isteğe bağlı initialize/persist |
| save-profile | device, name, isteğe bağlı overwrite |
| show-profile, delete-profile | name |
| apply-profile | device, name, isteğe bağlı persist |
| rename-profile | name, new_name |
| import-profile | Doğrulanmış profile nesnesi, isteğe bağlı overwrite |

Sayısal değerler JSON integer, bayraklar boolean olmalıdır. Boolean DPI seviyesi veya kesirli tuş kodu integer'a çevrilmez. Renk tam altı hex hane veya üç integer RGB kanalıdır.

`snapshot` cihaz listesi, seçili cihazın capability/durumu, servis durumu ve ilk profil sayfasını döndürür. Cihaz bilgisi okunamazsa `device_error`, profil sorunu varsa `profile_errors` ayrıca verilir. `list-profiles` ve `snapshot` yanıtlarında `profiles`, `profile_errors`, `profile_count`, `next_offset`, `profile_limit_exceeded` bulunur. `next_offset: null` son sayfadır. Profiller sayfa sınırları içinde atlanan bozuk dosyalar nedeniyle 32'den az olabilir.

0.4 kataloglarında `catalog_id`, dosya adları, kimlikleri, boyutları, zamanları ve bağlantı/izin bilgilerinin SHA-256 değeridir. Aynı adlı profilin üzerine yazılması da kimliği değiştirir. Sayfalar arasında farklıysa liste tekrar okunmalıdır. Sayfa okunurken dosya listesi veya dosya bilgileri değişirse o okuma reddedilir. Bu kimlik dosya içeriğinin hash'i veya diskin işlemsel anlık görüntüsü değildir; içerik uygulamadan önce tekrar doğrulanır. 0.3 yalnızca dosya adlarını kapsıyordu. `profiles_complete` ve `profile_refresh_error` ortak istemcinin yerel ek alanlarıdır; IPC yanıtı oldukları varsayılmamalıdır.

`snapshot` listeyi, seçimi ve servis durumunu birlikte alır; USB işlemini beklerken yönetici kilidini tutmaz. Seçilen bağlantının oturumu bu sırada değişirse `info: null` ve `device_error.code: device_changed` döner. Katalog kullanılamazsa `profile_catalog_error` nedenini taşır; cihaz bilgileri korunur.

İçe/dışa aktarma dosya yollarını CLI/GUI işler; IPC yalnızca profil nesnesini taşır. `doctor` ve `--version` istemcide çalışır, servis komutu değildir. Sürüm 0.2 profil JSON şemasını değiştirmez; 0.1 profilleri yeniden yazım gerektirmeden kullanılabilir. 0.1'de sayfasız olan `list-profiles` tüketicileri `next_offset` alanını izlemelidir.

## Eski sürümden geçiş

Eski taşıma ham JSON ve tek `recv(4096)` kullanıyordu. Yeni servis ve istemci birlikte güncellenmelidir. Ham JSON otomatik olarak tahmin edilmez. Eski `set-color` için `hex` alanı korunur; aynı istekte `hex` ve `color` birlikte kullanılamaz.

Tam cihaz ID'si önce, liste indeksi sonra çözülür. Varsayılan cihaz sıralanmış aktif listenin ilk elemanıdır. Birden çok cihaza uyan kısa ad hata döndürür; indeksler cihaz ekleme/çıkarma sırasında değişebileceği için kalıcı otomasyonda tam ID kullanın.
