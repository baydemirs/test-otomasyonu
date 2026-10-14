# GOREV-007 — Proje sadeleştirme

Kaynak: 2026-10-14 kullanıcı talimatı. Bağımlılık: GOREV-006. GOREV-004 teslim işi için ayrılmıştır.

## Kabul kriterleri

1. Aktif yürütücü pytest, tek uygulama adaptörü PowerShell/UIA olur; pywinauto karşılaştırma kodu, 0.6.9 sürümü ve sonuç raporu arşivde kalır. Varsayılan birim komutu UI'ye dokunmaz.
2. Uygulama bağlantısı, yaşam döngüsü, yürütme, inceleme ve kanıt doğrulama kodu `otomasyon/` altında; senaryolar ve otomasyon testleri `tests/` altında bulunur. Görev doğrulayıcılarının ortak dosya/özet işlemleri birleşir.
3. README, kurulum ve kanıt okuma yolunu yeni başlayan biri için açıklar. Güncel durum yalnız `durum/gorev-durumu.yaml` dosyasındadır.
4. `gereksinimler/CANRAT-UI-002.md` ve önceden oluşmuş koşu kanıtlarının içeriği ve yolları değişmez. Kurtarma süre sınırları, PID/başlangıç zamanı sahipliği ve normal kapanış koruması korunur.
5. Mevcut birim kontrolleri ve onaylı yöntemle gerçek Windows PowerShell/UIA pytest koşusu geçer; pytest XML, yaşam döngüsü ve UI JSON kanıtları aynı koşuya bağlanır. Windows engelinde görev tamamlanmaz.
6. Kullanıcıya ait uygulama kapanmaz; Start'a basılmaz ve CAN bağlantısı başlatılmaz. `.venv`, önbellekler ve hedef DLL dosyaları silinmez.

Test kimliği: CANRAT-UI-002. Beklenen durum: Off → On → Off. Kanıtlar yeni `raporlar/kosular/sadelestirme-*` koşusu ve onun işaret ettiği `pytest-gecis-*` koşusudur.
