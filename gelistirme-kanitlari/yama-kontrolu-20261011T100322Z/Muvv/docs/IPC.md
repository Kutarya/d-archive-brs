# IPC sürüm 1

Linux Unix stream socket üzerinde her bağlantı bir istek ve bir yanıt taşır. Soket yolu CLI ve servis için aynı XDG kurallarıyla hesaplanır.

## Çerçeve

İlk dört bayt, big-endian işaretsiz gövde uzunluğudur. Ardından belirtilen sayıda UTF-8 JSON baytı gelir. İstek en fazla 16384, yanıt en fazla 65536 bayttır. Başlık ve gövde parçalı gelebilir; alıcı tam uzunluk tamamlanana kadar okur.

JSON özel sayıları, yinelenen anahtarlar, nesne olmayan üst değer, geçersiz UTF-8 ve aşırı derin veri reddedilir. Stream socket'te bir `recv` çağrısı mesaj sınırı değildir. [Python socket açıklaması](https://docs.python.org/3.12/howto/sockets.html).

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

Hata kodları: `invalid_request`, `invalid_argument`, `device_not_found`, `ambiguous_device`, `device_busy`, `unknown_device_state`, `transport_error`, `operation_uncertain`, `busy`, `internal_error`.

## Komutlar

| Komut | Argümanlar |
|---|---|
| list, status, effects, list-profiles | Yok |
| info, save, reconnect | device |
| set-color | device ve color veya hex |
| set-effect | device, effect ve efektin ilan ettiği seçenekler |
| update-effect | device ve mevcut efektin seçenekleri |
| set-dpi | device, level, isteğe bağlı initialize |
| set-dpi-stages | device, stages, isteğe bağlı active |
| set-polling | device, hz |
| bind-key | device, button, key_code, isteğe bağlı initialize/persist |
| restore-buttons | device, isteğe bağlı persist |
| save-profile | device, name, isteğe bağlı overwrite |
| show-profile, delete-profile | name |
| apply-profile | device, name, isteğe bağlı persist |

Sayısal değerler JSON integer, bayraklar boolean olmalıdır. Boolean DPI seviyesi veya kesirli tuş kodu integer'a çevrilmez. Renk tam altı hex hane veya üç integer RGB kanalıdır.

## Eski sürümden geçiş

Eski taşıma ham JSON ve tek `recv(4096)` kullanıyordu. Yeni servis ve istemci birlikte güncellenmelidir. Ham JSON otomatik olarak tahmin edilmez. Eski `set-color` için `hex` alanı korunur; aynı istekte `hex` ve `color` birlikte kullanılamaz.

Tam cihaz ID'si önce, liste indeksi sonra çözülür. Varsayılan cihaz sıralanmış aktif listenin ilk elemanıdır. Birden çok cihaza uyan kısa ad hata döndürür; indeksler cihaz ekleme/çıkarma sırasında değişebileceği için kalıcı otomasyonda tam ID kullanın.
