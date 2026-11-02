# Geliştirme Ortamı Detayları

Bu bölüm, projenin geliştirme ortamı, klasör yapısı ve çalışma sırasında dikkat edilmesi gereken kuralları içerir.

## Klasör Yapısı

Geliştirme ortamı varsayılan olarak iki ana klasörden oluşmaktadır:

* **`development_environment`**: Geliştirme ortamına dair yapılandırmaların, Memory Bank kayıtlarının ve `proje.md` gibi sistem dosyalarının bulunduğu klasör.
* **`Muvv`**: Projenin asıl kaynak kodlarının, sürücü dosyalarının ve geliştirme sürecinin yürütüleceği ana klasör.

---

## Dikkat Edilmesi Gerekenler

### 1. Memory Bank Yönetimi
Tüm **Memory Bank** dosyaları (proje hafızası) `development_environment` klasörü altında saklanmalıdır. 
**Yapı:** `development_environment/memory-bank/` -> `progress.md`, `activeContext.md`, `techContext.md` vb.

### 2. Proje Bilgileri
Proje hakkındaki genel bilgilere ve açıklamalara `development_environment` klasörü altındaki **`proje.md`** dosyasından ulaşılabilir.

### 3. Veri İzolasyonu ve Git Politikası
Geliştirme ortamı verileri ile **Muvv** projesinin verileri kesinlikle birbirine karıştırılmamalıdır.  

* **Git Yönetimi:** `development_environment` klasörü, projenin asıl repo geçmişini kirletmemesi için `.gitignore` dosyasına eklenerek ana repo dışında tutulmalıdır.
* **Venv (Sanal Ortam):** Python sanal ortamı (`.venv`), proje kök dizininde bulunmalı ancak **kesinlikle Git'e yüklenmemelidir.** Bunun yerine bağımlılıklar `requirements.txt` dosyasında tutulmalıdır.

### 4. Test Yapılandırması
Test dosyaları, `Muvv` klasörü altında bulunan **`test`** ana dizininde, kategorize edilmiş şekilde tutulmalıdır.

# Güncelleme  

### 5. Git yönetimi
Şu anda 'Muvv' ve 'development_environment' klasörleri ayrı git depoları olarak yönetilmektedir. Commit atılacağında 'Muvv' klasörünün commit'i ayrı, 'development_environment' klasörünün commit'i ayrı atılmalıdır.