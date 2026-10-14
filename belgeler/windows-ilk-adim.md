# Windows İlk İnceleme

Amaç, açık CanRat uygulamasındaki arayüz kontrollerinin Windows UI Automation aracılığıyla okunup okunamadığını görmek. UI Automation, programın düğme ve alanlarını isim ve kimlikleriyle sorgulamaya yarayan Windows arayüzüdür. Bu belge salt okunur envanter içindir; gerçek kutu testi [README](../README.md) içindeki pytest komutuyla çalışır.

## Ön koşullar

Windows masaüstü oturumu, Python 3.9 veya üzeri ve Windows PowerShell gerekir. Ek Python paketi kurulmaz. Python sürümünü `py -3 --version` ile kontrol et. `py` yoksa `python --version` kullanılabilir; bu komut gerçekten Python 3.9+ döndürmelidir. Python yoksa sonucu geliştiriciye bildir; rastgele kurulum komutu çalıştırma.

CanRat klasörünü DLL'leriyle birlikte çıkar. Beklenen uygulama yolu proje köküne göre `hedef_uygulama/CANRAT_3min/CANRat.exe`. İçte `CANRAT (1)` adlı ikinci kopya da var; ilk çalışmada üstteki kopyayı kullan. Aynı dosyayı normal Windows oturumunda aç; tek örnek açık olsun. VS Code ve hedef uygulamanın erişim seviyeleri farklıysa erişim sorunu çıkabilir; otomatik yönetici yetkisi veya güvenlik politikası değişikliği yapılmaz.

## Çalıştırma

VS Code terminalinde proje kökünden:

```powershell
py -3 otomasyon/inceleme/canrat_incele.py --exe ".\hedef_uygulama\CANRAT_3min\CANRat.exe"
```

`py` bulunmuyor ama uygun `python` çalışıyorsa aynı komutun başında `python` kullan. Başka bir klasördeki uygulama için `--exe` değerini o CANRat.exe dosyasının gerçek tam yoluyla değiştir. Boşluk içeren yolları çift tırnak içine al.

Araç pencereyi açmaz, kapatmaz, düğmelere basmaz veya CAN mesajı göndermez. Hedef dosya yoluyla açık süreç eşleştirilir; tüm masaüstünün kontrol ağacı toplanmaz. Uygulamanın doğal arka plan davranışı bu araç tarafından durdurulmaz.

## Sonuç

Her çalıştırma `raporlar/kosular/inceleme-<kimlik>/arayuz-envanteri.json` üretir. Dosya; uygulama ve araç özetlerini, komutu, süreç kimliğini ve okunan kontrolleri içerir. Özel yoldaki uygulama adı ve arayüzde görünen metinler raporda bulunabilir; paylaşmadan önce içeriğe bak.

- `GOZLEM_ALINDI`: Envanter okunmuş. İşlevin doğru çalıştığı veya GOREV-000'ın tamamlandığı anlamına gelmez.
- `ENGELLENDI`: Ortam eksik, uygulama bulunamadı, çıktı eksik, kontroller okunamadı veya inceleme süre aşımına uğradı. Açıklama rapordadır.
- `test_sonucu` daima `null`: Bu araç geçti/kaldı kararı vermez.

Çıkış kodu 0 envanter alındığını, 2 incelemenin engellendiğini, 3 raporun yazılamadığını gösterir. Varsayılan alt süreç sınırı 25 saniyedir. Süre aşımında yalnızca aracı çalıştıran PowerShell alt süreci sonlandırılır; CanRat sonlandırılmaz. İşletim sistemi süreç başlatması ve dosya yazma süresi bu sınıra dahil değildir.

PowerShell yürütme politikası scripti engelliyorsa hata kaydını paylaş; politika atlatma veya kalıcı güvenlik ayarı değişikliği yapma. Gerekirse ekip tarafından izin verilen inceleme yöntemi seçilir.

## Sonraki adım

Önceki Codex oturumunun Windows sandbox'ı, kullanıcının terminalinden farklı kullanıcı ve özel masaüstünde çalışabildi. O oturumda envanter komutu desteklenen komut bazlı onay yöntemiyle ayrıca çalıştırıldı ve aynı envanter alındı. Ölçümler, sınırlar ve yerel çalıştırıcı değerlendirmesi [Windows erişim farkı raporundadır](../raporlar/windows-erisim-farki.md). Bu erişim ve onay yeni araca aktarılmış sayılmaz; yeni araç kendi Windows masaüstü erişimini doğrular. Güvenlik yapılandırmasını değiştirmek veya onay reddini başka yoldan aşmak bu yöntemin parçası değildir.

Oluşan JSON'daki gerçek kontrol adlarını ve kimliklerini değerlendir. Kontroller okunamıyorsa erişim engelini raporla. Boş listeyi başarı veya tıklama koordinatlarını güvenilir çözüm kabul etme.

## Teknik kaynaklar

- [Microsoft UI Automation FindAll](https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.automationelement.findall)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)

Bu kaynaklar erişim ve süre sınırı uygulamasını açıklar; CanRat üzerinde uyumluluk kanıtı değildir.
