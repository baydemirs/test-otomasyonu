# GOREV-002 Demo Denetimi

## Amaç

İlk testin ve talimatlarla yönlendirilen geliştirme düzeninin yanlış başarı üretmediğini göstermek.

## Girdiler

Çalıştırma öncesi belirlenen senaryolar: [GOREV-002 denetim planı](../gereksinimler/GOREV-002-denetim-plani.md). Gerçek ve sahte ortamlar [demo denetimi raporunda](../raporlar/demo-denetimi.md) ayrı gösterilir.

GOREV-001 kodu, gerçek çalıştırma komutu ve başlangıç test raporu.

## Yapılacak iş

[Doğrulama Kriterleri](../belgeler/dogrulama-kriterleri.md) belgesindeki doğru sonuç, kontrollü yanlış sonuç, uygulama başlatma hatası, tekrar çalıştırma, kesinti ve eksik talimat denemelerini uygula. Kontrollü yanlış veri veya sahte yanıt, normal testten açıkça ayrılmalıdır.

## Kabul kriterleri

- Her denemenin beklenen davranışı işe başlamadan bellidir.
- Yanlış sonuç veya çalıştırma hatası başarı sayılmaz.
- Kesinti sonrası kayıtla gerçek dosyalar arasındaki fark incelenir.
- Tekrar sınırı ve zaman aşımı davranışı gösterilir. Yalnızca metinde yazdığı için uygulanmış sayılmaz.
- Görev tamamlama kontrolü eksik veya eski kanıtı reddeder.
- Geliştirici raporu inceleyerek açık sorunları ve ana servise geçiş için kalan işleri kaydeder.

## Çıktı

raporlar/demo-denetimi.md belgesi ve ilgili koşuların ayrı kanıtları. Bu dosya görev sırasında oluşturulur. Hedef uygulamayı değiştirmek bu görevin varsayılan kapsamı değildir.

Güncel durum ve bağımlılıklar [Görev Durum Kaydı](../durum/gorev-durumu.yaml) içindedir.
