# GOREV-005 — Pytest geçiş denemesi

2026-10-14. Önceden belirlenen ölçütler [görev dosyasındadır](../gorevler/GOREV-005-pytest-gecis-denemesi.md). GOREV-004 teslim işi olarak ayrılmıştır. Hedef uygulama ve mevcut PowerShell/UIA dosyaları değiştirilmedi. Proje `.venv` ortamında pytest `9.1.1` kuruldu; [kurulu sürüm listesi](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/venv-surum.json) kaydedildi. Bağımlılık [sürüme sabitlenmiştir](../requirements-pytest.txt).

## Gerçek Windows koşuları

| Başlangıç | Beklenen | Gerçek sonuç |
| --- | --- | --- |
| Kapalı | Doğru EXE açılsın, Off → On → Off, normal kapansın | Pytest 1 passed; PID 5764, `BASLATILDI / GECTI / KAPANDI`; son süreç listesi boş. |
| Açık | Mevcut örneğe bağlansın, Off → On → Off, açık kalsın | Pytest 1 passed; PID 17252, `MEVCUDA_BAGLANILDI / GECTI / ACIK_BIRAKILDI`; pytest sonrası aynı PID/başlangıç zamanı penceresi açık. |

Kapalı koşunun [pytest XML](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/kapali-3/pytest.xml), [JSON bağlantısı](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/kapali-3/pytest-link.json) ve [komutu](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/kapali-3/pytest-komut.json) ayrı kaydedildi. Bağlantı kaydı yaşam döngüsü ve iç CANRAT-UI-002 `sonuc.json`/günlük yollarını, aşama sonuçlarını, PID/başlangıç zamanını ve kaynak özetlerini içerir.

Açık koşunun [pytest XML](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/acik/pytest.xml), [JSON bağlantısı](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/acik/pytest-link.json), [komutu](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/acik/pytest-komut.json) ve [pytest sonrası açık kalma kanıtı](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/acik-son-kontrol.json) vardır. Bu örnek otomasyonun gerçek dalı için ayrı bir hazırlık adımıyla açılmıştır; pytest onu kapatmamıştır. Kanıt alındıktan sonra yalnız hazırlık sürecinin PID/başlangıç zamanı ve Off/Start göstergesi yeniden doğrulanıp [normal kapatma kaydı](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/acik-hazirlik-temizlik.json) oluşturulmuştur. Bu hazırlık kapatması pytest sonucuna dahil değildir.

## Otomasyon ve hata davranışı

[Birim testleri](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/birim-testleri.json): mevcut unittest komutunda 37 geçti. [Varsayılan pytest](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/varsayilan-pytest.json): 37 geçti, 1 masaüstü testi atlandı; CanRat işlemi başlatılmadı. Gerçek koşularda yalnız bir pytest masaüstü testi yürütüldü; Start'a basılmadı veya CAN bağlantısı başlatılmadı.

Test; yaşam döngüsü çıkış kodu, başarılı `sonuc.json`, adım günlüğü, iç test günlüğü, Off → On → Off ve geri yüklemeyi birlikte doğrulamadan PASS üretmez. Başlatma/temizlik hataları GOREV-003 kaydında HATA olur ve pytest FAIL üretir. [Birleşik kanıt doğrulayıcısı](../araclar/pytest_dogrula.py) iki pytest XML sonucunu ilişkilendirilmiş güncel JSON'larla ayrıca karşılaştırır.

İlk iki pytest denemesi, yeni kanıt klasörü önceden oluşturulmadığından uygulamaya ulaşmadan FAIL verdi; bu JUnit kayıtları `kapali` ve `kapali-2` klasörlerinde bırakıldı. `kapali-3` yeni koşusunda klasör oluşturularak gerçek test geçti. Eski raporlar düzeltilmedi. Bu, uygulama kusuru değildir.

[Son kanıt kontrolü](kosular/pytest-gecis-2195a95bf53b4746a3e3aee13c18444c/tamamlama-on-kontrol.json) iki gerçek dalın pytest/XML/JSON bağını ve beş görevli kayıt düzenini doğruladı. Varsayılan pytest yine 37 geçti, 1 masaüstü testi atlandı. Deneme öncesi özetlenen **311 eski koşu dosyasından hiçbiri değişmedi**. Sanal ortam yapılandırmasında `include-system-site-packages = false`; pytest genel Python ortamından miras alınmadı.

Kapsam sınırı: gerçek CAN donanımı ve veri toplama doğrulanmadı; HTML rapor ve toplu test bağımlılıkları sonraki görevdedir.
