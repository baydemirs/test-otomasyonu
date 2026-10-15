# Oturum devri

Bu not 2026-10-15 devir anının kısa özetidir. **Güncel görev durumu ve bağımlılıklar için tek asıl kaynak [görev kaydıdır](durum/gorev-durumu.yaml).** Yeni ajan ilk olarak [AGENTS.md](AGENTS.md) kurallarını ve bu kaydı salt okunur inceler; burada yazanları güncel dosya ve kanıtların yerine koymaz.

## Çalışan kapsam

Son tamamlanan iş [GOREV-010](gorevler/GOREV-010-cift-yonlu-gecis-destegi.md) (CANRAT-UI-002 onay kutusu testinde `Off → On → Off` ve `On → Off → On` çift yönlü durum geçiş desteği, dinamik beklenti türetimi, çapraz katman tutarlılığı ve gerçek Windows masaüstü koşuları); önceki aşamalar [GOREV-009](gorevler/GOREV-009-kanit-guvenligi-ve-rapor-korumasi.md), [GOREV-004](gorevler/GOREV-004-teslim-hazirligi.md), [GOREV-008](gorevler/GOREV-008-html-rapor.md) ve [GOREV-007](gorevler/GOREV-007-proje-sadelestirme.md) belgelerindedir. Tek aktif masaüstü senaryosu [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md): `MainWindow.centralwidget.cboxAppendRecieved` için başlangıç durumunu oku, karşıt durumu doğrula ve başlangıca dön. Aktif yol **pytest → PowerShell/.NET UIA**; pywinauto denemesi [arşivdedir](otomasyon/arsiv/pywinauto/README.md). Kullanım ve kurulum rehberi [README](README.md), teslim bileşenleri ve sınırları [Teslim Bileşenleri](belgeler/teslim-bilesenleri.md), teknoloji ve sahiplik kararları [Mimari Kararlar](belgeler/mimari-kararlar.md) içindedir.

Devir anında görev kaydında yarım iş görünmüyordu. Sıradaki somut adım, yeni ajanın kaynakları ve kanıtları **salt okunur** karşılaştırması, ardından kendisine verilen yeni görevin kabul kriterlerini belirlemesidir. Önceki ajanın yarım bıraktığı bir işlem saptanırsa gerçek dosya ve süreç durumu incelenmeden tekrarlanmaz. Aynı proje üzerinde iki geliştirme ajanı eşzamanlı çalışmaz.

## Doğrulanmış komutlar ve kanıtlar

Proje kökünden, mevcut `.venv` ile doğrulanmış komutlar (pytest yerel önbelleğe yazabilir; **ilk salt okunur incelemeden sonra** çalıştır):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --structure-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --tasks-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-843ce87a53ad4d419c0f541ab004b6cd/kapali --expected Closed
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder raporlar/kosular/pytest-gecis-843ce87a53ad4d419c0f541ab004b6cd/kapali
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-4b21c9e914484b42859d165961fb3353/acik --expected Existing
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder raporlar/kosular/pytest-gecis-4b21c9e914484b42859d165961fb3353/acik
```

GOREV-010 tamamlanması sonunda varsayılan pytest **106 geçti, 1 masaüstü testi atlandı** (6 yeni birim testi eklendi; `test_html_rapor.py` 60 teste ulaştı):
1. **Dinamik Beklenti Türetimi:** `test_canrat_ui_002_pytest.py` içindeki sabit `['Off', 'On', 'Off']` varsayımı kaldırılarak beklenti yalnız işlem öncesinde kaydedilmiş `observed['initial']` değerinden hesaplandı (`Off` ise `['Off', 'On', 'Off']`, `On` ise `['On', 'Off', 'On']`); geçersiz/bilinmeyen başlangıçta tahmin yapılmadan hata üretildi.
2. **Çift Yönlü Doğrulama:** `pytest_dogrula.py` ve `ortak.py` her iki geçerli geçişi destekleyecek şekilde güncellendi; köprü beklenen durumları ile UI beklenen durumlarının çapraz eşleşmesi zorunlu kılındı.
3. **Gerçek Windows Koşuları ve Kanıt Korunması:**
   - **Run 1 (Kapalı Başlangıç, Off):** `raporlar/kosular/pytest-gecis-843ce87a53ad4d419c0f541ab004b6cd/kapali` altında `Off → On → Off` döngüsü başarıyla tamamlandı, süreç `CloseMainWindow` ile normal kapatıldı, kanıtlar `DOGRULANDI (Kayıtlı: GECTI)` olarak doğrulandı.
   - **Run 2 (Önceden Açık, On):** Otomasyon hazırlık örneği (PID 1000) açılarak başlangıç `Off` değeri okundu ve kutu `On` durumuna getirildi. `raporlar/kosular/pytest-gecis-4b21c9e914484b42859d165961fb3353/acik` altındaki test koşusu PID 1000 sürecine bağlanarak `On → Off → On` döngüsünü ve `ACIK_BIRAKILDI` durumunu başarıyla tamamladı ve kanıtlar `DOGRULANDI (Kayıtlı: GECTI)` olarak doğrulandı. **Bağımsız Doğrulama Sınırı:** PID 1000 hazırlık örneğinin ilk `Off` durumu, `On`'a getirilmesi ve test sonrasındaki geri yükleme/kapanışına ait özgün yapısal kanıt dosyası oluşturulmamış, yalnızca komut stdout çıktısında yer almıştır; bu dış hazırlık ve geri yükleme/kapanış adımları diskteki kanıt dosyalarından bağımsız olarak doğrulanamamaktadır (geçmiş olaya sonradan yeni kanıt üretilmez).
4. **Tarihsel Kanıtlar:** `evaluate_run_evidence` ve `html_rapor.py` ile geçmiş koşu raporlarının değerlendirilmeye devam ettiği teyit edildi.

**Herkese açık GitHub kopyası ham `raporlar/kosular/` kayıtlarını içermez.** Bu kayıtlar yalnız yerel çalışma alanında korunur. Temiz bir klonda yapısal denetim için `--structure-only` kullanılır; `--tasks-only` yerel geçmiş kanıtların varlığını denetler. Teslim modeli, hedef uygulamanın harici temin edilmesi ve tarihsel kanıtların ilgili kaynak sürümleriyle değerlendirilmesi gerektiği [belgeler/teslim-bilesenleri.md](belgeler/teslim-bilesenleri.md) içinde açıklanmıştır.

## Sınırlar

Gerçek Windows'ta hem `Closed` (`Off → On → Off`) hem de `Existing` (`On → Off → On`) dalları doğrulanmıştır. Her iki koşuda da Start butonuna basılmaz, CAN bağlantısı başlatılmaz. Kullanıcıya ait açık CanRat süreci kapatılmaz; yalnız otomasyonun açtığı hazırlık süreci kapatılır. Kutu durumuna müdahale edildiğinde orijinal durum saklanır ve iş sonunda geri yüklenir. HTML raporu mevcut kanıtlardan üretilir, testi yeniden çalıştırmaz ve ağ bağlantısı gerektirmez. Yeni araç Windows oturumunu, `hedef_uygulama/CANRAT_3min/CANRat.exe` dosyasını, mevcut süreçleri ve masaüstü erişimini ayrıca doğrular.

**Otomatik LLM/ajan geçişi uygulanmadı.** Devir, bu dosyalar ve yeni oturumda yapılacak durum kontrolüyle yürür.
