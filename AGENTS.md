# Geliştirme Ajanı Çalışma Rehberi

Bu proje küçük bir uygulama üzerinden test otomasyonu geliştirmek içindir. Bu kurallar projeyi devralan her geliştirme ajanı için geçerlidir; kullanılan aracın üst düzey talimatları ve erişim sınırları içinde uygulanır. Bu dosya süreç tanımıdır; kendi başına program çalıştırmaz, erişim izni vermez veya yeni ajan başlatmaz.

## Okuma sırası

1. Yeni oturumun ilk işlemi salt okunur durum kontrolü olsun: bu kuralları, [Görev Durum Kaydı](durum/gorev-durumu.yaml) dosyasını ve [Devir Notu](DEVIR.md) belgesini oku; ilgili görev dosyası ile kabul kriterlerini incele. Bu aşamada masaüstü testi veya uygulama işlemi başlatma.
2. [Proje Kapsamı](belgeler/proje-kapsami.md), [Çalışma Kuralları](belgeler/calisma-kurallari.md), [Yol Haritası](belgeler/yol-haritasi.md) ve [Doğrulama Kriterleri](belgeler/dogrulama-kriterleri.md) belgelerini incele.
3. Teknoloji veya bileşen sınırını değiştireceksen [Mimari Kararlar](belgeler/mimari-kararlar.md) belgesini de oku.
4. Yeni bir kişiye açıklama yaparken [Proje Rehberi](README.md) ve gerekirse [Terimler Sözlüğü](belgeler/terimler-sozlugu.md) belgesini kullan.

## Görev seçimi

Kullanıcı belirli bir görev verdiyse onun bağımlılıklarını kontrol et. Aksi halde bağımlılıkları tamamlanmış, durumu hazir olan görevlerden en küçük oncelik değerini seç. Eşitlik halinde görev kimliğinin sayısal kısmı küçük olanı seç. devam_ediyor veya dogrulaniyor durumunda bir iş varsa önce gerçek dosyalarla kayıtların uyumunu inceleyerek o işi sürdür.

Engellendi durumundaki görevi, eksik bilgi gerçekten sağlanmadan otomatik olarak hazır yapma. Uygun görev bulunmuyorsa engelleri ve gereken sonraki girdiyi bildir. Görev durumunu devir notundan veya geçmiş raporlardan çıkarma; tek asıl kayıt [Görev Durum Kaydı](durum/gorev-durumu.yaml) dosyasıdır. Yeni masaüstü koşusu için [Windows İlk Adım](belgeler/windows-ilk-adim.md) belgesindeki oturum ve erişim sınırlarını izle. Envanteri test başarısı sayma.

## Oturum devri ve masaüstü sınırı

- Devir kaydı dosyalarla çelişirse gerçek kaynakları, görev kaydını ve koşu kanıtlarını incele; tamamlanmayı varsayma.
- Önemli adımlar tamamlandıkça görev kaydını ve gerekli [devir bilgisini](DEVIR.md) güncelle. Yalnız oturum sonunda kayıt bırakmaya güvenme; devir notuna ikinci bir ayrıntılı görev durum listesi yazma.
- Önceki ajanın yarım işlemini gerçek dosya, süreç ve kanıt durumunu kontrol etmeden tekrarlama. Aynı proje üzerinde iki geliştirme ajanını eşzamanlı çalıştırma.
- Windows masaüstü ve CanRat erişimini yeni araç veya oturum için ayrıca doğrula. Önceki aracın erişimini, onaylarını veya güvenlik bağlamını devralınmış kabul etme; kısıtlamaları aşma veya güvenlik ayarlarını değiştirme.
- Start'a basma, CAN bağlantısı başlatma veya kullanıcıya ait açık CanRat örneğini kapatma. Eski koşu kanıtlarını ve kabul kriterlerini değiştirme.

## Uygulama döngüsü

1. Girdileri ve kabul kriterlerini kontrol et. Eksik temel bilgi varsa belirt.
2. Yapılacak somut değişikliği kısa biçimde açıkla ve görev durumunu güncelle.
3. Kapsam içindeki değişikliği uygula.
4. Görevde tanımlı doğrulama komutlarını gerçekten çalıştır. Komut henüz belirli değilse bunu tamamlanmış doğrulama gibi sunma.
5. Test kimliği, beklenen ve gerçekleşen sonuç, kullanılan sürüm ve kanıt yolunu kaydet.
6. Otomasyon hatası varsa düzelt. Hedef uygulama kusuru varsa bulgu olarak kaydet. Beklenen sonucu testi geçirmek için değiştirme.
7. Görevin kabul kriterlerine göre tamamlandı veya engellendi kararı ver. Gerekçeyi ve kanıtı belirt.

## Durum ve tekrar sınırı

Durumların asıl kaynağı durum/gorev-durumu.yaml dosyasıdır. Yol haritasına veya görev dosyalarına ikinci bir güncel durum listesi ekleme. Kabul ölçütünü veya mimari kararı sessizce değiştirme; gerekçeyi ve etkisini kullanıcıya bildir.

Aynı sorunda sonuç vermeyen iki düzeltme girişiminden sonra otomatik tekrarı bırak, bulguları ve ihtiyaç duyulan kararı bildir. Bu başlangıç önerisi ileride kontrol kodunda uygulanacak ve mentörün beklentisine göre ayarlanacaktır. Şu an talimat düzeyindedir, zorunlu bir çalışma zamanı sınırı değildir.

## Çıktı biçimi

Kullanıcı ilk kez bu tür bir proje geliştiriyor. Açıklamalar Türkçe, kısa ve somut olsun. Sonuç mesajı şu bilgileri içersin: yapılan iş, değişen dosyalar, çalıştırılan kontrol, gözlenen sonuç, kalan engel ve sonraki adım. Yapılmamış işlemi yapılmış gibi gösterme.
