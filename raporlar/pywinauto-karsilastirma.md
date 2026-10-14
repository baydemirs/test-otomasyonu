# GOREV-006 — pywinauto karşılaştırması

2026-10-14. Kabul ölçütleri koşudan önce [görev dosyasına](../gorevler/GOREV-006-pywinauto-karsilastirma.md) yazıldı; [CANRAT-UI-002](../gereksinimler/CANRAT-UI-002.md) değiştirilmedi. Uygulamaya erişen eski PowerShell/UIA dosyaları değiştirilmedi. Kullanılan EXE SHA-256: `0b9bd8141cf4d78e9232a0d4747786692778e44868ffdfe2d7037f2d0902540d`.

## Python ve paket uyumluluğu

Proje Python'u **3.14.4, 64-bit**. Resmî [PyPI sürüm kaydı](https://pypi.org/project/pywinauto/) pywinauto 0.6.9 için evrensel Python wheel sunar, ancak 3.14'ü açık sınıflandırıcı olarak listelemez. Bu yüzden metadata değil, [yerel import/API kaydı](kosular/pywinauto-f0df9212aa884318b759563d910fe261/uyumluluk.json) ve aşağıdaki gerçek Windows koşuları uyumluluk kanıtıdır. `.venv` içinde pywinauto **0.6.9**, comtypes **1.4.17**, pywin32 **312**, six **1.17.0** kuruldu. Pytest **9.1.1** korunur. Kurulum [sabit bağımlılık dosyasıyla](../requirements-pywinauto.txt) tekrarlanır.

## Gerçek CanRat sonuçları

| Yöntem / başlangıç | Beklenen | Gözlenen |
| --- | --- | --- |
| Pywinauto, mevcut tek süreç | Start Off/Start, hedef Off → On → Off, aynı PID açık | [Pytest PASS ve JSON bağlantısı](kosular/pytest-gecis-6b8e9964c1234f1598af7d622a6cee6f/pywinauto-acik/pytest-link.json): PID **8768**, başlangıç ticks `639275574475923827`, MEVCUDA_BAGLANILDI / GECTI / ACIK_BIRAKILDI. |
| PowerShell/UIA, aynı süreç | Aynı kriter, aynı PID açık | [Pytest PASS ve JSON bağlantısı](kosular/pytest-gecis-6b8e9964c1234f1598af7d622a6cee6f/powershell-acik/pytest-link.json): aynı PID/ticks, Off → On → Off, ACIK_BIRAKILDI. `--canrat-adapter` verilmedi; varsayılan yöntem kullanıldı. |
| Pywinauto, kapalı başlangıç | Doğru EXE başlatılsın, Off → On → Off, yalnız owned süreç normal kapansın | [Pytest PASS ve JSON bağlantısı](kosular/pytest-gecis-6b8e9964c1234f1598af7d622a6cee6f/pywinauto-kapali-gecerli/pytest-link.json): PID **3308**, BASLATILDI / GECTI / KAPANDI, CloseMainWindow, son süreç listesi boş. |

Her bağlantı kaydı pytest XML, yaşam döngüsü `sonuc.json`/günlüğü ve iç CANRAT-UI-002 `sonuc.json`/UIA günlüğüne gider. Aynı açık süreçte iki adaptörün [test sonrası PID denetimi](kosular/pywinauto-f0df9212aa884318b759563d910fe261/acik-son-kontrol.json) başarılıdır. Bu örnek karşılaştırma için otomasyon tarafından hazırlanmıştı; iki test açık bıraktıktan ve kanıt kaydedildikten sonra yalnız hazırlık örneği [normal kapatıldı](kosular/pywinauto-f0df9212aa884318b759563d910fe261/tespit-hazirlik-temizlik.json). Kullanıcıya ait süreç kapatılmadı. Tek koşuların süreleri ölçüldü ama performans kıyası için örnek sayısı yetersizdir.

## Kontrol bulunamaması ve hata kaydı

İlk gerçek pywinauto koşusu [FAIL/HATA](kosular/pytest-gecis-6b8e9964c1234f1598af7d622a6cee6f/pywinauto-kapali/pytest-link.json) üretti. Start kontrolü bulundu fakat yanlış `Button` türü beklendiği için kutuya dokunulmadı (`mutation_attempted=false`); owned süreç normal kapandı. [Salt okunur gerçek UI incelemesi](kosular/pywinauto-f0df9212aa884318b759563d910fe261/tip-inceleme.json), Qt `QPushButton` sınıfının UIA'da `CheckBox` türü ve Off ToggleState ile sunulduğunu gösterdi. Adaptör eşlemesi bu kanıta göre düzeltildi; ilk başarısız kayıt korunur. Bu hata otomasyon kaynaklıdır, hedef uygulama kusuru diye sınıflandırılmadı.

Eksik kontrol, yinelenen kimlik, yanlış tür, pasif olmayan kutu, belirsiz ToggleState ve hata/geri yükleme sonucunun HATA kalması [sahte kontrol nesneleriyle](kosular/pywinauto-f0df9212aa884318b759563d910fe261/sahte-kontroller.json) sınanır. Bu kontroller gerçek CanRat'ta kontrol silinmiş veya geri yükleme arızası yaşanmış gibi sunulmaz.

[Birleşik karşılaştırma denetimi](kosular/pywinauto-f0df9212aa884318b759563d910fe261/karsilastirma-dogrulama.json), iki yöntemin aynı PID ve başlangıç zamanında geçtiğini, pywinauto'nun kapalı dalını, ilk gerçek HATA kaydını ve sahte kontrolleri ayrı doğruladı. [Mevcut unittest kayıtlarında](kosular/pywinauto-f0df9212aa884318b759563d910fe261/birim-kontrolleri.json) 43 test geçti; [varsayılan pytest](kosular/pywinauto-f0df9212aa884318b759563d910fe261/varsayilan-pytest.json) 43 geçti ve tek masaüstü testi atladı. [Paket denetimi](kosular/pywinauto-f0df9212aa884318b759563d910fe261/pip-check.json) kırık gereksinim bulmadı; [kurulu paketler](kosular/pywinauto-f0df9212aa884318b759563d910fe261/pip-freeze.json) sürümleri gösterir. [Eski kayıt ve kaynak karşılaştırmasında](kosular/pywinauto-f0df9212aa884318b759563d910fe261/eski-kayit-karsilastirma.json) **344 eski koşu dosyası değişmedi**. Dört mevcut PowerShell/UIA dosyası, orijinal CANRAT-UI-002 Python test yürütücüsü ve kabul kriteri aynı SHA-256 değerindedir; yalnız ortak Python yaşam döngüsü yürütücüsü adaptör seçimi için genişledi.

## Kod ve davranış karşılaştırması

Pywinauto UI testinde `AutomationElement.FromHandle`, `PropertyCondition/FindAll`, `GetCurrentPattern(TogglePattern)` ve doğrudan .NET `Add-Type` çağrılarını `Desktop(...).windows()`, `descendants()`, `get_toggle_state()` ve `toggle()` ile ifade eder. Bu API'ler [pywinauto'nun UIA kontrol belgelerinde](https://pywinauto.readthedocs.io/en/latest/code/pywinauto.controls.uia_controls.html) tanımlıdır; gerçek 0.6.9 denemesinde de çalıştı. Süreç kimliği, mutex, başlangıç/ara/son kararlılık okumaları, günlük ve hata halinde geri yükleme hâlâ özel kod gerektirir. Yaşam döngüsü kapanış koruması, her iki yolda değişmeyen PowerShell/UIA Start okumasını kullanır; bu deneme UI testinin erişim yöntemini karşılaştırır. Eski sarmalayıcıyı korumak için yeni bir yaşam döngüsü sarmalayıcısı eklendi; toplam kod yüzeyi bu denemede azalmadı.

Pywinauto yolu `.venv` ortamına pywinauto ile üç dolaylı bağımlılık getirir; eski PowerShell/UIA yolu bu paketleri gerektirmez. Yeni yolun sert alt süreç zaman aşımından sonra, eski CANRAT-UI-002 Python yürütücüsündeki ayrı 12 saniyelik `Recover` denemesinin eşdeğeri henüz yoktur. Normal hata yolunda `finally` ile geri yükleme denenir ve başarısızlık HATA olur; ani süreç kesintisi ve takılan COM çağrısından güvenilir kurtarma bu denemede doğrulanmadı. Bu fark, varsayılan yöntemi değiştirmeme kararını destekler.
