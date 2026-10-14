# GOREV-001 İlk Demo Testi

## Amaç

Uygulama incelemesinde seçilen tek işlevi otomatik çalıştırmak ve sonucu raporlamak.

## Girdiler

Bu görev için seçilen senaryo [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md). Kesin kriter kaynağı kullanıcının 2026-10-13 tarihli açık talimatıdır; önceki başlangıç ekranı adayı yerine bu kutu etkileşimi seçilmiştir. Araç: mevcut Python/Windows PowerShell ve .NET UIA; hedef bağlantı kodu ayrı katmandadır.

GOREV-000 inceleme kaydı, test verisi, gereksinimden gelen beklenen sonuç, başlangıç koşulu ve seçilen araç. Önceki görev tamamlanmadan bu bilgileri uydurarak kod yazılmaz.

## Yapılacak iş

1. Seçilen araçla en küçük çalışan uygulama bağlantısını kur.
2. Tek test senaryosunu yaz. Uygulamaya özgü işlemleri bağlantı katmanında tut.
3. Açık zaman aşımı ve test sonrası başlangıç durumuna dönüşü tanımla.
4. Sonuç doğrulamasını ve rapor üretimini ekle.
5. Gerçek kurulum ve test komutlarını README.md içine yaz.
6. Belge yolları, zorunlu görev alanları ve kanıt kayıtları için küçük bir kontrol komutu ekle. Ne kontrol ettiğini ve neyi garanti etmediğini açıkla.

## Kabul kriterleri

Bir gerçek test çalışır. Rapor beklenen ve gerçekleşen sonucu içerir. Testi tekrar çalıştırmak için Codex zorunlu değildir. Çalıştırılmayan veya başlatılamayan işlem başarılı sayılmaz. Kontroller gerçekten çalıştırılmıştır. Kod ve rapor aynı sürüm/çalıştırma bilgisine bağlanır.

## Çıktılar

Somut dosyalar: [Python yürütücü](../otomasyon/yurutme/canrat_ui_002.py), [UIA senaryosu](../otomasyon/yurutme/canrat_ui_002.ps1), [CanRat bağlantısı](../otomasyon/baglanti/canrat_toggle.ps1), [kanıt kontrolü](../otomasyon/dogrulama/demo_dogrula.py), [koşu raporu](../raporlar/canrat-ui-002.md). Gerçek komutlar README'dedir.

otomasyon/yurutme/ altındaki yürütme kodu, otomasyon/baglanti/ altındaki hedefe özgü kod, raporlar/ altındaki sonuçlar, gerçek kurulum ve çalıştırma adımları. Kesin dosya uzantıları ve komutlar araç seçiminden sonra belirlenecek.

Hedef uygulama kusuru tespit edilirse ayrıca raporla. Görevin tamamlanmasını [Doğrulama Kriterleri](../belgeler/dogrulama-kriterleri.md) üzerinden değerlendir. Güncel durum [Görev Durum Kaydı](../durum/gorev-durumu.yaml) dosyasındadır.
