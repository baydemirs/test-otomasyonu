# GOREV-009 — Kanıt Güvenliği ve Rapor Koruması

## Kapsam ve bağımlılık

Kaynak: Kullanıcının 2026-10-15 talimatı. Bağımlılık: GOREV-004.
CanRat ortak kanıt değerlendirmesindeki (`evaluate_run_evidence`) güvenlik açıklarını kapatmak, süreç sahipliği ve jurnal denetimlerini derinleştirmek ve HTML rapor çıktısının ham kanıtları korumasını sağlamak. Kapsam yeni özelliklerle genişletilmez; yeni masaüstü testi çalıştırılmaz.

## Kabul kriterleri

1. **Başarılı koşunun zorunlu alanları:**
   - Köprüde (`pytest-link.json`) test kimliği (`test_id`), koşu kimliği (`run_id`), durum (`status`), çıkış kodu (`exit_code`), beklenen durumlar (`expected_states`) ve gözlemlenen durumlar (`observed_states`) eksiksiz bulunmalıdır.
   - UI ve yaşam döngüsü kayıtlarının kimlikleri (`process_id`, `process_start_ticks`) ve bağlantıları aynı koşuyu göstermelidir.
   - Eksik alanlara başarı varsayılanı verilmez.

2. **UI işleminin tamamlanması:**
   - Başarılı kayıtta uygun şema/mod (`schema_version=1`, `mode='Exercise'`), tamamlanmış aşama (`phase='completed'`), işlem ve temizlik bilgileri (`cleanup_attempted=True`, `mutation_attempted=True`, `restored=True`) bulunmalıdır.
   - `changed_verified=False`, yarım aşama, eksik adım veya geri yükleme hatası (`cleanup_error`) doğrulanmış başarı üretmemelidir.
   - Başlangıç → karşıtı → başlangıç kuralı eksiksiz uygulanır.

3. **Süreç sahipliği ve adımlar:**
   - Kapalı başlangıçta (`Closed`) sahiplik (`owned=True`) zorunlu olmalıdır.
   - Önceden açık uygulamada (`Existing`) sahiplik olmamalı (`owned=False`) ve süreç kapatılmamış olmalıdır (`close.status='ACIK_BIRAKILDI'`, `request_sent=False`, `still_running=True`).
   - Alt test sonucu, üst test sonucu, süreç kimliği, başlangıç modu ve kapatma bilgisi karşılaştırılmalıdır.
   - Temizlik hatası (`cleanup_error`) ve tüm hata alanları denetlenmelidir.
   - UI ve yaşam döngüsü adımları (jurnal dosyaları: `uia-adimlari.json`, `yasam-adimlari.json`) sonucun gözlemleriyle karşılaştırılmalı; boş, eksik veya çelişkili jurnal doğrulamayı bozmalıdır.

4. **Sonuçların sınıflandırılması:**
   - Pytest XML'indeki başarısızlık (`failure`) bir otomasyon hatasından (`pytest.fail`) kaynaklanıyorsa UI/yaşam döngüsündeki `HATA` otomatik olarak `KALDI`'ya çevrilmemelidir.
   - Gerçek yürütücü kayıtlarına göre tutarlı `GECTI`, `KALDI`, `HATA`, `ATLANDI` değerlendirilmeli; kanıt eksikliği ile çelişki birbirinden ayrılmalıdır.

5. **Ortak değerlendirme:**
   - HTML raporu yalnız `evaluate_run_evidence` çıktısını gösterir; kendi içinde bağımsız başarı türetmez.
   - `pytest_dogrula.py` sürüm ve komut denetimlerini koruyarak ortak değerlendirmeyi kullanır.
   - Tarihsel raporlar üretilirken o koşunun kanıtı değerlendirilir; mevcut kaynak hash'i ile eşleşme zorunluluğu aranmaz.

6. **Rapor dosyasının korunması:**
   - `--output` ile verilen rapor yolu; ham kanıt dosyalarını (`.json`, `.xml`, jurnaller) ezmeyi ve HTML dışındaki uzantıları reddeder.
   - Çıktı klasörü kanıt klasöründen farklıysa göreli dosya bağlantıları doğru hesaplanır.
   - Raporlama adımı başarısız olursa kayıtlı test sonucunu değiştirmez.
   - Rapor üretimi ham kanıtların özet değerlerini (`SHA-256`) değiştirmemelidir.
