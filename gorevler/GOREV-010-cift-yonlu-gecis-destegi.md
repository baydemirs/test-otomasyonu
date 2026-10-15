# GOREV-010 — Çift Yönlü Durum Geçiş Desteği (Off ↔ On)

## Kapsam ve bağımlılık

Kaynak: Kullanıcının 2026-10-15 talimatı. Bağımlılık: GOREV-009.
CANRAT-UI-002 test senaryosunun her iki geçerli başlangıç durumunu (`Off → On → Off` ve `On → Off → On`) pytest köprüsü (`test_canrat_ui_002_pytest.py`), ortak kanıt değerlendiricisi (`ortak.py`), doğrulayıcılar (`pytest_dogrula.py`) ve HTML rapor üreticisi boyunca tam ve tutarlı desteklemek.

## Kabul kriterleri

1. **İki Geçerli Başlangıç Durumu Desteği:**
   - `Off → On → Off` ve `On → Off → On` döngülerinin her ikisi de geçerli ve doğrulanabilir kabul edilmelidir.
   - Geçiş beklentisi sabit `Off → On → Off` varsayımından arındırılmalıdır.

2. **Beklenen Geçişin Önceden Hesaplanması:**
   - Beklenen durumlar (`expected_states`), yalnızca işlem öncesinde kaydedilmiş geçerli başlangıç değerinden (`initial`) türetilmelidir:
     - İlk değer `Off` ise: karşıt `On`, son `Off` (`['Off', 'On', 'Off']`).
     - İlk değer `On` ise: karşıt `Off`, son `On` (`['On', 'Off', 'On']`).
   - Beklenti, gerçekleşen değişiklikten (`changed`) veya son değerden (`final`) türetilmemeli; bilinmeyen/geçersiz başlangıç durumunda tahmin yapılmamalı, geçersiz sayılmalıdır.

3. **Çapraz Katman Tutarlılığı:**
   - Köprü (`pytest-link.json`), UI (`sonuc.json`), yaşam döngüsü (`sonuc.json`) ve HTML rapor aynı beklentiyi tutarlı göstermelidir.
   - Gerçekleşen durumlar (`observed_states`) beklenen geçişle uyuşmadığında veya geri yükleme başarısız olduğunda kanıt kesinlikle doğrulanamamalıdır.

4. **Kural ve Güvenlik Bütünlüğü:**
   - CANRAT-UI-002 kabul kriteri ve eski ham kayıtlar değiştirilmez.
   - Ortak kanıt kontrolleri, süreç sahipliği, süre sınırları ve kurtarma mekanizmaları korunur.
   - HTML rapor üretimi ham kanıtların özet değerlerini (`SHA-256`) değiştirmemelidir.

5. **Gerçek Windows Doğrulaması ve Kanıt Korunması:**
   - Gerçek Windows'ta başlangıcı `Off` ve `On` olan iki ayrı koşu üretilmeli ve her koşu kendi başlangıç durumuna dönmelidir.
   - Hazırlık için kutu durumuna müdahale edilecekse, bütün işlem öncesindeki gerçek değer kaydedilmeli ve iş sonunda ona geri dönülmelidir.
   - Önceden açık kullanıcı süreci açık bırakılmalı; yalnız otomasyonun açtığı süreç normal kapatılmalıdır.
   - Start'a basılmaz, CAN bağlantısı başlatılmaz.
   - Oluşan tüm kanıtlar (JSON/XML, günlükler, komut çıktıları, HTML) yerelde silinmeden korunmalıdır.
   - Mevcut tarihsel raporların değerlendirilebildiği teyit edilmelidir.

## Doğrulama durumu ve kanıt sınırları

1. **Koşu 1 (Kapalı Başlangıç, Off):** `raporlar/kosular/pytest-gecis-843ce87a53ad4d419c0f541ab004b6cd/kapali` altında `Off → On → Off` döngüsü, normal süreç kapanışı (`KAPANDI`), tüm JSON/XML ve HTML kanıtlarıyla eksiksiz doğrulanmıştır.
2. **Koşu 2 (Önceden Açık, On):** `raporlar/kosular/pytest-gecis-4b21c9e914484b42859d165961fb3353/acik` altında PID 1000 sürecine bağlanılarak `On → Off → On` döngüsü ve `ACIK_BIRAKILDI` durumu pytest, yaşam döngüsü ve UI raporlarıyla eksiksiz doğrulanmıştır.
3. **PID 1000 Hazırlık ve Kapanış Kaydı Sınırı:** PID 1000 hazırlık örneğinin test öncesi ilk `Off` durumu, `On`'a getirilmesi ve test sonrasında tekrar `Off` yapılarak sürecin kapatılması adımları test yürütücüsünün terminal komut çıktısında yer almış; ancak bu hazırlık/kapanış katmanına ait diskte bağımsız, yapısal bir kanıt dosyası oluşturulmamıştır. Geçmiş olaya ait sonradan kanıt üretilmeyeceği kuralı gereğince, bu dış hazırlık, ilk durum ve geri yükleme/kapanış adımlarının diskteki kanıt dosyalarından bağımsız olarak doğrulanamadığı açıkça kayıt altına alınmıştır.
