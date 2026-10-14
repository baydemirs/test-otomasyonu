# GOREV-003 — gerçek yaşam döngüsü kanıtı

2026-10-13. Kriterler koşudan önce [görev dosyasına](../gorevler/GOREV-003-uygulama-yasam-dongusu.md) yazıldı. Güncel durumun tek kaynağı [görev kaydıdır](../durum/gorev-durumu.yaml). Start'a basılmadı, CAN bağlantısı başlatılmadı; güvenlik ayarları değiştirilmedi. Gerçek denemeler mevcut komut bazlı onayla Admin'in Windows masaüstünde çalıştırıldı.

## Gerçek Windows denemeleri

| Başlangıç | Önceden belirlenen sonuç | Gözlenen sonuç |
| --- | --- | --- |
| Kullanıcının açık örneği | Bağlan, owned=false; kutu testi geçsin; aynı süreç açık kalsın | PID 18480, UTC başlangıç ticks `639274711768917415`. MEVCUDA_BAGLANILDI / GECTI / ACIK_BIRAKILDI. Kapatma isteği gönderilmedi. |
| Kullanıcı uygulamayı kapattıktan sonra | Süreç listesi boş; doğru klasörden başlat, owned=true; test geçsin; normal kapat | PID 21568, UTC başlangıç ticks `639274898668202904`. BASLATILDI / GECTI / KAPANDI. CloseMainWindow, çıkış 0, son süreç listesi boş. |

Açık örnek [yaşam döngüsü kaydı](kosular/yasam-e3da51bf022a4bf49311ac64e927c2b9/sonuc.json), [adım günlüğü](kosular/yasam-e3da51bf022a4bf49311ac64e927c2b9/yasam-adimlari.json), [kutu testi](kosular/canrat-ui-002-a929e7f41cba49e3995b27919bcc44e3/sonuc.json).

Kapalı başlangıç [yaşam döngüsü kaydı](kosular/yasam-ec0cd28b53e746119103326a7da341b6/sonuc.json), [adım günlüğü](kosular/yasam-ec0cd28b53e746119103326a7da341b6/yasam-adimlari.json), [kutu testi](kosular/canrat-ui-002-f865e30fed804d9188bd5f90d08ea6c8/sonuc.json).

Her iki kutu testinde de gerçek okuma `Off → On → Off`; geri yükleme doğrulandı. Start göstergesi Off/Start idi. Kapalı koşuda EXE ve çalışma klasörü tam olarak `hedef_uygulama/CANRAT_3min/CANRat.exe` ve onun üst klasörüydü. Açık koşu bitince kullanıcı kapatacağını bildirdi; uygulamayı kullanıcı kapattı. Otomasyon kullanıcıya ait örneği kapatmadı.

## Geliştirmede bulunan hata

[İlk koşu](kosular/yasam-4b0cd9a2145a47bf9b8d6d99bc185286/sonuc.json) HATA'dır; başarı kanıtı olarak kullanılmaz. Kutu testi geçmiş, uygulama açık kalmıştı; ancak Start-Process ile dönen nesnenin ExitCode değeri null idi. Alt süreci .NET Process ile başlatıp çıktıyı asenkron okuyan ve süreli beklemeden sonra çıkış kodunu alan uygulama kullanıldı. PowerShell dosyalarına Windows PowerShell'in Türkçe mesajları doğru okuması için UTF-8 BOM eklendi. Yeni koşu ayrı klasöre yazıldı; ilk kayıt düzeltilmedi.

## Otomasyon kontrolleri ve sınırlar

`demo_dogrula.py` artık görev sayısını sabitlemez. Benzersiz kimlik, mevcut dosya/kanıt, geçerli bağımlılık ve döngüsüzlük kontrol edilir. Tamamlanan görevde boş kanıt listesi reddedilir. Geçerli dördüncü görev, tek görev, yinelenen kimlik, bilinmeyen/kendine/döngülü bağımlılık, eksik dosyalar ve proje dışına çıkan yollar fixture testleridir; gerçek UI denemesi değildir.

Yaşam döngüsü kanıt doğrulayıcısı iki dalın güncel kaynak özetlerini, adım sırasını, süreç sahipliğini, iç testin kimliğini/zaman aralığını, stdout ile rapor eşleşmesini ve normal kapatma/açık bırakmayı kontrol eder. Değiştirilmiş bellek kopyaları üzerindeki olumsuz testler ve sahte süreç nesneleriyle sahiplik kontrolleri, gerçek uygulamada çoklu örnek veya kapatma arızası denendiği anlamına gelmez.

Pencere 15 saniye, iç test 55 saniye, normal kapatma 10 saniye, dış yürütücü 110 saniye ile sınırlıdır. Kesinti veya OS arızasında kapanış garantisi yoktur; kısmi kayıt başarı sayılmaz. Kilitler kullanıcı müdahalesini engellemez. Bu görev CAN donanımını, veri toplamayı veya CanRat'ın arka plan davranışlarını doğrulamaz.

GOREV-002'nin tarihsel tamamlanma kayıtları korunur. `demo_dogrula.py` bu görevde değiştiği için eski denetim paketi yeni doğrulayıcı sürümüne kanıt sayılmaz; güncel toplu denetim eski sürümü reddeder. Önceki test kriteri ve UI test kodu değiştirilmemiştir.

## Kaydedilmiş doğrulama sonuçları

- [37 birim testi](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/birim-testleri.json): tamamı geçti; 11 görev kaydı, 10 yaşam döngüsü kanıt kontrolü ve önceki 16 test.
- [6 sahte süreç kontrolü](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/sahte-sahiplik.json): sahip olunmayan süreç, yeniden kullanılan PID, farklı EXE, çıkmış süreç ve penceresiz süreç kapatılmadı; doğru sahte sahiplikte tek normal kapatma çağrısı yapıldı. Gerçek uygulama arıza testleri değildir.
- [İki gerçek dalın birleşik doğrulaması](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/yasam-kaniti.json): çıkış 0.
- [Dört görevli kayıt](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/gorev-kaydi.json): çıkış 0.
- [Önceki başarılı CANRAT-UI-002](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/eski-demo.json): değişmeyen test/kriter sürümleriyle hâlâ doğrulanıyor.
- [GOREV-002 eski doğrulayıcı sürümü reddi](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/eski-denetim-surum-reddi.json): beklenen çıkış 2; `Kanıt reddi denetimi eski doğrulayıcı sürümüne ait.`
- [Eski kayıt karşılaştırması](kosular/gorev003-24b7a2ddbd9549ab803cd3a81ae1928e/eski-kayit-karsilastirma.json): başlangıçta özetlenen 277 dosyanın tamamı aynı SHA-256 değerinde, eksik/değişen dosya yok.

Görev kapsamındaki iki gerçek başlangıç koşulu karşılandı. Kalan kapsam sınırı: çoklu gerçek örnek, OS kesintisi ve CanRat'ın kapanmayı reddetmesi bu yaşam döngüsü görevi sırasında gerçek uygulama üzerinde tetiklenmedi. Sonraki çalıştırmalar `py -3 tests/canrat_yasam.py --expected Auto` ile aynı kapsamda yapılabilir; yeni işlev testi bu görevin parçası değildir.
