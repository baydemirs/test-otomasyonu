# Oturum devri

Bu not 2026-10-14 devir anının kısa özetidir. **Güncel görev durumu ve bağımlılıklar için tek asıl kaynak [görev kaydıdır](durum/gorev-durumu.yaml).** Yeni ajan ilk olarak [AGENTS.md](AGENTS.md) kurallarını ve bu kaydı salt okunur inceler; burada yazanları güncel dosya ve kanıtların yerine koymaz.

## Çalışan kapsam

Son tamamlanan işin tanımı [GOREV-008](gorevler/GOREV-008-html-rapor.md) (bağımsız HTML raporu); önceki mimari sadeleştirme [GOREV-007](gorevler/GOREV-007-proje-sadelestirme.md) ve [raporundadır](raporlar/proje-sadelestirme.md). Tek aktif masaüstü senaryosu [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md): `MainWindow.centralwidget.cboxAppendRecieved` için başlangıç durumunu oku, karşıt durumu doğrula ve başlangıca dön. Aktif yol **pytest → PowerShell/.NET UIA**; pywinauto denemesi [arşivdedir](otomasyon/arsiv/pywinauto/README.md). Kullanım ve klasör haritası [README](README.md), teknoloji ve sahiplik kararları [Mimari Kararlar](belgeler/mimari-kararlar.md) içindedir.

Devir anında görev kaydında yarım iş görünmüyordu. Sıradaki somut adım, yeni ajanın kaynakları ve kanıtları **salt okunur** karşılaştırması, ardından kendisine verilen yeni görevin kabul kriterlerini belirlemesidir. Önceki ajanın yarım bıraktığı bir işlem saptanırsa gerçek dosya ve süreç durumu incelenmeden tekrarlanmaz. Aynı proje üzerinde iki geliştirme ajanı eşzamanlı çalışmaz.

## Doğrulanmış komutlar ve kanıtlar

Proje kökünden, mevcut `.venv` ile doğrulanmış komutlar (pytest yerel önbelleğe yazabilir; **ilk salt okunur incelemeden sonra** çalıştır):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --tasks-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali --expected Closed
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-34acf074e3ef475a9f877fb17f13991f/acik --expected Existing
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --existing raporlar/kosular/pytest-gecis-34acf074e3ef475a9f877fb17f13991f/acik --closed raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder raporlar/kosular/pytest-gecis-34acf074e3ef475a9f877fb17f13991f/acik
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali
```

GOREV-008 sonunda varsayılan pytest **58 geçti, 1 masaüstü testi atlandı**; görev kaydı, kapalı dal, açık dal bağlı kanıtları ve üretilen `rapor.html` dosyaları doğrulandı. `otomasyon/dogrulama/ortak.py` içinde tekil ortak kanıt değerlendirme fonksiyonu (`evaluate_run_evidence`) oluşturuldu; `html_rapor.py` bu değerlendirmenin sonucunu yalnız görselleştirir, `pytest_dogrula.py` ise ortak değerlendirmeyi kullanarak kendine özgü sürüm ve komut kontrollerini sürdürür. Link status=HATA/exit_code=1 iken GECTI iddiası, UI hata alanı doluyken GECTI iddiası, XML testcase içinde failure varken sayaçların sıfır olması, XML skipped iken UI/yaşam döngüsünün GECTI demesi, UI test_sonucu=HATA iken XML PASS iddiası, geçersiz başlangıç modu (expected_branch) veya kapanış başarısızlığı (KAPANMADI/exited=False) ve UI gozlem.error / cleanup_error hataları gibi tüm regresyonlar elendi. Kayıtlı sonuçların kaynak bazında (XML, Köprü, UI, Yaşam Döngüsü) dökümü raporda ayrı gösterilir. 21 HTML raporu birim testi ile tüm çelişki senaryoları ve tutarlı KALDI/HATA/ATLANDI doğrulamaları güvence altına alındı. Son kanıtların yerel yolları: `raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali/rapor.html`, `raporlar/kosular/pytest-gecis-34acf074e3ef475a9f877fb17f13991f/acik/rapor.html` ve bunlara bağlı `pytest-link.json`, `pytest.xml`, `sonuc.json` dosyalarıdır. Gerçek masaüstü komutu ve güvenli koşulları [README'dedir](README.md); onu ilk salt okunur kontrol sırasında çalıştırma.

**Herkese açık GitHub kopyası ham `raporlar/kosular/` kayıtlarını içermez.** Bu kayıtlar yalnız yerel çalışma alanında korunur. Görev kaydındaki kanıt yolları geçmiş gerçek koşulara işaret eder; yeni klonda bu dosyalar yoksa `--tasks-only` ve geçmiş kanıta bağlı birim kontrolleri geçmeyebilir. Eksik kanıtı başarı olarak yorumlama veya sahte dosya ile doldurma. Gerekli ham kanıtların aktarımı ayrı, açık bir karardır; [özet raporlar](raporlar/README.md) kaynak deposunda kalır.

## Sınırlar

GOREV-007 ve GOREV-008 sonrasında gerçek Windows'ta hem **kapalı başlangıç (Closed)** hem de **önceden açık uygulama (Existing)** dalları yeniden doğrulandı: Off → On → Off; kapalı dalda süreç normal kapandı, açık dalda süreç test süresince açık kaldı ve test bitiminde hazırlık örneği güvenle kapatıldı. HTML raporu mevcut doğrulanmış kanıtlardan üretilir, testi yeniden çalıştırmaz ve ağ bağlantısı gerektirmez. Tarihsel GOREV-002 kayıtları, taşınan güncel kodun doğrulaması değildir. Yeni araç Windows oturumunu, `hedef_uygulama/CANRAT_3min/CANRat.exe` dosyasını, mevcut süreçleri ve masaüstü erişimini ayrıca doğrular; önceki aracın onayları veya oturumu devredilmiş sayılmaz. Start'a basılmaz, CAN bağlantısı başlatılmaz, kullanıcının açık uygulaması kapatılmaz. Eski kanıtlar ve kabul kriterleri değiştirilmez.

**Otomatik LLM/ajan geçişi uygulanmadı.** Devir, bu dosyalar ve yeni oturumda yapılacak durum kontrolüyle yürür.
