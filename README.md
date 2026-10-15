# CanRat masaüstü test otomasyonu

Bu proje, CanRat'ın tek bir arayüz kontrolünü (`MainWindow.centralwidget.cboxAppendRecieved`) Windows masaüstünde denetler. Test ilk ToggleState değerini okur, karşıt durumu doğrular ve başlangıca geri döner. Start'a basmaz, CAN bağlantısı başlatmaz. Beklenen davranış [CANRAT-UI-002](gereksinimler/CANRAT-UI-002.md) dosyasındadır.

## Teknolojiler

Python 3 ve **pytest** testleri yürütür. Windows PowerShell ile .NET UI Automation, CanRat kontrollerini okur ve izinli kutuyu değiştirir. Python yaşam döngüsü kodu süre sınırını ve kanıt kaydını; PowerShell yaşam döngüsü kodu PID, başlangıç zamanı, süreç sahipliği ve normal kapatmayı yönetir. Pywinauto, [karşılaştırması](raporlar/pywinauto-karsilastirma.md) tamamlanmış arşiv denemesidir; aktif çalıştırmada kullanılmaz.

## Kurulum ve çalıştırma

Windows'ta proje kökünden çalıştırın. Hedef `hedef_uygulama/CANRAT_3min/CANRat.exe` ve yanındaki DLL dosyaları bulunmalıdır. Başka bir CanRat kopyası seçilmez. Python 3 ve Windows PowerShell gerekir.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-pytest.txt
.\.venv\Scripts\python.exe -m pytest -q

# Temiz klonda (geçmiş ham kanıtlar olmadan) görev yapısı ve bağımlılık kontrolü:
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --structure-only

# Yerel geliştirme ortamında geçmiş kanıt dosyalarının varlığıyla birlikte tam kontrol:
.\.venv\Scripts\python.exe otomasyon/dogrulama/demo_dogrula.py --tasks-only
```

Teslim bileşenleri, paketleme modeli ve sınırlar hakkında ayrıntılı bilgi [Teslim Bileşenleri](belgeler/teslim-bilesenleri.md) belgesindedir.

Varsayılan `pytest -q` yalnız birim kontrollerini çalıştırır; masaüstü testini atlar. Gerçek masaüstü testi, uygulamanın açık veya kapalı olduğunu önce doğrulayarak **ayrıca** çalıştırılır. `Existing`, kullanıcının açık örneğine bağlanır ve açık bırakır; `Closed`, yalnız kendi açtığı örneği normal yoldan kapatır. Birden fazla örnek hata kabul edilir. Örnek kapalı başlangıç komutu:

```powershell
$run = "raporlar/kosular/pytest-gecis-$([guid]::NewGuid().ToString('N'))/kapali"
New-Item -ItemType Directory -Path $run -Force | Out-Null
$python = (Resolve-Path .\.venv\Scripts\python.exe).ProviderPath
$argv = @($python, '-m', 'pytest', '-q', 'tests/desktop/test_canrat_ui_002_pytest.py', '--run-desktop', '--canrat-initial', 'Closed', '--evidence-dir', $run, '--junitxml', "$run/pytest.xml")
& $python @($argv[1..($argv.Count-1)])
$code = $LASTEXITCODE
$json = @{ argv = $argv; exit_code = $code } | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText((Join-Path (Resolve-Path $run).ProviderPath 'pytest-komut.json'), $json, (New-Object Text.UTF8Encoding($false)))
if ($code -ne 0) { throw "Pytest başarısız: $code" }
.\.venv\Scripts\python.exe otomasyon/dogrulama/pytest_dogrula.py --folder $run --expected Closed
```

Açık tek örneğe bağlanmak için ayrı boş klasör ve `--canrat-initial Existing` kullanın. Masaüstü erişimi için komut, uygulamayla aynı etkileşimli Windows oturumunda ve mevcut onaylı komut yöntemiyle çalışmalıdır. Envanter adımları [Windows ilk adım](belgeler/windows-ilk-adim.md) belgesindedir.

## Klasör haritası

| Klasör | Amaç |
| --- | --- |
| `otomasyon/baglanti/` | CanRat'a özgü PowerShell/UIA erişimi ve süreç işlevleri |
| `otomasyon/yurutme/` | Tek kontrol testi, yaşam döngüsü ve kurtarma |
| `otomasyon/inceleme/` | Salt okunur arayüz envanteri ve erişim tanısı |
| `otomasyon/dogrulama/` | Görev kaydı ve JSON/pytest kanıt denetimi; ortak dosya yardımcıları |
| `otomasyon/arsiv/pywinauto/` | Tamamlanmış karşılaştırmanın kodu ve sürüm kaydı |
| `tests/unit/`, `tests/desktop/`, `tests/audit/` | Birim, açıkça seçilen masaüstü ve denetim senaryoları |
| `gereksinimler/` | Test adımları ve kabul kriterleri |
| `belgeler/` | Mimari, çalışma kuralları ve kullanım bilgisi |
| `gorevler/`, `durum/` | Görev tanımları ve [tek güncel durum kaydı](durum/gorev-durumu.yaml) |
| `raporlar/` | Sonuç özetleri; ham `kosular/` kanıtları yerel alanda kalır ve herkese açık depoya eklenmez |
| `hedef_uygulama/` | Hedef EXE ve çalışması için gerekli DLL dosyaları |

## Sonuçları okuma ve kapsam

Masaüstü koşusunda `<run>/pytest.xml` pytest sonucudur; `<run>/pytest-link.json` aynı koşunun yaşam döngüsü `sonuc.json` ve UI `sonuc.json` yollarını içerir. Yalnız pytest çıkış kodu başarı kanıtı değildir; `otomasyon/dogrulama/pytest_dogrula.py` bağlı JSON'ları, süreç sahipliğini ve Off → On → Off durumlarını denetler. Eski koşu kayıtları tarihsel kanıttır; taşınan kaynakların güncel sürümüne ait kanıt sayılmaz.

Koşuya ait okunabilir, bağımsız HTML raporu üretmek ve açmak için:

```powershell
.\.venv\Scripts\python.exe otomasyon/dogrulama/html_rapor.py --folder $run
Start-Process "$run/rapor.html"
```

Herkese açık kaynak deposu ham `raporlar/kosular/` kayıtlarını içermez. Geçmiş görev kanıtlarının doğrulanması için yerel çalışma alanı gerekir; yeni klonda eksik kanıtı başarılı doğrulama saymayın.

Şimdiki kapsam tek kutu testidir. CAN haberleşmesi, Start işlemi ve toplu test bağımlılıkları desteklenmez. Tekil koşular için yerel HTML raporu desteklenir. `.venv` ve önbellekler yerel ortamda kalır; kaynak/teslim kapsamı dışındadır.

