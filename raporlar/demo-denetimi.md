# GOREV-002 — demo denetimi

Tarih: 2026-10-13. Beklentiler çalıştırmadan önce [denetim planına](../gereksinimler/GOREV-002-denetim-plani.md) kaydedildi. İlk başarılı testin [kabul kriterleri](../gereksinimler/CANRAT-UI-002.md) ve normal test kodu değiştirilmedi. Kriter SHA-256 değeri hâlâ `7c55db26c7fb8a7f5783231f88f86de73326f58a6d8ad390440d7c03e5593e1c`.

Kanıt kökü: `raporlar/kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16`. Denetimin uygun bulunması, olumsuz senaryodaki ürün testini GECTI yapmaz. GOREV-002 durumunun tek kaynağı [görev kaydıdır](../durum/gorev-durumu.yaml).

## Gerçek uygulamada yapılanlar

Bu bölümdeki komutlar desteklenen komut bazlı onayla Codex tarafından çalıştırıldı. CanRat PID 18480 açık kaldı; EXE değiştirilmedi, uygulama kapatılmadı, Start'a basılmadı ve CAN bağlantısı başlatılmadı.

| Senaryo | Beklenen | Gerçekleşen |
| --- | --- | --- |
| D02 ek salt okunur sorgu | Bulunmayan denetim kimliği reddedilsin; sıfır Toggle | `__GOREV002_MISSING__` kimliği bulunamadı; hata ve çıkış 2; mutation_attempted=false |
| D06 tekrar 1 | GECTI; ilk değere dön | Off → On → Off, GECTI |
| D06 tekrar 2 | Aynı başlangıç ve sonuç | Off → On → Off, GECTI |
| D07 kontrollü kesinti | Yarım koşu başarı sayılmasın; yeni süreç gerçek durumu okuyup ilk değere dönsün | Denetim yardımcısı On gözleminden sonra kendi sürecini çıkış 91 ile sonlandırdı. Yeni Inspect süreci On okudu; günlükte ilk değer Off idi. Recover Off'a döndürdü; bağımsız son Inspect Off okudu |

İki tekrarın ayrı gerçek koşu kayıtları: [tekrar 1](kosular/canrat-ui-002-58fc7e9449e0484dac8693943ff7c154/sonuc.json), [tekrar 2](kosular/canrat-ui-002-a379027880fa4dc7a2a13e69746612b1/sonuc.json). Önceki başarılı koşu da korunmuştur.

Kesinti ve devam kanıtları: [yarım günlük](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/live/interrupted.json), [yeni süreçle okuma komutu](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/live/resume-inspect/command.json), [geri yükleme](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/live/recovery.json), [gerçek denetim özeti](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/live/live-summary.json).

Gerçek UI denetimi 14:11:32–14:11:48 Türkiye saatinde gerçekleşti. Başlangıç, devam ve kurtarmada PID ile süreç başlangıç zamanı eşleşti. Yeni süreç eski kaydı başarı kabul etmedi: kayıttaki Off ile arayüzdeki On farkını okudu, yalnızca izinli kutuyu geri çevirdi. Kesilen koşu `HATA` olarak tutuldu; geri yükleme başarısı eski koşuya GECTI yazmadı. Start'ın ön/son göstergesi Off/Start kaldı.

Bu bir test-alt-süreci kesintisidir; Codex konuşmasının kapatılması, işletim sistemi çökmesi veya elektrik kesintisi denendiği iddia edilmez. Gerçek eksik kimlik sorgusu da mevcut gerekli kontrolün kendiliğinden kaybolduğunu göstermez.

## Sahte adaptörle yapılanlar

[Sahte senaryo özeti](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/mock/mock-summary.json). Gerçek Python yürütücüsü ve PowerShell senaryosu ayrı çalışma klasörlerine aynı özetlerle kopyalandı; yalnız uygulama bağlantısı [sahte adaptör](../tests/audit/sahte_canrat.ps1) ile değiştirildi. Bu adaptör UIA yüklemez, gerçek süreç/pencere sorgulamaz ve CanRat'a girdi göndermez. İç koşu raporları normal yürütücü şemasını kullanır; onları saran manifest ve denetim sonuçları `SAHTE_ADAPTOR_GERCEK_POWERSHELL` olarak etiketlidir. Bu dosyalar gerçek CanRat testi kanıtı olarak sunulmaz.

| Senaryo | Beklenen ürün test sonucu | Gözlenen sonuç / denetim kanıtı |
| --- | --- | --- |
| D01 uygulama açık değil | HATA | HATA, 0 Toggle; kullanıcı uygulamasını kapatmadan yokluk yanıtı sınandı |
| D02 gerekli kutu yok | HATA | HATA, 0 Toggle |
| D03 durum değişmiyor | KALDI | KALDI; 1 Toggle denemesi, tekrar yok; ilk Off durumu yeniden okundu |
| D04 süre aşımı | HATA; sınırlı kurtarma | HATA; 45 saniye bekleyen sahte sağlayıcı alt süreci gerçek 30 saniye sınırında sonlandırıldı; 12 saniye limitli ayrı kurtarma Off'a döndürdü; toplam 31.367 saniye |
| D05 geri yükleme hata veriyor | HATA ve ayrı cleanup_error | HATA; 1 değişiklik + 1 geri yükleme denemesi; restored=false ve ayrı geri yükleme hatası; yalnız sahte kutu On kaldı |
| D12a Indeterminate | HATA | HATA, 0 Toggle |
| D12b Start On/Stop | ATLANDI | ATLANDI, 0 Toggle |

D04'te zaman gerçekten geçti ve işletim sistemi alt süreci gerçekten sonlandırıldı; sahte olan UI sağlayıcısı ve durum yanıtlarıdır. Bu, gerçek CanRat sağlayıcısının takılmasının denendiği anlamına gelmez. D05'te gerçek uygulamanın geri yüklemesi kasıtlı bozulmadı.

D11'de iki başarısız sahte işlem için çıkışlar 7/7 oldu. Kayıtlı deneme sayacı yeni süreçte tekrar okundu; üçüncü çağrı işlem başlatılmadan çıkış 3 ile reddedildi. [Tekrar sınırı kanıtı](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/mock/D11-retry/audit-result.json). Bu sınır denetim çalıştırıcısında uygulanmıştır; Codex'in bütün geliştirme/düzeltme adımlarını yöneten genel bir çalışma zamanı sınırı olduğu iddia edilmez. Normal UI senaryosundaki 1 değişiklik + en fazla 1 geri yükleme çağrısı D03/D05'te ayrıca sayılmıştır.

## Tamamlama kontrolünde bulunan ve düzeltilen sorunlar

İlk [kanıt denetimi](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/evidence-before/evidence-summary.json) üç uygunsuz kaydı kabul etti:

- **Yüksek — eksik sürüm kanıtı:** yalnız raporda mevcut hash girdileri doğrulanıyordu; bir zorunlu script özeti çıkarılınca kabul ediliyordu. Sabit zorunlu dosya kümesi denetimi eklendi.
- **Orta — yarım adım:** `phase=toggle_attempt` olan kopya, diğer alanları eski başarılı kayıttan kaldığı için kabul ediliyordu. `completed`, temizlik, süreç kimliği ve zorunlu adım sırası kontrolleri eklendi.
- **Orta — yanlış görev ilişkisi:** yanlış görev kimliği reddedilmiyordu. Şema/görev/test/koşu/zaman/kaynak ve komut-günlük ilişkisi denetimleri eklendi.

Bunlar otomasyonun kanıt doğrulayıcısı kusurlarıdır; CanRat ürün kusuru olarak kaydedilmedi. Başarılı testin beklenen sonucu veya kabul kriteri değiştirilmedi. [demo_dogrula.py](../araclar/demo_dogrula.py) düzeltildi; ilk hatalı denetim kanıtları korundu.

Son [kanıt denetiminde](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/evidence-final/evidence-summary.json) geçerli kopya kabul edildi; eksik rapor, eksik günlük, eksik zorunlu alan, eksik hash, eski hash, yarım adım ve yanlış görev kimliği ayrı ayrı reddedildi. Bunlar açıkça etiketli yapay kanıt kopyalarıdır; asıl başarılı rapor değiştirilmedi.

D10'da ayrı dosya ağacında görev yolu `gorevler/MISSING.md` yapıldı; [kontrol çıkış 2 ile reddetti](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/D10-document/audit-result.json). Yeni GOREV-002 tamamlama kontrolü de [eksik kanıt ve eski plan kopyalarını](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/gate-negative/summary.json) çıkış 2 ile reddetti. Görev durumu dosyası bu olumsuz denemelerde değiştirilmedi.

## Çalıştırma ve doğrulama

Çalıştırılan aşamalar `tests/audit/denetim.py --stage new|mock|evidence|broken-document|live` ile ayrıdır. Her aşamanın komut, süre, stdout/stderr ve çıkış kayıtları kendi kanıt alt klasöründedir. Yeniden denetimde `--stage new` ile yeni kök oluşturulmalı; eski klasörlerin üzerine çalıştırılmamalıdır.

Tam denetim doğrulaması:

```powershell
py -3 araclar/denetim_dogrula.py --folder raporlar/kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16
```

Kontrol, sahte denetimlerin ham koşularını, gerçek tekrarların sürüm/sonuç kanıtlarını, kesinti ve bağımsız okuma/kurtarma günlüklerini, bozuk kanıt reddini ve mevcut kod/kriter özetlerini inceler. Eksik/açık sorun olduğunda exit 2 verir. UI etkileşimi yapmaz; görev durumunu otomatik değiştirmez. [Son tamamlama kontrolü](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/tamamlama-son.json).

`py -3 -m unittest discover -s tests/unit -v` tekrar çalıştırıldı: 16/16 başarılı. [Birim test çıktısı](kosular/denetim-53c20a7efe0a4e6a98f8bed3e29ddb16/birim-kontrolleri.txt). Birim testleri gerçek UI kanıtı yerine sayılmadı.

## Açık sınırlar ve ana servise geçiş

Bu denetimin planlanan kabul ölçütlerinde açık kalan yok; gerçek kutu Off'a döndü. Ancak ana servise geçmeden önce aşağıdakiler yeni görevlerle ele alınmalı:

1. Gerçek uygulamanın kapanması, sağlayıcı kilitlenmesi ve temizleme hatası yalnızca ayrılmış, otomasyonun sahip olduğu test ortamında sınanmalı. Bu oturumdaki kullanıcı uygulaması bu amaçla kapatılmadı veya bozulmadı.
2. Ani güç kaybı veya denetim üst sürecinin de ölmesi durumunda otomatik geri dönüş garanti değildir. Mevcut PID/başlangıç zamanı ve gerçek durum okunmadan eski işlemler tekrar edilmemeli; otomatik oturum açılışı servisi kurulmadı.
3. Mutex otomasyon koşularını sınırlar; kullanıcı tıklamasını engellemez. Paralel insan etkileşimi ve farklı sürüm/pencere düzeni ayrıca değerlendirilmelidir.
4. Kanıt dosyaları ve doğrulayıcı aynı yazılabilir projededir. Bu denetim yanlış/eksik kaydı yakalar; kötü niyetli bütün dosyaları değiştirmeye karşı bağımsız imza veya güvenlik sınırı sağlamaz.
5. Ana servis için gerçek gereksinim kaynakları, cihaz/tenant hedefi, donanım ön koşulları, güvenli geri dönüş ve işlem bazlı izinler tanımlanmalıdır. CAN bağlantısı, cihaz davranışı, veri kaydı ve flash işlemlerinin doğruluğu bu demoyla kanıtlanmış değildir.
