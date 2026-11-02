# Python Environment Setup Guide

## Genel Bakış
Proje bağımlılıklarını izole etmek için `Muvv/` klasörü altında yerel bir Python sanal ortamı (`.venv`) kullanılır.

## Kurulum (Otomatik Olarak Yapıldı)
Aşağıdaki adımlar kurulum sırasında uygulanmıştır:

1.  **Sanal Ortam Oluşturma:**
    ```bash
    cd Muvv
    python3 -m venv .venv
    ```

2.  **Bağımlılıkları Yükleme:**
    ```bash
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Kullanım

### Ortamı Aktif Etme
Geliştirme yaparken veya projeyi çalıştırırken sanal ortamı aktif etmelisiniz:

```bash
source Muvv/.venv/bin/activate
```

### Yeni Bağımlılık Ekleme
Eğer projeye yeni bir kütüphane eklerseniz, `requirements.txt` dosyasını güncellemeyi unutmayın:

1.  Kütüphaneyi kurun: `pip install kütüphane_adı`
2.  Dosyayı güncelleyin: `pip freeze > requirements.txt` (veya manuel ekleyin).

## Git Politikası
*   `.venv/` klasörü `.gitignore` dosyasına eklenmiştir ve Git deposuna **gönderilmez**.
*   `requirements.txt` dosyası Git deposunda **takip edilir**.
