# GOREV-002 denetim senaryoları

Bu dizindeki senaryolar uygulama açık değil, kontrol eksik, değişim gerçekleşmiyor, süre aşımı ve geri yükleme hatası durumlarını gerçek ve sahte kaynaklarla ayrı değerlendirir. [Denetim planı](../../gereksinimler/GOREV-002-denetim-plani.md) ve [tarihsel sonuç](../../raporlar/demo-denetimi.md) karşılaştırma için saklanır.

`denetim.py` içindeki tarihsel kanıt kopyalama senaryoları eski CANRAT-UI-002 kaynak yollarını ve o günkü SHA özetlerini temel alır. Kaynaklar `otomasyon/` altına taşındığından eski koşu, güncel kodun tamamlanma kanıtı olamaz. Bu senaryoları yeni koşuda yeniden geçerli saymak için önce fixture kaynağını yeni sürümle üretmek gerekir; eski raporlara dokunulmaz. Varsayılan `pytest -q` bu denetim sürücüsünü çalıştırmaz.
