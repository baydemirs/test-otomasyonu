# Çalışma Kuralları

## Sonuçların doğruluğu

- Beklenen sonucu uygulama gereksiniminden veya mentörün sağladığı örnekten al. Gerçekleşen sonuçtan beklenen sonucu türetme.
- Çalıştırılmayan testi geçti diye kaydetme. Atlanan veya başlatılamayan test başarılı sayılmaz.
- Hedef uygulama hatasını, otomasyon hatasını ve ortam sorununu ayrı açıkla. Hata kaynağı henüz bilinmiyorsa bilinmiyor olarak belirt.
- Kabul kriterlerini sadece testi geçirmek için gevşetme.

## Değişiklik düzeni

- Göreve ilişkin dosyaları değiştir. Hedef uygulamanın kodunda değişiklik ayrıca görevin kapsamına dahil edilmiş olmalıdır.
- Aynı kuralı birkaç belgede kopyalama. Ayrıntının asıl belgesine bağlantı ver.
- Dosya adları anlamlı, ASCII karakterli ve boşluksuz olsun. Belge başlıklarında doğru Türkçe kullan.
- README.md ve AGENTS.md yerleşik adlarını koru. Kod ve kütüphane adlarını seçilen dilin kurallarına uygun tut.
- Kullanıcının mevcut çalışmasının üzerine yazmadan önce dosyayı incele ve değişiklikleri koru.

## Çalıştırma ve kayıt

- Her test çalıştırmasına ayrı kimlik ver. Eski raporların üzerine sessizce yazma.
- Başlangıç koşulunu ve test sonrası temizliği tanımla. Süre aşımını sınırsız bırakma.
- Kod, talimat ve rapor arasındaki sürüm ilişkisini kaydet. Git kullanılacaksa depo kurulumunu ayrı bir başlangıç adımı olarak yap.
- Geliştirme sırrını, gerçek parolayı veya kişisel bilgiyi örnek veri ve rapora koyma.

## Yeni test ekleme süreci

Yeni bir test prosedürü geldiğinde geliştirme ajanı altyapıyı baştan yazmadan şu 6 adımlı akışı sırasıyla izler:

1. **Gereksinimi İnceleme:** İlgili yetkili gereksinim ve prosedür belgesini oku; belirsiz veya çelişkili noktaları kullanıcıya sorarak netleştir. Eksik kabul kriteri uydurma.
2. **Kriterleri Önceden Kaydetme:** Ölçülebilir kabul kriterlerini ve beklenen davranışı kod yazımından önce görev dosyasına kaydet.
3. **Mevcut Altyapıyı Kullanma:** Uygulama adaptöründeki (`otomasyon/baglanti/`) mevcut işlemleri kullan. Yeni bir arayüz veya donanım erişim işlemi gerekiyorsa bunu senaryonun içine gömmek yerine uygun adaptör katmanına ekle.
4. **Senaryo Geliştirme ve Doğrulama:** Test senaryosunu yaz ve kapsamına uygun kontrollerle doğrula. Sahte (sentetik) verilerle yapılan birim kontrolleri doğrulama mantığını sınar ancak gerçek uygulama testinin geçtiğini kanıtlamaz. Görev kapsamı gerçek uygulama koşusu gerektiriyorsa tamamlanma değerlendirmesinde gerçek koşuyu esas al; gerçek koşu yapılamadıysa doğrulanamayan kapsamı ve engeli kaydet (yalnız belge değişikliklerinde masaüstü testi çalıştırılması gerekmez).
5. **Sonuç ve Kanıtı Ayrı Raporlama:** Hedef uygulamanın test sonucunu (`GECTI`, `KALDI`, `HATA`, `ATLANDI` — tanımlar için bkz. [Doğrulama Kriterleri](dogrulama-kriterleri.md)) ile otomasyonun kanıt doğrulama durumunu (`DOGRULANDI`/`DOGRULANAMADI`) birbirine karıştırmadan ayrı ayrı raporla.
6. **Belge ve Durum Kaydı:** Görev kaydını (`durum/gorev-durumu.yaml`) ve devir notunu (`DEVIR.md`), işin gerçek sonucu ve kalan sınırlarıyla aynı görev oturumu içinde güncelle.

> [!IMPORTANT]
> Proje belgelerinin, devir notlarının ve görev durumlarının güncellenmesi geliştirme ajanının açık sorumluluğudur. Kodun belgeleri kendiliğinden güncellediği iddia edilemez; her somut değişiklik ve sınır ajan tarafından ilgili belgelere dürüstçe işlenir.

## Geliştirme ajanı ile test yürütmesinin ayrımı

- **Ajanın Sorumluluğu:** Geliştirme ajanı test kodunu yazar, uyarlar ve belgelerin bakımını yapar.
- **Yürütmenin Nesnelliği:** Test çalıştırma sırasında yürütme sırası, süre sınırları ve başarı/başarısızlık kararları kayıtlı kod ve kurallarla belirlenir. Bu kararlar ve çalışma mantığı LLM’in anlık tercihlerine bırakılmaz.

Bu kuralların metinde bulunması teknik zorunluluk oluşturmaz. Otomatik uygulanabilen kontroller küçük kontrol komutlarıyla (`demo_dogrula.py`, `pytest_dogrula.py`) denetlenir.
