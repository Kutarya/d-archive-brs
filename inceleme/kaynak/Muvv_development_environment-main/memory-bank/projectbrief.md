# Project Brief

## Vizyon
Muvv, Linux ekosisteminde donanım üreticilerinin (SteelSeries, Razer, Logitech vb.) sağlamadığı resmi yazılım desteğini, topluluk odaklı, tamamen modüler ve hacklenebilir bir yapıda sunmayı amaçlayan bir "Çatı Uygulama" (Framework) projesidir. Her fareyi "yaşayan bir kod parçası" olarak ele alır.

## Temel Amaçlar
*   **Marka Bağımsızlık:** Tek bir markaya hapsolmadan, herkesin kendi faresi için eklenti (driver) yazabilmesi.
*   **Modülerlik:** Sürücü, Animasyon, Yönetici ve Arayüz katmanlarının ayrıştırılması.
*   **Açık Kaynak:** Topluluk destekli geliştirme.
*   **Linux Odaklı:** `udev` kuralları ve Linux mimarisine uygun yapı.

## Kapsam
*   **Sürücü Katmanı:** USB HID protokolü ile cihaz iletişimi.
*   **Animasyon Motoru:** "Vitray" mantığı ile ışık/renk animasyonları.
*   **Yönetici:** Sistem bileşenlerini koordine eden daemon (Donanım Bağımsız).
*   **GUI:** Kullanıcı arayüzü (CustomTkinter).
