# Doğrulama Kriterleri

## Önce iki farklı sonucu ayır

Test sonucu, hedef uygulamanın bir beklentiyi karşılayıp karşılamadığını söyler. Görev durumu, otomasyonu geliştirme işinin kabul koşullarını karşılayıp karşılamadığını söyler. Kontrollü yanlış sonucu yakalayan testin kaldı sonucu üretmesi, demo denetimi için beklenen davranıştır.

## Test sonucu sınıfları

| Sonuç | Anlamı |
| --- | --- |
| GECTI | İşlem çalıştı, gerçekleşen sonuç beklenen sonuçla uyumlu |
| KALDI | İşlem çalıştı, gerçekleşen sonuç beklentiyi karşılamadı |
| HATA | Test güvenilir sonuç üretemedi, örneğin uygulama başlamadı |
| ATLANDI | Test yürütülmedi, nedeni kaydedildi |

KALDI sonucundan tek başına hata kaynağı çıkarılmaz. Ürün, otomasyon veya ortam kaynaklı olduğunu belirlemek için kanıt incelenir.

## Demo denemeleri

1. Bilinen doğru sonuçta GECTI üret.
2. Kontrollü yanlış sonuçta KALDI üret. Testi yeşile çevirmek için beklenen değeri değiştirme.
3. Uygulama başlatılamadığında HATA ve açık neden üret. Tanımlı zaman aşımında sonlan.
4. Aynı başlangıç koşuluyla testi yeniden çalıştır ve sonuçları karşılaştır.
5. Geliştirme oturumu kesilip açıldığında dosya ve kanıtları kontrol ederek uygun göreve dön.
6. Eksik görev girdisini veya bozuk belge yolunu gizlemeden raporla.

## Asgari kanıt

Her çalıştırmada görev kimliği, test kimliği, çalıştırma kimliği, tarih, uygulama sürümü, otomasyon sürümü veya dosya özeti, gerçek komut, test verisi, beklenen ve gerçekleşen sonuç, sonuç sınıfı ve kanıt yolu tutulur. Anlamlıysa ekran görüntüsü eklenir. Sadece bir dosyanın varlığı doğru sonucun kanıtı değildir.

## Görev tamamlanma kontrolü

GOREV-000 için test çalıştırma şartı yoktur; kabul kanıtı uygulama incelemesidir. GOREV-001 için gerçek test komutu ve raporu gerekir. GOREV-002 için doğru ve olumsuz örneklerin beklenen sınıfları üretmesi gerekir. `otomasyon/dogrulama/` altındaki görev doğrulayıcıları komut başarısını, gerekli sonuç alanlarını ve sürüm/çalıştırma ilişkisini denetler; sonuçlar ayrıca geliştirici tarafından incelenir.

Bu belge genel kabul planıdır. İlk gerçek etkileşim demosunun kesin kriterleri [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md), koşu kanıtları [demo raporundadır](../raporlar/canrat-ui-002.md). Bir gerçek başarılı koşu, demo denetimindeki bütün olumsuz senaryoların çalıştırıldığı anlamına gelmez.
