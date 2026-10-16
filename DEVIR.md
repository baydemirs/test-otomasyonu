# Oturum devri

Bu not 2026-10-15 devir anının kısa özetidir. **Güncel görev durumu ve bağımlılıklar için tek asıl kaynak [görev kaydıdır](durum/gorev-durumu.yaml).** Yeni ajan ilk olarak [AGENTS.md](AGENTS.md) kurallarını ve bu kaydı salt okunur inceler; burada yazanları güncel dosya ve kanıtların yerine koymaz.

## Çalışan kapsam

Son tamamlanan iş [GOREV-011](gorevler/GOREV-011-devir-hedefi-ve-test-ekleme-sureci.md) (projenin devir hedefinin, yeni test ekleme sürecinin, geliştirme ajanı ile test yürütmesi ayrımının ve ana servise ilişkin gelecek ihtiyaçlarının belgelenmesi); önceki aşama [GOREV-010](gorevler/GOREV-010-cift-yonlu-gecis-destegi.md) (CANRAT-UI-002 onay kutusu testinde `Off → On → Off` ve `On → Off → On` çift yönlü durum geçiş desteği, dinamik beklenti türetimi, çapraz katman tutarlılığı ve gerçek Windows masaüstü koşuları) belgesindedir. Tek aktif masaüstü senaryosu [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md): `MainWindow.centralwidget.cboxAppendRecieved` için başlangıç durumunu oku, karşıt durumu doğrula ve başlangıca dön. Aktif yol **pytest → PowerShell/.NET UIA**; pywinauto denemesi [arşivdedir](otomasyon/arsiv/pywinauto/README.md). Kullanım ve kurulum rehberi [README](README.md), teslim bileşenleri ve sınırları [Teslim Bileşenleri](belgeler/teslim-bilesenleri.md), teknoloji ve sahiplik kararları [Mimari Kararlar](belgeler/mimari-kararlar.md), çalışma prensipleri ve 6 adımlı test ekleme akışı [Çalışma Kuralları](belgeler/calisma-kurallari.md) içindedir.

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

GOREV-011 kapsamında netleştirilen devir ve mimari kuralları:
1. **Teslim Modeli ve Altyapı:** Emirhan altyapıyı kuracak ve ana servis uygulamasında 1–2 temsilî test geliştirecektir. Projeyi devralan sonraki kişi, ayrıntılı test prosedürünü geliştirme ajanına vererek yeni test ekletecek, çalıştıracak ve denetleyecektir. Yeni test eklemek altyapının yeniden yazılmasını gerektirmez. Beklenen davranış yetkili gereksinimden alınır; eksik kabul kriterleri ajan tarafından uydurulamaz.
2. **Yeni Test Ekleme Süreci (6 Adım):** Gereksinimi inceleme, kriterleri önceden kaydetme, mevcut adaptör altyapısını kullanma, senaryo geliştirme ve doğrulama (sentetik kontrollerin gerçek uygulama testinin geçtiğini kanıtlamadığı; gerçek koşu gerektiğinde bunun esas alınacağı, yapılamadıysa kapsam ve engelin kaydedileceği; yalnız belge değişikliklerinde masaüstü testi gerekmediği), test sonucu (`GECTI`, `KALDI`, `HATA`, `ATLANDI` — bkz. [Doğrulama Kriterleri](belgeler/dogrulama-kriterleri.md)) ile kanıt doğrulama durumunu (`DOGRULANDI`/`DOGRULANAMADI`) ayrı raporlama, görev kaydı ve DEVIR.md'yi aynı görev içinde güncelleme. Belge güncellemek geliştirme ajanının sorumluluğudur; kodun belgeleri kendiliğinden güncellediği iddia edilemez.
3. **Geliştirme Ajanı ile Test Yürütmesinin Ayrımı:** Ajan test kodunu geliştirir ve belgeleri günceller. Test çalıştırma sırasında yürütme sırası, süre sınırları ve assert kararları kayıtlı kod ve kurallarla belirlenir; LLM'in anlık tercihlerine bırakılmaz.
4. **Ana Servis Gelecek İhtiyaçları:** Test grupları/sıra/önkoşullar, ortam hazırlığı/bağımlılık/temizlik, süre sınırlı veri bekleme, hata/atlama/durdurma kuralları, test başına kanıt + toplu koşu özeti ve alternatif erişim yöntemleri ana servisin gelecek ihtiyaçları olarak kaydedilmiştir. Bunlar tamamlanmış özellik değildir; bu aşamada varsayımsal uygulama kodu geliştirilmemiştir.
5. **Kapsam, Kanıt ve Kurulum Sınırı:** CanRat üzerinde çift yönlü durum geçişleri (`Closed` dalında `Off → On → Off`, `Existing` dalında `On → Off → On`), süreç sahipliği ve HTML rapor üretimi doğrulanmıştır. [GOREV-010](gorevler/GOREV-010-cift-yonlu-gecis-destegi.md#doğrulama-durumu-ve-kanıt-sınırları) kapsamındaki asıl `Existing` test koşusunun (`raporlar/kosular/pytest-gecis-4b21c9e914484b42859d165961fb3353/acik`) PID 1000 üzerinde `On → Off → On` geçişi ve `ACIK_BIRAKILDI` durumu yapısal kanıtlarla doğrulanmıştır; buna karşılık PID 1000 hazırlık örneğinin dış hazırlık (ilk `Off` okuma, `On` durumuna getirme) ve test sonrası geri yükleme/kapatma adımlarına ait disk üzerinde bağımsız yapısal kanıt dosyası bulunmamaktadır (geçmiş olay için geriye dönük kanıt üretilmemiştir). Ana servis uygulaması henüz kurulmamıştır; gerçek gereksinimler görülmeden altyapı uygunluğu peşinen doğrulanamaz. Devralma kabulü (yeni kişi/ajanın belgelerle test ekleyebilmesi) nihai hedeftir; henüz gerçek bir devralma denemesiyle doğrulanmamıştır.

**Herkese açık GitHub kopyası ham `raporlar/kosular/` kayıtlarını içermez.** Bu kayıtlar yalnız yerel çalışma alanında korunur. Temiz bir klonda yapısal denetim için `--structure-only` kullanılır; `--tasks-only` yerel geçmiş kanıtların varlığını denetler. Teslim modeli, hedef uygulamanın harici temin edilmesi ve tarihsel kanıtların ilgili kaynak sürümleriyle değerlendirilmesi gerektiği [belgeler/teslim-bilesenleri.md](belgeler/teslim-bilesenleri.md) içinde açıklanmıştır.

## Sınırlar

Gerçek Windows'ta CanRat için hem `Closed` (`Off → On → Off`) hem de `Existing` (`On → Off → On`) dalları doğrulanmıştır. Her iki koşuda da Start butonuna basılmaz, CAN bağlantısı başlatılmaz. Kullanıcıya ait açık CanRat süreci kapatılmaz; yalnız otomasyonun açtığı hazırlık süreci kapatılır. Kutu durumuna müdahale edildiğinde orijinal durum saklanır ve iş sonunda geri yüklenir. HTML raporu mevcut kanıtlardan üretilir, testi yeniden çalıştırmaz ve ağ bağlantısı gerektirmez. Yeni araç Windows oturumunu, `hedef_uygulama/CANRAT_3min/CANRat.exe` dosyasını, mevcut süreçleri ve masaüstü erişimini ayrıca doğrular.

**Otomatik LLM/ajan geçişi uygulanmadı.** Devir, bu dosyalar ve yeni oturumda yapılacak durum kontrolüyle yürür.
