# Proje Kapsamı

## Amaç

Açık talimatlarla geliştirilen ve farklı bir geliştirme ajanı veya geliştirici tarafından devralınabilen tek bir test otomasyonu projesi oluşturmak. İlk uygulama CanRat, sonraki hedef ana servis yazılımıdır.

## Bilinenler

- İlk geliştirme oturumları VS Code içindeki Codex ile yürütüldü; yeni araç kendi erişimini ve onaylarını ayrıca doğrular.
- CanRat Windows masaüstü uygulamasıdır; pakette Qt 6 bileşenleri vardır.
- Sağlanan CANRAT_3min.zip, çalıştırılabilir dosya ve derleme çıktıları içerir. Tam kaynak proje yoktur.
- İlk demo PCAN gerektirmeyecek. Bu, CAN iletişiminin doğrulandığı anlamına gelmez.
- Servis test prosedürü ileri aşamanın referansıdır; CanRat gereksinimi değildir.

## Doğrulanan kapsam

İlk Windows envanteri ve tek kutu testinin kesin kabul kriterleri kaydedildi. Beklenen sonuç [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md) dosyasındadır; geçmiş envanter ve test kanıtları [raporlardadır](../raporlar/). Başka uygulamalar veya CAN haberleşmesi bu kanıtlardan doğrulanmış sayılmaz.

## İlk demo

Uygulama erişimi doğrulandıktan sonra tek bir gerçek işlev testi, sonuç/kanıt kaydı, kontrollü yanlış sonucu yakalama, çalıştırma hatası ve kesintiden sonra devam denetimi. Ön inceleme aracı yalnızca erişim kanıtı toplar; işlev testi yerine geçmez.

## Sonraki kapsam

Ana servis senaryoları, gerçek donanım ortamı ve insana bağlı adımlar ayrı görevlerle eklenecek. RAG ve ek ajanlar, ölçülen bir ihtiyaç veya açık teslim gereksinimiyle eklenecek. Uygulama paketini veya ana servis yazılımını değiştirmek mevcut kapsamda değildir.
