# CANRAT-UI-002 gerçek etkileşim demosu

Tarih: 2026-10-13; gerçek koşu başlangıcı 10:31:27 Türkiye saati. Kabul kaynağı: [kullanıcı talimatından kaydedilen kriterler](../gereksinimler/CANRAT-UI-002.md).

## Gerçek sonuç

[Gerçek koşu JSON'u](kosular/canrat-ui-002-6b9739a5a4924ba4a0fca7b401aeb47f/sonuc.json) ve [UIA adım günlüğü](kosular/canrat-ui-002-6b9739a5a4924ba4a0fca7b401aeb47f/uia-adimlari.json): GECTI. PID 18480; yalnızca `MainWindow.centralwidget.cboxAppendRecieved` üzerinde etkileşim yapıldı.

| Adım | Beklenen | Gerçek gözlem |
| --- | --- | --- |
| Başlangıç | Kesin Off veya On | Off |
| Değişiklik | İlk değerin karşıtı | On; changed_verified=true |
| Geri yükleme | İlk değer | Off; restored=true |
| Start öncesi/sonrası | Off / Start | Off / Start; active=false |

Komut `py -3 tests/canrat_ui_002.py --mode Exercise`, mevcut komut bazlı onayla Codex araç çağrısından çalıştırıldı. Alt süreç ve komut çıkış kodu 0; raporlanan süre 2.419 saniye. Genel hata, geri yükleme hatası ve kurtarma ihtiyacı yok. Koşu EXE, Python yürütücü, PowerShell senaryosu, UIA bağlantısı ve kriter dosyasının SHA-256 özetlerini içerir. Uygulama sürümü ikili özetiyle tanımlandı; ürün sürüm numarası doğrulanmış sayılmadı.

Start yalnızca okundu; Start veya CAN bağlantısı tetiklenmedi. Uygulama açılmadı/kapatılmadı, güvenlik ayarı değiştirilmedi. Veri toplama etkinliği arayüz göstergesi üzerinden kontrol edildi; bu fiziksel CAN trafiği ölçümü değildir.

## Ön kontrol ve otomasyon hatası

[İlk salt okunur ön kontrol](kosular/canrat-ui-002-ab9a9695976c44e49e52c3f9975a3ce7/sonuc.json): kutu Off ve Start Off okundu, fakat günlük güncellemesinde File.Replace yedek yoluna PowerShell null aktarımı başarısız oldu. Sonuç HATA; mutation_attempted=false. Ürün hatası değildir. Yedek yolu açık verilerek düzeltildi; eski kayıt korundu.

[Düzeltilmiş ön kontrol](kosular/canrat-ui-002-e0096dcea6ad4fc7b5c6bcb11bb4ed05/sonuc.json): HAZIR, test_sonucu=null; Start iki okumada Off/Start, kutu Off. Gerçek etkileşim koşusu ön koşulları yeniden doğruladı.

## Kontroller ve sınırlar

Birim komutu `py -3 -m unittest discover -s tests/unit -v`: 16 test. Bunlar sahte gözlemlerle Off/On başlangıçlarını, belirsiz durumları, kararsız/doğrulanmamış sonucu, temizleme hatasını, aktif Start durumunu, bozuk kanıtı ve alt süreç süre aşımında kurtarma başarısı/başarısızlığının ayrı raporlanmasını denetler. Fiziksel uygulamada hata enjeksiyonu yapılmadı. [Birim kontrol çıktısı](kosular/canrat-ui-002-6b9739a5a4924ba4a0fca7b401aeb47f/birim-kontrolleri.txt) ayrı kayıttır.

Kanıt kontrolü: `py -3 araclar/demo_dogrula.py --report raporlar/kosular/canrat-ui-002-6b9739a5a4924ba4a0fca7b401aeb47f/sonuc.json`. Kontrol gerçekten çalıştırıldı, çıkış kodu 0 ve `DEMO_KANITI_DOGRULANDI` üretti. Kontrol, gerçek gözlem/sonuç uyumunu, dosya özetlerini, görev alanlarını ve ilgili belge yollarını denetler. Yeni UI etkileşimi yapmaz, belge üzerinden uygulamanın davranışını tekrar sınamaz ve görev durumunu kendiliğinden değiştirmez.

finally ile geri yükleme gerçek başarılı koşuda çalıştı. Sağlayıcı kilitlenmesi, kapanan uygulama, güç kesintisi veya insan müdahalesi halinde geri dönüş garanti edilemez. Böyle durumda bilinmeyen/Indeterminate değere tahminle Toggle uygulanmaz; sonuç HATA ve ayrı temizlik hatası olur. Kurtarma aynı PID ve süreç başlangıç zamanına bağlıdır. Mutex yalnızca diğer otomasyon koşularını sınırlar; kullanıcı tıklamasını engellemez.

Bu demo için gerçek hata/timeout enjeksiyonu, tekrar koşusu ve kesintiden devam denetimi GOREV-002 kapsamında ayrıca ele alınmalıdır. Kutunun UI durumu test edildi; log dosyası veya CAN iletişim davranışı bu koşudan çıkarılamaz.
