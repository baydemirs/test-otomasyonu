# CANRAT-UI-002 — kayıt seçeneğini değiştir ve geri yükle

Kaynak: kullanıcının 2026-10-13 tarihli bu test kimliğiyle verdiği açık talimat. Bu kriterler envanterde görülen değerlerden türetilmedi.

Görev: GOREV-001. Hedef: üstteki `hedef_uygulama/CANRAT_3min/CANRat.exe`, tek açık örnek. Uygulama başlatılmaz veya kapatılmaz. Ek paket gerekmez; Python standart kütüphanesi ve Windows PowerShell/.NET UI Automation kullanılır.

## Ön koşul ve test verisi

- Start kontrolü `MainWindow.centralwidget.btnStart` yalnızca okunur. ToggleState=Off ve adı Start olmalı; iki ardışık okumada tutarlı olmalı. On veya Stop gözlenirse veri toplama etkin kabul edilerek ATLANDI kaydedilir. Okunamayan, Indeterminate veya çelişkili durum HATA'dır ve etkileşim başlatılmaz. Bu arayüz göstergesi fiziksel CAN trafiğinin yokluğunun kanıtı değildir.
- Hedef kutu `MainWindow.centralwidget.cboxAppendRecieved`; sınıf QCheckBox, tür CheckBox, etkin/görünür ve TogglePattern destekli olmalı.
- Test verisi ilk okunan kesin Off veya On değeridir. Off için beklenen geçiş On, On için Off; son beklenen değer ilk değerdir. Indeterminate geçerli başlangıç veya ara değer değildir.
- Test sırasında kullanıcı uygulamayla etkileşmemeli. Aynı PID için otomasyon koşuları mutex ile tekilleştirilir; bu kilit kullanıcı tıklamasını engellemez.

## Adımlar ve kabul kriterleri

1. EXE yoluyla tek pencereyi eşleştir; PID ve süreç başlangıç zamanını kaydet.
2. Start'ı ve hedefin ilk ToggleState değerini salt okunur kontrol et. Ön inceleme ayrı kayıt verir; etkileşim koşusunda ön koşul tekrar kontrol edilir.
3. İlk durumu disk günlüğüne yaz; yazma hatasında kutuyu değiştirme.
4. Yalnızca hedef kutunun TogglePattern.Toggle metodunu bir kez çağır. En fazla iki saniye içinde karşıt kesin değeri iki ardışık okumayla doğrula. İkinci Toggle ile ilk işlemi körlemesine tekrarlama.
5. finally bloğunda hedefin gerçek durumunu oku. İlk değerden farklıysa ve kesin Off/On ise en fazla bir Toggle ile geri yükle. Başlangıç değeri zaten mevcutsa yeniden değiştirme. İki ardışık okumayla geri dönüşü doğrula.
6. Start'ın hâlâ Off/Start olduğunu doğrula; Start üzerinde hiçbir etkileşim metodu çağırma.

GECTI için kesin ilk değer, karşıt değerin doğrulanması, ilk duruma dönüşün doğrulanması, pasif Start göstergeleri ve hatasız koşu birlikte gerekir. Okunamayan veya belirsiz durum GECTI olamaz. Kesin gözlem beklentiye uymuyorsa KALDI; güvenilir sonuç üretilememişse HATA. Geri yükleme hatası ayrı alanda kaydedilir ve genel sonucu HATA yapar. Veri toplama etkinse ATLANDI ve etkileşim yapılmadı kaydı gerekir.

## Hata, süre sınırı ve kanıt

Normal UIA doğrulama beklemeleri iki saniye, PowerShell alt süreci 30 saniye ile sınırlıdır. Alt süreç süre aşımında test HATA olur; ilk durum ve süreç kimliği disk günlüğünde varsa aynı süreç için ayrı, 12 saniyeyle sınırlı geri yükleme denenir. Başlangıç okunmamışsa veya süreç değişmişse tahminle Toggle yapılmaz. UIA sağlayıcısının takılması, uygulamanın kapanması ya da güç kesintisinde geri yükleme garanti edilemez; kanıt belirsizliği başarı sayılmaz. CanRat hiçbir durumda otomasyon tarafından sonlandırılmaz.

Her koşu benzersiz klasörde ilk/ara/son ToggleState, ön koşul gözlemleri, gerçek komutlar, çıkış kodları, süreler, EXE/kod/kriter özetleri, test ve koşu kimlikleri, sonuç ve ayrı temizlik hatası içerir. Başlangıç kontrolü ile gerçek test ayrı etiketlenir. Uygulama sürümü güvenilir ürün sürümü yoksa SHA-256 ile tanımlanır.

Teknik API kaynağı: [Microsoft TogglePattern](https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.togglepattern). Bu kaynak testin kabul beklentisi yerine geçmez.
