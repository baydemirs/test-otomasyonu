# GOREV-011 — Devir Hedefi ve Yeni Test Ekleme Süreci

## Kapsam ve bağımlılık

Kaynak: Kullanıcının 2026-10-15 talimatı. Bağımlılık: GOREV-010.
Bu görev yalnız dokümantasyon kapsamındadır. Kod, bağımlılık, test kabul kriteri veya ham kanıt değiştirilmez; masaüstü testi çalıştırılmaz; push yapılmaz.
Projenin devir hedefini, yeni test ekleme sürecini, geliştirme ajanı ile test yürütmesi ayrımını ve ana servise ilişkin gelecek ihtiyaçlarını mevcut belgelere işlemek.

## Kabul kriterleri

1. **Teslim Hedefinin Belgelenmesi:**
   - Proje belgelerinde teslim hedefi netleştirilmelidir: Emirhan altyapıyı kuracak ve ana servis uygulamasında 1–2 temsilî test geliştirecektir. Sonraki kişi, ayrıntılı test prosedürünü geliştirme ajanına vererek yeni test ekletecek, çalıştıracak ve sonuçlarını denetleyecektir.
   - Yeni test eklemenin her defasında altyapının yeniden yazılmasını gerektirmeyeceği; beklenen davranışın yetkili gereksinimden alınacağı ve ajanın eksik kabul kriteri uyduramayacağı kuralı belgelenmelidir.
   - Devralma kabulü kaydedilmelidir: Yeni kişi/ajan, proje belgeleri ve prosedürle bir test ekleyebilmelidir. Bu kabulün henüz gerçek bir devralma denemesiyle doğrulandığı iddia edilmemeli, henüz doğrulanmadığı açıkça belirtilmelidir.

2. **Yeni Test Ekleme Sürecinin Tanımlanması:**
   - İlgili belgede 6 adımlı akış tanımlanmalıdır:
     1. İlgili gereksinim ve prosedürü oku; belirsiz noktaları netleştir.
     2. Kabul kriterlerini uygulamadan önce kaydet.
     3. Uygulama adaptöründeki mevcut işlemleri kullan; yeni erişim işlemi gerekiyorsa uygun katmana ekle.
     4. Senaryoyu yaz ve kapsamına uygun kontrollerle doğrula. Sahte/sentetik verilerle yapılan kontrollerin gerçek uygulama testinin geçtiğini kanıtlamadığı; gerçek koşu gereken işlerde tamamlanma değerlendirmesinde gerçek koşunun esas alınacağı, yapılamadıysa doğrulanamayan kapsamın ve engelin kaydedileceği açıkça belirtilmelidir (yalnız belge değişikliklerinde masaüstü testi çalıştırılması gerektiği anlamı oluşturulmamalıdır).
     5. Test sonucu (`GECTI`, `KALDI`, `HATA`, `ATLANDI` sınıflarının tamamını kapsayacak şekilde [Doğrulama Kriterleri](../belgeler/dogrulama-kriterleri.md) belgesine bağlantı vererek) ile kanıt doğrulama durumunu (`DOGRULANDI`/`DOGRULANAMADI`) ayrı raporla.
     6. Görev kaydı ve DEVIR.md’yi, işin gerçek sonucu ve kalan sınırlarıyla aynı görev içinde güncelle.
   - Belge güncellemenin bugün geliştirme ajanının açık sorumluluğu olduğu, kodun tüm belgeleri kendiliğinden güncellediği iddiasında bulunulmaması gerektiği açıkça belirtilmelidir.

3. **Geliştirme Ajanı ile Test Yürütmesinin Ayrılması:**
   - Ajanın test kodunu geliştirdiği ve bakımını yaptığı; test çalıştırma sırasında ise sıra ve kararların kayıtlı kod ve kurallarla belirlendiği, LLM’in anlık tercihlerine bırakılmadığı mimari ve çalışma kurallarında netleştirilmelidir.

4. **Gelecek İhtiyaçlarının Ayrıştırılması:**
   - Ana servis gereksinimleri geldiğinde değerlendirilecek ihtiyaçlar (test grupları/sıra/önkoşullar, ortam hazırlığı/bağımlılık/temizlik, süre sınırlı veri bekleme, hata/atlama/durdurma kuralları, test başına kanıt ve toplu koşu özeti, alternatif erişim yöntemleri) açıkça gelecek ihtiyacı olarak kaydedilmeli; tamamlanmış özellik gibi sunulmamalı ve bu görevde uygulama kodu geliştirilmemelidir.

5. **Mevcut Kapsam, Kanıt Sınırı ve Kurulum Sınırı:**
   - Mevcut çalışan CanRat kapsamı gelecek hedeflerinden açıkça ayrılmalıdır.
   - Ana servis uygulamasının henüz kurulmadığı ve gerçek gereksinimler görülmeden uygunluğunun doğrulanamayacağı belirtilmelidir.
   - `DEVIR.md` içinde, [GOREV-010](GOREV-010-cift-yonlu-gecis-destegi.md) kapsamındaki asıl `Existing` testinin (`On → Off → On` ve `ACIK_BIRAKILDI`) doğrulanan kanıtları ile PID 1000 dış hazırlık ve son temizlik/kapanış adımlarının bağımsız yapısal kanıtının bulunmadığı sınırı birbirinden ayrı anlatılmalı ve ilgili bölüme bağlantı verilmelidir.
   - Belge bağlantıları ve görev yapısı doğrulanmalıdır.
