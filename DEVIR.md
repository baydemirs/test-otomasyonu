# Oturum devri

Bu not 2026-10-14 devir anının kısa özetidir. **Güncel görev durumu ve bağımlılıklar için tek asıl kaynak [görev kaydıdır](durum/gorev-durumu.yaml).** Yeni ajan ilk olarak [AGENTS.md](AGENTS.md) kurallarını ve bu kaydı salt okunur inceler; burada yazanları güncel dosya ve kanıtların yerine koymaz.

## Çalışan kapsam

Son tamamlanan işin tanımı [GOREV-007](gorevler/GOREV-007-proje-sadelestirme.md), doğrulaması [sadeleştirme raporundadır](raporlar/proje-sadelestirme.md). Tek aktif masaüstü senaryosu [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md): `MainWindow.centralwidget.cboxAppendRecieved` için başlangıç durumunu oku, karşıt durumu doğrula ve başlangıca dön. Aktif yol **pytest → PowerShell/.NET UIA**; pywinauto denemesi [arşivdedir](otomasyon/arsiv/pywinauto/README.md). Kullanım ve klasör haritası [README](README.md), teknoloji ve sahiplik kararları [Mimari Kararlar](belgeler/mimari-kararlar.md) içindedir.

Devir anında görev kaydında yarım iş görünmüyordu. Sıradaki somut adım, yeni ajanın kaynakları ve kanıtları **salt okunur** karşılaştırması, ardından kendisine verilen yeni görevin kabul kriterlerini belirlemesidir. Önceki ajanın yarım bıraktığı bir işlem saptanırsa gerçek dosya ve süreç durumu incelenmeden tekrarlanmaz. Aynı proje üzerinde iki geliştirme ajanı eşzamanlı çalışmaz.

## Doğrulanmış komutlar ve kanıtlar

Proje kökünden, mevcut `.venv` ile doğrulanmış komutlar (pytest yerel önbelleğe yazabilir; **ilk salt okunur incelemeden sonra** çalıştır):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --tasks-only
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali --expected Closed
```

GOREV-007 sonunda varsayılan pytest **37 geçti, 1 masaüstü testi atlandı**; görev kaydı ve son kapalı dalın bağlı kanıtı doğrulandı. Son kanıtların yerel yolları: `raporlar/kosular/sadelestirme-65d5cf1cae154433b7bdff0895c94318/dogrulama.json`, `raporlar/kosular/pytest-gecis-9bbd1a1f468f4cd3a5372a4b430a95b4/kapali/pytest-link.json` ve aynı klasördeki `pytest.xml`. Gerçek masaüstü komutu ve güvenli koşulları [README'dedir](README.md); onu ilk salt okunur kontrol sırasında çalıştırma.

**Herkese açık GitHub kopyası ham `raporlar/kosular/` kayıtlarını içermez.** Bu kayıtlar yalnız yerel çalışma alanında korunur. Görev kaydındaki kanıt yolları geçmiş gerçek koşulara işaret eder; yeni klonda bu dosyalar yoksa `--tasks-only` ve geçmiş kanıta bağlı birim kontrolleri geçmeyebilir. Eksik kanıtı başarı olarak yorumlama veya sahte dosya ile doldurma. Gerekli ham kanıtların aktarımı ayrı, açık bir karardır; [özet raporlar](raporlar/README.md) kaynak deposunda kalır.

## Sınırlar

GOREV-007 sonrasında gerçek Windows'ta **kapalı başlangıç** yeniden doğrulandı: Off → On → Off, yalnız o koşunun başlattığı süreç normal kapandı. **Önceden açık uygulama dalı bu değişiklikten sonra yeniden çalıştırılmadı.** Tarihsel GOREV-002 kayıtları, taşınan güncel kodun doğrulaması değildir. Yeni araç Windows oturumunu, `hedef_uygulama/CANRAT_3min/CANRat.exe` dosyasını, mevcut süreçleri ve masaüstü erişimini ayrıca doğrular; önceki aracın onayları veya oturumu devredilmiş sayılmaz. Start'a basılmaz, CAN bağlantısı başlatılmaz, kullanıcının açık uygulaması kapatılmaz. Eski kanıtlar ve kabul kriterleri değiştirilmez.

**Otomatik LLM/ajan geçişi uygulanmadı.** Devir, bu dosyalar ve yeni oturumda yapılacak durum kontrolüyle yürür.
