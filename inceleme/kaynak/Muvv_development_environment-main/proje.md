# Open Source Modular Linux Mouse Driver & Animation Engine
**Teknik Tasarım ve Mimari Dökümantasyonu**

## 1. Proje Vizyonu ve Felsefesi
Bu projenin temel amacı, Linux ekosisteminde donanım üreticilerinin (SteelSeries, Razer, Logitech vb.) sağlamadığı resmi yazılım desteğini, topluluk odaklı, tamamen modüler ve hacklenebilir bir yapıda sunmaktır. 

Bu proje her fareyi **yaşayan bir kod parçası** olarak ele alır. Tek bir markaya hapsolmadan, herkesin kendi faresi için eklenti (driver) yazabileceği bir "Çatı Uygulama" (Framework) geliştirilecektir.

---

## 2. Teknoloji Yığını (Tech Stack)

* **Çekirdek (Core):** Python 3.10+ (Hızlı prototipleme ve dinamik sınıf yapısı için).
* **Donanım Erişimi (I/O):** `hidapi` (Cython/C types). USB HID cihazlarına *byte* seviyesinde erişim, packet sending/receiving (bit-banging) için.
* **Eşzamanlılık:** `threading` + `queue` (Thread-Safe USB İletişimi).
* **Arayüz (GUI):** `CustomTkinter`. Modern, DPI-aware ve şık bir kullanıcı deneyimi için.
* **Veri Yapıları:**     
    * **NumPy:** Vektörel işlemler ve bellek dostu RGB matris yönetimi.
    * **Numba (İleri Safha):** Animasyon hesaplamalarını makine koduna (JIT) derleyerek CPU yükünü minimize etmek için..

---

## 3. Mimari Katmanlar (Architecture Layers)

Sistem 4 ana katmandan oluşur: **Driver (Sürücü)**, **Artist (Animasyon)**, **Manager (Yönetici)** ve **GUI (Arayüz)**.

### 3.1. Sürücü Katmanı (The Driver Layer) - `drivers/`
Eski nesil "JSON Config" yapısı yerine, **Python Sınıfı (Class)** yapısı benimsenmiştir.

* **BaseMouse (Ata Sınıf):** Tüm sürücülerin miras alacağı şablon sınıftır. `connect()`, `disconnect()`, `set_color()`, `set_dpi()`, `save_profile()` gibi soyut metodları barındırır.
* **Dinamik Yapı:** Her fare (örn: `Rival3.py`) kendi protokolünü kendi yönetir. Checksum hesaplama, Handshake (tokalaşma) veya paketleri parçalara bölme işlemi bu sınıfın içindedir.
* **Virtual State (Sanal Durum):** Sürücü, farenin LED durumunu RAM üzerinde bir liste olarak tutar. Fiziksel cihaza veri sadece `flush()` veya `update()` çağrıldığında gönderilir.

### 3.2. Vitray (The Animation Engine) - `animations/`
Animasyon sistemi donanımdan tamamen soyutlanmıştır. Motor, hangi fareyi yönettiğini bilmez, sadece elindeki matematiksel veriyi işler.

* **Vitray (Stained Glass) Mantığı:**
    * **Color Map (Harita):** Kullanıcının seçtiği renkler sabit bir zemin gibidir.
    * **Brightness Mask (Işık):** Animasyon aslında rengi değil, "Işık Şiddetini" (Brightness) hareket ettirir.
    * **Sonuç:** Işık (Maske) Harita (Renk) üzerinde gezer. Bu sayede fiziksel olarak pürüzsüz geçişler (additive blending) sağlanır.
* **Interpolasyon:** "Küt" geçişler yerine 0.0 - 1.0 arası float değerler ve matematiksel fonksiyonlar (Sine, Linear) kullanılır.
* **Zone Mapping:** LED'leri mantıksal gruplara ayırma (Örn: Logo, Scroll, Side).

### 3.3. Yönetici Katmanı (The Manager) - `managers/`
Sürücü ve Animasyon motorunu birbirine bağlayan "Beyin" katmanıdır.
* Donanım bağımsızdır.
* Takılı cihazı algılar, uygun sürücü sınıfını (Driver Class) yükler (Instantiation).
* Animasyon döngüsünü (Loop) başlatır ve üretilen kareleri (Frame) sürücüye iletir.
* Daemon (Servis): Arka planda sessizce çalışır, hidapi ve animations burada döner.
* GUI (Client): Sadece Daemon'a "Rengi kırmızı yap" diye emir yollar (Socket veya Named Pipe üzerinden).
* Böylece kullanıcı arayüzü kapatsa bile arkada "Artist" çalışmaya devam eder.

---

## 4. Donanım Özellikleri ve Protokol Yönetimi

### 4.1. DPI ve Sensör Ayarları
DPI değişimi yazılımsal değil, donanımsal protokol üzerinden yapılacaktır.
* Kullanıcı GUI üzerinden DPI kademelerini seçer.
* Driver sınıfı, bu değerleri cihazın anlayacağı Hex paketine çevirip `hid_write` ile cihaza gömer.
* Cihazın dahili hafızasına (On-board memory) kayıt yapılır.

### 4.2. Tuş Atama (Key Mapping & Macros)
* **Yöntem:** Farenin desteklediği **Donanımsal Atama Protokolü** kullanılacaktır.
* **İşleyiş:** Kullanıcı "Yan tuşa M tuşunu ata" dediğinde, Mouse bunu kaydeder direk mouseden çalışır.
* *Not: Bu özellik sadece protokolü çözülmüş ve tuş atamalarını kaydetme özelliği olan farelerde çalışır.*

---

## 5. Kritik Risk Analizi ve Çözümler (Risk Assessment)

Projenin geliştirme sürecinde dikkat edilmesi gereken teknik darboğazlar:

### Hata Yönetimi ve Cihazın Kilitlenmesi
* **Risk:** Yazılımın, cihaza hatalı bir paket gönderip çökmesi durumunda, cihaz "garip" bir modda kalabilir.
* **Çözüm:** `try-finally` blokları ile yazılım kapanırken mutlaka `disconnect()` ve `reset_state()` metodları çağrılmalıdır.

### Kullanıcı kaydete bastığında o anki animasyon işlemi ile çakışma riski.
* **Risk:** Kullanıcı tam kaydete bastığında mouseye aynı anda ışık veriside gider gariplik veya soft brick vs. olabilir.
* **Çözüm** queue kullamak burada mantıklı olabilir.


---

## 6. Kurulum ve Sistem Entegrasyonu (UX)

### udev Kural Yönetimi (Linux Specific)
Linux'ta USB cihazlara erişim `root` yetkisi gerektirir. Kullanıcı deneyimini iyileştirmek için:
* Uygulama ilk açılışta bir "Kurulum Sihirbazı" sunar.
* Desteklenen farenin `VendorID` ve `ProductID` bilgilerini içeren bir `.rules` dosyasını `/etc/udev/rules.d/` altına yazar.
* Kullanıcının sadece bir kere şifre girmesi yeterli olur; sonrasında uygulama kullanıcı modunda (user-space) çalışır.

### Persistence (Kalıcılık)
* Uygulama kapandığında son kullanılan profil (Renkler, DPI, Tuşlar) JSON formatında `~/.config/ProjectName/` altına kaydedilir.
* Servis modu (Daemon) sayesinde bilgisayar açılışında bu ayarlar otomatik yüklenir.

---

Yol Haritası (Roadmap)

### Faz 1: The Prototype (Mevcut Durum)
- [x] SteelSeries Rival 3 Gen 2 Tersine Mühendislik (Tamamlandı).
- [ ] BaseMouse ve Driver yapısının kodlanması.
- [ ] Basit CLI (Komut Satırı) üzerinden renk değiştirme testi.

### Faz 2: The UI & Engine
- [ ] Animasyon motorunun (Vitray mantığı) entegrasyonu.
- [ ] CustomTkinter arayüzünün giydirilmesi.
- [ ] Arka plan servisi (Daemon) ve Tray Icon.

### Faz 3: The Input (Riskli Bölge)
- [ ] `evdev` ile tuş dinleme ve makro altyapısı.
- [ ] Windows Porting (hidapi düzenlemeleri).