# Otomatik Testler

`unit/` içindeki testler envanter, görev kaydı, UI sonuç sınıflandırması, kurtarma ve süreç sahipliği kanıtını kontrollü sahte verilerle doğrular. Gerçek CanRat testi değildir.

`../otomasyon/yurutme/canrat_ui_002.py` gerçek koşuyu yürütür; `../otomasyon/yurutme/canrat_ui_002.ps1` etkileşim ve finally/kurtarma düzenini içerir. Kabul kriterleri [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md), komutlar [proje rehberindedir](../README.md). Ön kontrol gerçek işlev testi sonucu üretmez. Birim testi sonucu ile gerçek Windows testi sonucu ayrı raporlanır.

`audit/denetim.py` GOREV-002 aşamalarını yürütür; `audit/sahte_canrat.ps1` gerçek uygulamaya erişmeyen ayrı denetim adaptörüdür. `audit/gercek_deneme.ps1` yalnızca salt okunur eksik kimlik sorgusu veya denetim üst sürecinin gözetimindeki kontrollü kutu/kesinti senaryosu içindir; `Interrupt` modu tek başına çalıştırılmamalıdır. Plan, güvenlik sınırları ve gerçek kanıtlar [demo denetimi raporundadır](../raporlar/demo-denetimi.md).

`desktop/test_canrat_ui_002_pytest.py` GOREV-005'in tek pytest masaüstü testidir. Varsayılan `pytest -q` sırasında atlanır; yalnız `--run-desktop`, başlangıç durumu ve yeni kanıt klasörüyle çalışır. Mevcut yaşam döngüsü ve UIA kodunu alt süreç olarak kullanır. Komutlar ve gerçek kanıtlar [pytest geçiş raporundadır](../raporlar/pytest-gecis-denemesi.md).

GOREV-006 pywinauto denemesi [arşivdedir](../otomasyon/arsiv/pywinauto/README.md). Bu testin aktif adaptörü yalnız PowerShell/UIA'dır. Geçmiş karşılaştırma ve sahte kontroller [raporda](../raporlar/pywinauto-karsilastirma.md) ayrılır.
