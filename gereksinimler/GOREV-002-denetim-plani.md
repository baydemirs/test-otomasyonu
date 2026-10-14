# GOREV-002 — çalıştırma öncesi denetim planı

Kaynak: kullanıcının 2026-10-13 tarihli GOREV-002 talimatı, görev dosyası ve genel doğrulama kriterleri. `CANRAT-UI-002.md` kabul kriterleri korunur (başlangıç SHA-256: `7c55db26c7fb8a7f5783231f88f86de73326f58a6d8ad390440d7c03e5593e1c`).

Her senaryoda ürün test sonucu ile denetimin beklenen davranışı karşılayıp karşılamadığı ayrıdır. Örneğin beklenen KALDI çıktısını almak denetim açısından uygundur; ürün testi GECTI olarak değiştirilmez. Gerçek masaüstü komutları mevcut komut bazlı onay yöntemiyle çalışır. Start yalnızca okunur; etkin veya belirsizse UI etkileşimi yapılmaz. Kullanıcının açtığı uygulama kapatılmaz; hiçbir başka EXE kopyası seçilmez.

| Kimlik | Ortam / yöntem | Çalıştırmadan önce beklenen |
| --- | --- | --- |
| D01 | Sahte bağlantı adaptörü, gerçek Python/PowerShell yürütücüsü; uygulama yok | HATA; sıfır Toggle, ilk durum bilinmiyor; uygulama kapatma yok |
| D02 | Sahte adaptörde gerekli kutu yok; ayrıca gerçek uygulamada salt okunur bulunmayan kimlik sorgusu | HATA; sıfır Toggle. Gerçek sorgu mevcut kutunun kaybolduğunu kanıtlamaz |
| D03 | Sahte adaptörde Toggle çağrısı durumu değiştirmiyor | KALDI; bir değişiklik çağrısı, tekrar yok; mevcut ilk durum okunup doğrulanır |
| D04 | Sahte adaptör ilk Toggle'dan sonra 45 saniye bekler; gerçek alt süreç 30 saniyede kesilir | HATA; 30 saniyelik gerçek timeout, ayrı 12 saniye limitli kurtarma; geri yükleme başarılı olsa da test HATA kalır |
| D05 | Sahte adaptörde ilk değişiklik olur, geri Toggle hata verir | HATA; cleanup_error ayrı, restored=false; sonsuz tekrar yok |
| D06 | Aynı tanımlı gerçek test iki yeni koşu | Her ikisi GECTI; aynı ilk değer, karşıt değer, ilk değere dönüş; Start Off/Start |
| D07 | Gerçek uygulamada yalnız izinli kutu değiştirilip denetim alt süreci bilinçli sonlandırılır; yeni süreç günlüğü ve gerçek kutuyu okur | Kesilen koşu HATA/yarım, asla GECTI değil. Yeni Inspect günlüğün ilk değeriyle mevcut karşıt değerin farkını gösterir; Recover aynı PID/başlangıç zamanında mevcut duruma göre ilk değere döner |
| D08 | Başarılı koşunun ayrı kopyalarında eksik rapor, adım günlüğü, zorunlu alan, sürüm girdisi | Tamamlama denetimi her birini açık nedenle reddeder |
| D09 | Ayrı kanıt kopyasında eski kod özeti / belirsiz adım / kesinti kaydı | Tamamlama denetimi reddeder; eski özgün başarılı koşu ve kriter değiştirilmez |
| D10 | Ayrı çalışma ağacında bozuk görev/belge yolu | Tamamlama denetimi eksik girdiyi reddeder |
| D11 | Sahte işlem başarısızlığında kayıtlı iki deneme hakkı | İki başarısız denemeden sonra üçüncü çağrı yapılmadan reddedilir; yeni süreç aynı kayıtla bu sınırı korur |
| D12 | Sahte okumada Indeterminate / Start On | Belirsiz kutu HATA; etkin veri toplamada ATLANDI; sıfır Toggle |

D01/D02 sahte ön koşulları uygulamanın gerçekten kapatılması yerine kullanılır. D04'te zaman sınırı gerçekte geçer, hedef CanRat değildir; D05 için gerçek uygulamanın geri yüklemesi kasıtlı bozulmaz. D07 gerçek UI üzerinde kontrollü test-alt-süreci kesintisidir; elektrik kesintisi veya Codex konuşmasının kapatılması olarak sunulmaz. Kurtarma başarısızsa hemen raporlanır ve daha fazla gerçek etkileşim yapılmaz.

Her alt deneme önceden belirlenen beklentisi, mod etiketi, gerçek komut, stdout/stderr/çıkış kodu, süre ve dosya özetiyle benzersiz bir denetim klasörüne yazılır. Sahte adaptör kopyaları `SAHTE_ADAPTOR` manifestiyle etiketlenir; normal üretim testine hata enjeksiyon bayrağı eklenmez. Tamamlama denetimindeki bir kusur bulunursa ilk reddedilmeyen örnek korunur, otomasyon düzeltilir ve etkilenen kontroller yeniden çalıştırılır. Kabul kriteri değiştirilmez.

Tamamlama ancak tüm gerekli denetimler beklenen davranışı üretirse, gerçek kutu ilk durumuna dönmüşse, kanıt/kod tutarlılığı sağlanmışsa ve kalan sınırlar raporlanmışsa verilir. Çevre engeli veya karşılanmayan bir kriter varsa görev engellendi olarak gerekçesiyle kaydedilir.
