# Proje Kapsamı

## Amaç ve Teslim Hedefi

Açık talimatlarla geliştirilen ve farklı bir geliştirme ajanı veya geliştirici tarafından devralınabilen bir test otomasyonu altyapısı kurmak.

- **Teslim Modeli:** Emirhan otomasyon altyapısını kuracak ve ana servis uygulamasında 1–2 temsilî test geliştirecektir. Projeyi devralan sonraki kişi, ayrıntılı test prosedürünü geliştirme ajanına vererek yeni test ekletecek, testleri çalıştıracak ve sonuçlarını denetleyecektir.
- **Yeniden Yazmama İlkesi:** Yeni bir test eklemek, her defasında altyapının yeniden yazılmasını gerektirmemelidir. Altyapı; uygulama adaptörü, yaşam döngüsü, test yürütücüsü ve doğrulama katmanlarını modüler sunar.
- **Yetkili Gereksinim Kuralı:** Test edilen beklenen davranış yetkili gereksinim ve prosedür belgelerinden alınmalıdır; eksik kabul kriterleri geliştirme ajanı tarafından uydurulamaz.

## Mevcut Doğrulanan Kapsam (CanRat)

Küçük demo uygulaması olan CanRat üzerinde tek bir arayüz kontrolünün (`MainWindow.centralwidget.cboxAppendRecieved`) çift yönlü durum geçişleri (`Off → On → Off` ve `On → Off → On`), süreç sahipliği ve bağımsız HTML rapor üretimi doğrulanmıştır. Beklenen sonuç [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md) dosyasındadır; geçmiş envanter ve test kanıtları [raporlardadır](../raporlar/).

Bu kanıtlar yalnızca hedeflenen tek kutu için geçerlidir; CAN iletişimi, Start işlemi veya başka pencereler doğrulanmış sayılmaz.

## Ana Servis Durumu ve Gelecek Kapsam

- **Uygulama Durumu:** Ana servis uygulaması henüz kurulmamıştır. Gerçek gereksinimler ve çalışma ortamı görülmeden altyapının ana servise uygunluğu peşinen doğrulanamaz.
- **Gelecek İhtiyaçlar:** Ana servis senaryoları, gerçek donanım ortamı, test paketleri/sıralaması, ortam hazırlığı ve insana bağlı adımlar gerçek gereksinimler sağlandığında ayrı görevlerle eklenecektir. RAG ve ek denetim ajanları, ölçülen bir ihtiyaçla değerlendirilecektir.

## Devralma Kabul Ölçütü

Projenin devir başarısı şu ölçüte dayanır: Yeni bir kişi ve geliştirme ajanı, proje belgelerini ve test prosedürünü kullanarak altyapıyı baştan yazmadan yeni bir test ekleyebilmeli, çalıştırabilmeli ve kanıtlarını denetleyebilmelidir.

> [!IMPORTANT]
> Bu devralma kabulü projenin nihai teslim hedefidir; henüz farklı bir kişi/ajan ile gerçek bir devralma denemesi yapılarak doğrulanmamıştır.
