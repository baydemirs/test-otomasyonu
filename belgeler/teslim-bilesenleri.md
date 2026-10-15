# Teslim Bileşenleri ve Kapsam Sınırları

Bu belge, test otomasyon projesinin teslim bileşenlerini, paketleme modelini ve sınırlarını tanımlar. Kurulum ve çalıştırma komutları için ana kaynak [README.md](../README.md) rehberidir.

## 1. Teslim Bileşenleri

Proje üç ana bileşen olarak ele alınır:

1. **Kaynak Kod ve Otomasyon Deposu (Git / GitHub):**
   - Python ve PowerShell betikleri, birim testleri, pytest konfigürasyonu, görev ve durum kayıtları, mimari belgeler.
   - Herkese açık depoda tutulur (`main` dalı).
   - `.gitignore` kuralları uyarınca ikili dosyalar (`.exe`, `.dll`), sanal ortam (`.venv`), geçici önbellekler ve ham koşu kanıtları bu depoya dahil edilmez.
2. **Hedef Uygulama Paketi (Harici Paket):**
   - `CANRAT_3min.zip` arşivi harici olarak sağlanır.
   - Otomasyon kodundan bağımsızdır ve telif/dağıtım sınırları nedeniyle Git deposunda yer almaz.
   - İlgili arşiv, [hedef_uygulama/README.md](../hedef_uygulama/README.md) rehberine göre `hedef_uygulama/CANRAT_3min/CANRat.exe` yoluna açılır.
3. **Tarihsel Koşu Kanıtları (Yerel Çalışma Alanı):**
   - Geçmiş görevlere ait ham kayıtlar (`raporlar/kosular/` altındaki JSON/XML kanıtları ve `rapor.html` dosyaları) yerel geliştirme alanında saklanır.
   - Bu kayıtlar üretildikleri andaki kaynak sürümlerinin (`git commit` ve SHA-256 özetlerinin) tarihsel kanıtıdır; kod tabanında değişiklik yapıldığında taşınan güncel kodun otomatik kanıtı sayılmaz.
   - Temiz bir klonda geçmiş kanıtlar bulunmasa dahi tüm birim testleri bağımsız sentetik fixture verileriyle çalışır; görev şeması ve bağımlılıkları `python otomasyon/dogrulama/demo_dogrula.py --structure-only` ile doğrulanabilir.

## 2. Kapsam ve Çalışma Sınırları

- **Test Kapsamı:** Tek bir UI kontrolünün (`MainWindow.centralwidget.cboxAppendRecieved`) başlangıç, karşıt ve geri dönüş durumlarını (`Off → On → Off`) doğrulamakla sınırlıdır.
- **Güvenlik ve Masaüstü Sınırları:**
  - `Start` butonuna basılmaz, CAN bağlantısı başlatılmaz.
  - Kullanıcıya ait açık CanRat örneği kapatılmaz.
  - Başlatma ve kapatma işlemleri (`Closed` modunda) yalnızca otomasyonun kendi başlattığı süreç için geçerlidir.
- **Ortam Gereksinimi:** Masaüstü koşusu için Windows 10/11 etkileşimli masaüstü oturumu gereklidir. Temiz bir kopyada masaüstü testi varsayılan olarak atlanır; yalnızca açıkça `--run-desktop` bayrağı verildiğinde çalışır.
