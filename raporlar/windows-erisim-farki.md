# Windows masaüstü erişim farkı

Tarih: 2026-10-13. Görev: GOREV-000. Kapsam: salt okunur erişim tanısı ve mevcut arayüz envanteri; işlev testi değildir.

## Sonuç

Codex mevcut envanter komutunu kendi araç çağrısından, desteklenen komut bazlı onay mekanizmasıyla başarıyla çalıştırdı. Kullanıcının elle komut çalıştırması bu denemede gerekmedi. Güvenlik yapılandırması değiştirilmedi. Varsayılan sandbox ile masaüstü uygulaması farklı hesap, masaüstü ve bütünlük düzeyinde çalışıyor. Oturum numarası ve mimari aynı; bu iki bilginin eşitliği masaüstü erişimini garanti etmiyor.

## Kanıtlar ve karşılaştırma

Karşılaştırılan güncel tanılar aynı betik SHA-256 değerini içeriyor: `20129591a5553132f09525826aa166b16e32399d08d749e00ecef053fbc8c78c`.

| Özellik | Varsayılan Codex sandbox | Onaylı araç çalıştırması | CANRat PID 18480 |
| --- | --- | --- | --- |
| Hesap | DESKTOP-3T8K47G\CodexSandboxOffline | DESKTOP-3T8K47G\Admin | DESKTOP-3T8K47G\Admin |
| Kullanıcı SID son kısmı | 1002 | 1000 | 1000 |
| Windows oturumu | 1 | 1 | 1 |
| Süreç mimarisi | x64 Python | x64 Python | x64 |
| Bütünlük SID | S-1-16-8192 (orta) | S-1-16-12288 (yüksek) | S-1-16-12288 (yüksek) |
| TokenElevation | 0 | 1 | 1 |
| TokenUIAccess | 0 | 0 | 0 |
| Window station | WinSta0 | WinSta0 | Görülen hedef pencere Default masaüstünde |
| Masaüstü | CodexSandboxDesktop-6a3dca74d4fe9adbff17dc5c1901b4f9 | Default | Default |
| Hedef pencere görünürlüğü | Hedef HWND kaydı yok; EnumWindows false döndü, ek hata kodu 0 | Dört hedef HWND, biri görünür | Görünür HWND 263894, thread 5964 |

Tanı kayıtları:

- [Sandbox tanısı](kosular/erisim-bb5d56e58dd24b8489e61f914fbb6b61/windows-erisim.json), 10:09:00 Türkiye saati.
- [Onaylı çalıştırma tanısı](kosular/erisim-43633e50861a4de2b48a8fbe6fb62355/windows-erisim.json), 10:09:04 Türkiye saati.
- [Sandbox envanter denemesi](kosular/inceleme-7de9ddb68d764ee49bf02aad0e652e22/arayuz-envanteri.json): ENGELLENDI, alt süreç ve envanter çıkış kodu 2.
- [Codex'in başarılı envanteri](kosular/inceleme-a80d716fb435418097a3c3bf0237a2b0/arayuz-envanteri.json): GOZLEM_ALINDI, alt süreç ve envanter çıkış kodu 0.
- [Kullanıcının önceki başarılı envanteri](kosular/inceleme-d7679e4918a248da89b1d69bad4825e7/arayuz-envanteri.json).

İlk tanı `erisim-7312bbb294854f5083c57f262dc3866d` kaydında EnumWindows son hata değeri önceki API çağrısından kalmıştı. Tanı aracı bu sorgudan önce son hatayı sıfırlayacak şekilde düzeltildi; karşılaştırmada düzeltilmiş `erisim-bb5d...` kaydı kullanıldı. False dönüş ve sıfır hata kodu belirli bir erişim reddi kodu olarak yorumlanmadı.

`IsWow64Process2` iki Python süreci ve hedef için process_machine=0, native_machine=34404 (0x8664) döndürdü. Envanter alt komutunun kullandığı `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` PE makine alanı ayrıca 0x8664 olarak okundu. Dolayısıyla 32/64 bit farkını gösteren kanıt yok.

Kullanıcının önceki JSON'u token veya masaüstü bilgisi içermez; geçmiş terminalin tam güvenlik bağlamı geriye dönük kesinleşmiş sayılmadı. Yeni onaylı çalıştırma bu alanları doğrudan ölçer ve aynı PID, EXE özeti ve gözlem ağacını tekrar üretir.

## Neden

Sandbox içinde süreç görünmesine rağmen Get-Process ile Path null, MainWindowHandle 0 dönüyordu. Yeni tanıda yalnızca PROCESS_QUERY_LIMITED_INFORMATION ile hedef EXE yolu ve TOKEN_QUERY ile token bilgileri okunabildi. Önceki boş Path, EXE'nin bulunmadığını veya hiçbir süreç bilgisine erişilemediğini kanıtlamıyordu.

Envanter yardımcısı doğru EXE yolunu ve sıfırdan farklı MainWindowHandle değerini birlikte arıyor; sandbox çağrısı UIA kontrol ağacına ulaşmadan bu eşleştirmede sonlanıyor. Ayrı sandbox masaüstü doğrudan ölçüldü. Ayrıca sandbox orta, CANRat yüksek bütünlük düzeyinde; bu ikinci fark daha sonraki UIA erişimi açısından da önemlidir. Deneme hesap, masaüstü ve token bağlamını birlikte değiştirdiği için bu etkenlerin tek tek katkısı ayrıştırılmadı. Güvenlik sınırlarını değiştirerek ayrıştırma yapılmadı.

OpenAI, Windows sandbox'ın ayrı düşük yetkili kullanıcılar ve özel masaüstü kullandığını belgeliyor: [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox). Windows masaüstleri ayrı UI nesneleri/barındırma sınırlarıdır: [Microsoft Desktops](https://learn.microsoft.com/en-us/windows/win32/winstation/desktops). Yüksek bütünlük düzeyindeki uygulamaya UI erişimi ayrıca güvenlik kısıtlarına tabidir: [Microsoft UI Automation security](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview). Bu kaynaklar ölçülen farkları açıklar; tek başına hedef üzerinde başarı kanıtı değildir.

## Denenen desteklenen yöntem

Varsayılan exec_command çağrısı ile salt okunur tanı ve şu mevcut komut çalıştırıldı:

```powershell
py -3 araclar/canrat_incele.py --exe '.\hedef_uygulama\CANRAT_3min\CANRat.exe'
```

Ardından aynı komut, `exec_command` aracının `sandbox_permissions=require_escalated` seçeneğiyle, yalnızca tanı ve envanter için gerekçelendirilerek mevcut otomatik onay incelemesine sunuldu. İnceleme izin verdi ve araç komutu çalıştırdı. Genel full-access ayarı, kalıcı izin/prefix kuralı veya sandbox yapılandırması değiştirilmedi. Bu seçenek komutun sandbox dışında çalıştırılma isteğidir; Windows'ta mutlaka yeni bir UAC yükseltmesi anlamına gelmez. Ölçülen bağlam burada zaten yüksek bütünlük düzeyindeki Admin token'ıdır. RunAs, kullanıcı taklidi, token çoğaltma, masaüstü değiştirme, UIAccess veya SeDebugPrivilege kullanılmadı.

Envanter: ECEMTAG - CanRat ana penceresi ve 22 alt öğe; truncated=false, read_errors=[]. Test sonucu null. Önceki kullanıcı envanteriyle `gozlem` nesnesi birebir aynı. Uygulama, Python inceleme aracı ve PowerShell yardımcısının özetleri de aynı. Bu, elde edilen sonucun farklı EXE veya değiştirilmiş envanter aracıyla üretilmediğini destekler.

Yürütme politikası salt okunur kontrol edildi; LocalMachine RemoteSigned, diğer kapsamlar Undefined. Önce/sonra çıktılar aynı. Politikayı atlatan parametre yok. Herhangi bir ACL, UAC, Defender veya firewall değişikliği yapılmadı. Hedef uygulama açılmadı/kapatılmadı ve girdi gönderilmedi.

## Önerilen çalışma düzeni

Şu aşamada ek çalıştırıcı gerekmez. Dosya ve rapor işleri varsayılan sandbox'ta, masaüstü envanteri ise kapsamı belirli komut olarak mevcut onay incelemesinden geçirilerek yürütülebilir. Onayın ileride de otomatik verileceği garanti edilmez; ret halinde başka yoldan aynı erişim denenmez. Kalıcı geniş Python/shell çalıştırma izni önerilmez. Özellikle bu ortamda onaylı komut yüksek token aldığı için komut ve çalışacak kod her çağrıda dar kapsamda incelenmelidir. Henüz işlev testi yetkilendirilmemiştir.

Masaüstü testinde ileride en az ayrıcalık hedefi, uygulama gerektiriyorsa aynı mevcut yetki düzeyiyle sınırlı çalışmak; mümkünse normal kullanıcı düzeyindeki hedef ve test ortamını ekip kararıyla kullanmaktır. Bu inceleme için çalışan uygulamanın yetkisi veya açılış düzeni değiştirilmedi.

## Yerel çalıştırıcı seçeneği

Doğrudan yöntem başarıyla çalıştığı için yerel servis veya kalıcı arka plan süreci kurulmadı. Gelecekte kurum politikasıyla ayrıca onaylanan bir entegrasyon olarak değerlendirilebilir; sandbox veya onay reddini dolanmak için kullanılmamalıdır.

Güvenli tasarımın asgari sınırları:

- Kullanıcının etkileşimli Windows oturumunda çalışır; Session 0 servisi yerine hedefle aynı masaüstü/token bağlamı doğrulanır. Kurulum/oturum açılışı bir kez kullanıcı veya BT tarafından yönetilir; her koşuda elle komut gerekmez.
- Yalnızca tanımlı `canrat_envanter` işlem kimliğini kabul eder. İstemci exe yolu, script yolu, shell komutu, Python kodu, PID veya ek argv gönderemez. İzinli işlem sabit hedef EXE ve sabit argümanlarla shell=False çalışır. İşlev testleri ayrıca kabul kriteri ve yetkilendirme olmadan eklenmez.
- Named pipe gibi yerel IPC, uzak istemci reddi, açık istemci kimlik doğrulaması ve asgari ACL ile kurulur. Loopback tek başına kimlik doğrulaması sayılmaz. Sandbox kimliğine erişim açılması güvenlik sınırı genişletir; ayrıca politika onayı gerekir. Bu incelemede ACL/IPC erişimi açılmadı.
- Çalıştırıcı ve çalıştırdığı kod, istemcinin yazabildiği çalışma alanından ayrı güvenilir konumda tutulmalı; onaylı sürüm/özet doğrulanmalıdır. Codex'in değiştirebildiği Python dosyasını yüksek yetkiyle sabit isim altında çalıştırmak, yalnızca işlem adı allowlist'i olsa bile genel kod çalıştırma riski taşır. Özet ve manifest de istemcinin değiştirebildiği yerde tutulursa bu güvenlik sınırı değildir.
- Tek aktif koşu, sınırlı kuyruk/mesaj/çıktı boyutu, 25 saniyelik mevcut inceleme sınırı ve sınırlı toplam koşu süresi; süre aşımında yalnızca yürütücüye ait alt süreçler durdurulur, CANRat kapatılmaz. İstek kimliğiyle tekrarların yeni koşu başlatması önlenir; başarısızlık sessiz başarıya dönüştürülmez.
- Her koşu için istemci kimliği, çalıştırıcı/uygulama özetleri, oturum/masaüstü, gerçek komut, çıkış kodu ve benzersiz rapor kaydı tutulur. Bilinmeyen işlem, bozuk istek, hedef yolu farklılığı ve birden fazla hedef pencere reddedilir.

Bu yalnızca tasarım değerlendirmesidir; uygulanmış veya güvenlik doğrulaması yapılmış bir çalıştırıcı değildir.

## Kalanlar

GOREV-000 için gerçek envanter ve Codex'ten desteklenen çalıştırma kanıtı mevcut. İlk işlev testinin gereksinime dayalı kesin kabul kriterleri hâlâ eksik. İşlev testine geçilmedi; gözlemden beklenen değer veya geçti/kaldı kararı türetilmedi.
