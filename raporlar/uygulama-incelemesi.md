# CanRat Uygulama İncelemesi

Tarih: 2026-10-13. İlk bölümler statik paket ve gönderilen ekran görüntüsü incelemesidir. Windows erişim kayıtları aşağıda ayrı tutulmuştur. Sonradan seçilen ve çalıştırılan ilk etkileşim senaryosu [CANRAT-UI-002 raporundadır](canrat-ui-002.md); eski inceleme kayıtları kendi kapsamlarında korunmuştur.

## Doğrulananlar

CANRAT_3min.zip içinde CANRat.exe, Qt6Core/Gui/Widgets/SerialBus DLL'leri, CAN eklentileri, obj dosyaları ve Qt'nin ürettiği moc dosyaları var. main.cpp, mainwindow.cpp gibi tam uygulama kaynakları ve proje yapılandırması yok. Qt'nin ürettiği moc dosyaları uygulamanın davranış kaynak kodu yerine geçmez.

Paket üstte CANRAT_3min/CANRat.exe, ayrıca CANRAT_3min/CANRAT (1)/CANRat.exe içeriyor. İncelemede kullanılacak kopya üstteki olacak. Arşiv adındaki 3min ifadesinin çalışma süresi sınırı anlamına geldiği doğrulanmadı.

Ekranda PCAN seçimi, Scan, Start, ECU/EDM durumu, iki kayıt seçeneği, zaman aşımı sayaçları, kayıt alanı, Clear, Copy to Clipboard ve Open Log Folder var. Görülen başlangıç değerleri kabul kriteri değil, gözlemdir.

ReadMe.txt sinyal kimliği ve süre ayarlama kontrollerinden söz ediyor; bunlar gönderilen ekranda görünmüyor. Hangi açıklamanın bu sürüm için geçerli olduğu doğrulanmalı. README Clear için ekranı temizlediğini söylüyor; dolu bir kayıt alanını donanımsız nasıl hazırlayacağımız henüz bilinmiyor. Boş alanı temizlemek yeterli işlev kanıtı sayılmamalı.

## İlk test adayı

Bu başlangıç ekranı adayı, kullanıcının 2026-10-13 tarihli açık talimatıyla [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md) kutu etkileşim senaryosuyla değiştirildi. Kesin kriterler kullanıcı talimatından alındı; araç Python + Windows PowerShell/.NET UIA olarak seçildi. Gerçek koşu ayrı demo raporundadır.

Donanımsız başlangıç ekranı testi: uygulamayı aç, ana pencereyi ve gerekli kontrolleri doğrula, raporla ve yalnızca testin açtığı örneği kapat. Pencere/kontrol tanımları ve beklenen başlangıç değerlerinin kaynağı GOREV-000 bitmeden netleştirilecek. Henüz yürütülebilir test veya onaylı kriter değildir.

## Sonraki inceleme

[Windows ilk adım](../belgeler/windows-ilk-adim.md) ile kullanıcının Windows terminalinde gerçek UI Automation envanteri alındı; aşağıdaki kayıt erişimin kapsamını ve sınırlarını açıklar. Python, yalnızca ilk inceleme aracı için seçildi. Kalıcı GUI test kütüphanesi henüz seçilmedi; ilk testin kesin kabul kriterleri gereksinim kaynağından belirlenmeli.

## Windows ön inceleme kaydı — 2026-10-13

Çalıştırma kimliği: `1d9e47e8120b475695fd24979f21d5c7`. Bu ek kayıt ortam ve erişim incelemesidir; yukarıdaki statik ekran gözlemlerini gerçek kontrol envanterine dönüştürmez.

- Windows sürüm çıktısı: `Microsoft Windows NT 10.0.28000.0`; PowerShell: `5.1.28000.1`.
- `py -3 --version`: `Python 3.14.4`; aracın kullandığı yorumlayıcı: `C:\Python314\python.exe`. Kurulum yapılmadı.
- `Test-Path -LiteralPath hedef_uygulama/CANRAT_3min/CANRat.exe`: `False`. `hedef_uygulama` altında yalnızca `README.md` görüldü; proje içinde özyinelemeli dosya aramasında CANRat.exe bulunamadı. Başka kopya seçilmedi.
- `Get-Process -Name CANRat` sorgusunda süreç sayısı `0`; hedef masaüstü penceresine erişim doğrulanamadı.
- Çalıştırılan komut: `py -3 araclar/canrat_incele.py --exe ".\hedef_uygulama\CANRAT_3min\CANRat.exe"`.
- [Üretilen JSON](kosular/inceleme-1d9e47e8120b475695fd24979f21d5c7/arayuz-envanteri.json) okunarak incelendi: `inceleme_durumu=ENGELLENDI`, `test_sonucu=null`, `gozlem=null`, `uygulama_sha256=null`. Araç sürümü SHA-256 ve gerçek komut JSON'da kayıtlıdır; uygulama sürümü dosya olmadığı için belirlenemedi.
- Engel hedef dosyanın eksikliğidir. UI Automation alt süreci çalıştırılmadığından UIA erişimi ve script yürütme politikasının izin verip vermediği sınanmadı. Güvenlik ayarı değiştirilmedi.
- Gerçek kontrol adı, AutomationId, kontrol türü, etkinlik bilgisi veya pattern okunamadı. Bu durum boş envanter başarısı değildir. İşlev testi, test verisi, beklenen sonuç ve geçti/kaldı kararı yoktur.

Sonraki erişim adımı: kullanıcı paketi DLL ve alt klasörleriyle belirtilen konuma sağlamalı ve aynı CANRat.exe dosyasını normal Windows oturumunda tek örnek olarak açmalıdır. Ardından yalnızca envanter komutu yeniden çalıştırılabilir. İlk işlev testinin kesin kabul kriterleri ayrıca netleştirilecektir. Bu incelemede uygulama açılmadı/kapatılmadı, düğmelere basılmadı ve CAN bağlantısı başlatılmadı.

## Windows envanter tekrarı — 2026-10-13

Çalıştırma kimliği: `d5cc5dd8052f457b84d059112219b313`. Kullanıcının uygulamayı yerleştirip açtığını bildirmesinden sonra yalnızca envanter komutu tekrar çalıştırıldı:

```powershell
py -3 araclar/canrat_incele.py --exe ".\hedef_uygulama\CANRAT_3min\CANRat.exe"
```

- Hedef dosya bu kez mevcut (`Test-Path=True`); Python `3.14.4`. Üstteki EXE kullanıldı. `CANRAT (1)/CANRat.exe` kopyası da bulundu, seçilmedi.
- Uygulama SHA-256: `0b9bd8141cf4d78e9232a0d4747786692778e44868ffdfe2d7037f2d0902540d`. Araç ve UIA yardımcısının özetleri, zaman ve komutlar [yeni JSON kaydında](kosular/inceleme-d5cc5dd8052f457b84d059112219b313/arayuz-envanteri.json) tutuldu; önceki kayıt korundu.
- Envanter komutunun gerçek çıkış kodu `2`; UIA alt sürecinin çıkış kodu da `2`. Hata: `Open the specified CANRat.exe first, in this Windows session. Check path and privilege level.`
- JSON incelendi: `inceleme_durumu=ENGELLENDI`, `gozlem=null`, `test_sonucu=null`. Kontrol ağacı okunmadı; gerçek kontrol adı, AutomationId, kontrol türü veya pattern bilgisi yok.
- Salt okunur süreç sorgusunda CANRat PID `18480`, `SessionId=1`, `Path=null`, `MainWindowHandle=0`, `MainWindowTitle=""` gözlendi. Sorguyu çalıştıran PowerShell oturumunun `SessionId` değeri de `1`. Bu veriler açık sürecin hangi EXE kopyası olduğunu doğrulamaya yetmiyor; uygulamanın kapalı olduğunu da kanıtlamıyor.
- Araç, hedef dosya yolu ve sıfırdan farklı ana pencere tanıtıcısını birlikte aradığı için pencereyi eşleştiremedi. Erişim yetkisi, araç yürütme ortamının masaüstü görünürlüğü veya uygulamanın pencere durumu arasından kesin neden belirlenmedi. Scriptin kendi hata mesajına ulaşıldı; bu çalıştırmada yürütme politikası engeli raporlanmadı.

Sonraki adım: aynı komutu kullanıcının normal Windows masaüstü oturumundaki VS Code terminalinde çalıştırıp oluşan JSON ile karşılaştırmak. Bu, araç ortamına özgü erişim farkını ayırmaya yardımcı olur; yönetici yetkisi veya güvenlik politikası değişikliği önerilmedi/uygulanmadı. Uygulamaya tıklanmadı, uygulama açılmadı/kapatılmadı, CAN bağlantısı başlatılmadı ve işlev testi yapılmadı. Gözlemler kabul beklentisine veya geçmiş test sonucuna dönüştürülmedi.

## Kullanıcı terminalinden gerçek UIA envanteri — 2026-10-13

Kaynak: [arayuz-envanteri.json](kosular/inceleme-d7679e4918a248da89b1d69bad4825e7/arayuz-envanteri.json). Komutu kullanıcı kendi terminalinde çalıştırdı; Codex oluşan dosyayı okuyup inceledi. Kayıt zamanı `06:56:03 UTC` (`09:56:03 Europe/Istanbul`), çalıştırma kimliği `d7679e4918a248da89b1d69bad4825e7`.

- `GOZLEM_ALINDI`, `test_sonucu=null`, UIA alt süreç çıkış kodu `0`.
- Hedef yol üstteki `hedef_uygulama/CANRAT_3min/CANRat.exe`; PID `18480`. Uygulama ve iki araç dosyasının SHA-256 değerleri önceki denemenin kayıtlarıyla aynı.
- Ana pencere adı `ECEMTAG - CanRat`, AutomationId ve sınıf `MainWindow`, framework `Qt`, tür `Window`.
- Ana pencereye ek olarak 22 alt öğe bulundu; `truncated=false`, `read_errors=[]`. Ana pencere ve 22 öğenin tamamında `enabled=true`, `offscreen=false`. Bu özellikler etkileşim başarısını kanıtlamaz.
- 21 alt öğenin AutomationId değeri dolu ve bu kayıt içinde benzersiz; `QSizeGrip` öğesinin kimliği boş. Kimliklerin başka sürümlerde veya yeniden açılışta kararlılığı sınanmadı.

Aşağıdaki kimlikler `MainWindow.centralwidget.` önekiyle tamamlanır. Türler UIA'nın bildirdiği türlerdir; metinler aynen korunmuştur.

| Gözlenen ad / alan | AutomationId son kısmı | UIA türü | Bildirilen pattern'lar |
| --- | --- | --- | --- |
| PCAN seçim alanı; Name boş | cmbUsb | ComboBox | Invoke, Value, ExpandCollapse |
| Scan | btnScanPCan | Button | Invoke, Value |
| Append Recieved CAN ID | cboxAppendRecieved | CheckBox | Invoke, Value, Toggle |
| Start | btnStart | CheckBox | Invoke, Value, Toggle |
| N/A (ECU) | lblECUStatus | Text | Invoke |
| N/A (EDM) | lblEDMStatus | Text | Invoke |
| Append Timeout CAN ID | cboxAppendTimeout | CheckBox | Invoke, Value, Toggle |
| ECU timeout counter: | lblECUtimeoutCounter | Text | Invoke |
| EDM timeout counter: | lblEDMtimeoutCounter | Text | Invoke |
| Kayıt alanı; Name boş | edtLogView | Edit | Invoke, Value, Text |
| Open Log Folder | btnLogFolder | Button | Invoke, Value |
| Copy to Clipboard | btnCopyTextEdit | Button | Invoke, Value |
| Clear | pushButton | Button | Invoke, Value |

Diğer dokuz alt öğe: merkezi QWidget grubu, `CAN Rat`, `Select Pcan`, `ECU Status:`, `EDM Status:` metinleri, kayıt alanının viewport grubu, menü çubuğu, durum çubuğu ve QSizeGrip. Tam kimlik/sınıf bilgileri JSON'dadır.

Önemli sınırlar:

- Start kontrolünün Qt sınıfı `QPushButton`, UIA türü ise `CheckBox`. İleride yalnızca Button türüyle aranması kontrolü kaçırabilir. Bu farklılık ürün hatası olarak sınıflandırılmadı; hiçbir pattern çağrısı ile etkileşim denenmedi.
- Araç pattern isimlerini listeler; Value, Text veya Toggle değerlerini okumaz. PCAN seçimi, kutuların işaret durumu ve log içeriği bilinmiyor. Boş Name, boş log veya boş seçim kanıtı değildir.
- ECU/EDM için `N/A` gözlendi. Sayaç adlarında sayısal değer yok; sayaçların sıfır olduğu çıkarılamaz. Bu gözlemler başlangıç beklentisi veya kabul kriteri değildir.
- UIA üzerinden öğe bulma kullanıcı terminalinde kanıtlandı. Önceki Codex araç oturumu aynı PID için pencere/yol okuyamamıştı; iki kayıttaki fark kesin güvenlik politikası veya yetki teşhisi değildir. Güvenlik ayarı değiştirilmedi.

Erişim yöntemi olarak hedef süreç/pencereyle sınırlandırılmış UIA sorgusu bu sürüm için uygulanabilir görünüyor. İleride seçiciler AutomationId ve gerektiğinde sınıf/tür ile değerlendirilebilir; yeniden açılış kararlılığı ve pattern davranışı henüz doğrulanmadı. Yeni paket kurulmadı, kalıcı test kütüphanesi seçilmedi. İlk test için mentör/uygulama gereksiniminden kesin adımlar, beklenen sonuçlar ve araç zorunluluğu netleştirilmeli; envanter bu beklentilerin kaynağı yerine geçmez. Bu aşamada işlev testine geçilmedi.

## Codex'ten desteklenen çalıştırma kanıtı — 2026-10-13

[Erişim farkı raporunda](windows-erisim-farki.md) kullanıcı/oturum, mimari, token ve masaüstü farkları kanıtlarıyla incelendi. Codex'in varsayılan sandbox çağrısı engellendi; aynı envanter komutu desteklenen komut bazlı onayla Codex araç çağrısından başarıyla çalıştı. [Yeni envanter](kosular/inceleme-a80d716fb435418097a3c3bf0237a2b0/arayuz-envanteri.json) kullanıcı terminalindeki önceki gözlemle birebir aynı 22 alt öğeyi içeriyor; test_sonucu null. Elle komut çalıştırılması bu denemede gerekmedi. Güvenlik ayarları değiştirilmedi. Yerel çalıştırıcı seçeneği raporda değerlendirildi; kurulmadı. İşlev testine geçilmedi.

## Ana servis bulguları (statik kayıt)

Prosedürün değişiklik tablosu 13.09.2024 tarihli sürüm 1'i gösteriyor; güncel gereksinim olduğu varsayılmıyor. Sayısal ölçüm, ekran kontrolü, dosya dışa aktarma, flash, kalibrasyon, kayıt silme ve saha/Dyno adımları ayrı ihtiyaçlar. MASG1425 TCU adımının kriterinde ECU yazıyor. MASG1419 beklenen sürümlerini 6241/6240 olarak sabitliyor. Bunlar katalog hazırlanırken kaynağı korunarak netleştirilecek.

Kaynak dosya özetleri [kaynak kaydında](../gereksinimler/kaynak-kaydi.json). Paylaşılan ikili uygulama ve Word dosyası bu otomasyon ZIP'ine yeniden eklenmedi.
