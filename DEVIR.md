# Oturum devri

Bu not 2026-10-14 devir anının kısa özetidir. **Güncel görev durumu ve bağımlılıklar için tek asıl kaynak [görev kaydıdır](durum/gorev-durumu.yaml).** Yeni ajan ilk olarak [AGENTS.md](AGENTS.md) kurallarını ve bu kaydı salt okunur inceler; burada yazanları güncel dosya ve kanıtların yerine koymaz.

## Çalışan kapsam

Son tamamlanan iş [GOREV-009](gorevler/GOREV-009-kanit-guvenligi-ve-rapor-korumasi.md) (ortak kanıt değerlendirmesinde güvenlik ve tutarlılık açıklarının kapatılması, süreç sahipliği ve jurnal denetimleri, otomasyon hatası ile başarısızlık ayrımı ve HTML rapor çıktısının ham kanıtları koruması); önceki aşamalar [GOREV-004](gorevler/GOREV-004-teslim-hazirligi.md) (teslim hazırlığı ve temiz klon doğrulaması), [GOREV-008](gorevler/GOREV-008-html-rapor.md) (HTML raporu ve ortak değerlendirici) ve [GOREV-007](gorevler/GOREV-007-proje-sadelestirme.md) (mimari sadeleştirme) belgelerindedir. Tek aktif masaüstü senaryosu [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md): `MainWindow.centralwidget.cboxAppendRecieved` için başlangıç durumunu oku, karşıt durumu doğrula ve başlangıca dön. Aktif yol **pytest → PowerShell/.NET UIA**; pywinauto denemesi [arşivdedir](otomasyon/arsiv/pywinauto/README.md). Kullanım ve kurulum rehberi [README](README.md), teslim bileşenleri ve sınırları [Teslim Bileşenleri](belgeler/teslim-bilesenleri.md), teknoloji ve sahiplik kararları [Mimari Kararlar](belgeler/mimari-kararlar.md) içindedir.

Devir anında görev kaydında yarım iş görünmüyordu. Sıradaki somut adım, yeni ajanın kaynakları ve kanıtları **salt okunur** karşılaştırması, ardından kendisine verilen yeni görevin kabul kriterlerini belirlemesidir. Önceki ajanın yarım bıraktığı bir işlem saptanırsa gerçek dosya ve süreç durumu incelenmeden tekrarlanmaz. Aynı proje üzerinde iki geliştirme ajanı eşzamanlı çalışmaz.

## Doğrulanmış komutlar ve kanıtlar

Proje kökünden, mevcut `.venv` ile doğrulanmış komutlar (pytest yerel önbelleğe yazabilir; **ilk salt okunur incelemeden sonra** çalıştır):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --structure-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --tasks-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali --expected Closed
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali
```

GOREV-009 tamamlanma incelemesi sonunda varsayılan pytest **100 geçti, 1 masaüstü testi atlandı** (9 yeni birim testi eklendi; `test_html_rapor.py` 54 teste ulaştı):
1. **Zorunlu Alanlar ve Karşılaştırma Önceliği:** Köprü `test_id`, UI `test_id` ve beklenen senaryo (`CANRAT-UI-002`) eksiksiz eşleşti; UI `calistirma_id`, yaşam döngüsü `run_id` ve alt test `report_path` eksik/boş olduğunda reddedildi; kimliklerin kendi klasörleriyle, `report_path`'in köprünün UI raporuyla eşleşmesi sağlandı; yaşam döngüsünün üst `expected` değeri, `observed.expected` ve köprü `expected_branch` birlikte karşılaştırılarak üst değerin alt kontrolü atlatması engellendi; `expected_states`'in başlangıç → karşıtı → başlangıç kuralına ve gerçekleşen değerlere sıkı uyumu denetlendi, başarı elde etmek için beklenti değiştirme girişimleri engellendi.
2. **Uygulama Başlamadan Oluşan Gerçek HATA:** `canrat_yasam.ps1` şemasına uygun olarak `identity=null`, `owned=False`, `test=CALISTIRILMADI` ve `close=DENENMEDI` gibi erken hata kayıtları işlendi; süreç başlamadıysa olmayan süreç kimliği veya başarılı kapanış şart koşulmadı, hata açıklaması ve ulaşılan aşamayla tutarlı kayıtlar dürüstçe `HATA (DOĞRULANDI)` olarak doğrulandı; gerçekte başlamış süreç için aynı eksikliklerin gizlenmesine izin verilmedi. Rapor üretimi ham kanıt hash'lerini değiştirmez.

Aynı bilgisayarda geçici temiz bir kaynak kopyasında (mevcut `.venv` ve geçmiş `raporlar/kosular` kayıtları olmadan) yeni sanal ortam kurulup hedef uygulama sağlanarak README akışı Closed modunda uçtan uca çalıştırıldı ve doğrulandı. Önceki geçici çalıştırmadaki ham kanıtların silindiği [raporlar/temiz-klon-dogrulama.json](raporlar/temiz-klon-dogrulama.json) içine açıkça kaydedildi; bu eksikliği gidermek üzere taze olarak yeniden yürütülen temiz koşunun ham kanıtları (`raporlar/kosular/pytest-gecis-6b26d20f2a37499d988fc9fa6f329b57/kapali` ve bağlı yaşam döngüsü/UI dosyaları) silinmeden yerel alanda korundu. Doğrulama çıktılarının kaynak sürümü `b283d7f569829d357296b891ef1d94687f0dd79a` (yerel GOREV-004 düzeltmeleriyle birlikte) olarak kayıt altına alındı.

**Önemli Not:** Bu işlem yalnızca yeni bir masaüstü koşusunun geçmiş geliştirme kanıtlarından bağımsız çalışmasını çözmüştür. Olası diğer genel inceleme bulguları bu işlemle çözülmüş sayılmaz; her yeni ihtiyaç kendi görev ve kabul kriteriyle ele alınmalıdır.

**Herkese açık GitHub kopyası ham `raporlar/kosular/` kayıtlarını içermez.** Bu kayıtlar yalnız yerel çalışma alanında korunur. Temiz bir klonda yapısal denetim için `--structure-only` kullanılır; `--tasks-only` yerel geçmiş kanıtların varlığını denetler. Teslim modeli, hedef uygulamanın harici temin edilmesi ve tarihsel kanıtların ilgili kaynak sürümleriyle değerlendirilmesi gerektiği [belgeler/teslim-bilesenleri.md](belgeler/teslim-bilesenleri.md) içinde açıklanmıştır.

## Sınırlar

GOREV-007 ve GOREV-008 sonrasında gerçek Windows'ta hem **kapalı başlangıç (Closed)** hem de **önceden açık uygulama (Existing)** dalları yeniden doğrulandı: Off → On → Off; kapalı dalda süreç normal kapandı, açık dalda süreç test süresince açık kaldı ve test bitiminde hazırlık örneği güvenle kapatıldı. HTML raporu mevcut doğrulanmış kanıtlardan üretilir, testi yeniden çalıştırmaz ve ağ bağlantısı gerektirmez. Tarihsel GOREV-002 kayıtları, taşınan güncel kodun doğrulaması değildir. Yeni araç Windows oturumunu, `hedef_uygulama/CANRAT_3min/CANRat.exe` dosyasını, mevcut süreçleri ve masaüstü erişimini ayrıca doğrular; önceki aracın onayları veya oturumu devredilmiş sayılmaz. Start'a basılmaz, CAN bağlantısı başlatılmaz, kullanıcının açık uygulaması kapatılmaz. Eski kanıtlar ve kabul kriterleri değiştirilmez.

**Otomatik LLM/ajan geçişi uygulanmadı.** Devir, bu dosyalar ve yeni oturumda yapılacak durum kontrolüyle yürür.
