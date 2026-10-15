# GOREV-004 — Teslim hazırlığı ve temiz klon doğrulaması

## Kapsam ve bağımlılık

Kaynak: Kullanıcının 2026-10-15 talimatı. Bağımlılık: GOREV-008.
Projenin başka bir ortamda / mentör tarafından sorunsuz kurulup çalıştırılabilmesi için teslim bileşenleri (Git deposu, harici hedef uygulama paketi, yerel kanıtlar) ayrıştırılır; birim testleri ve yapısal kontroller geçmiş yerel ham kayıtlardan bağımsızlaştırılır; temiz bir kopyada kurulum ve varsayılan testler doğrulanır. Yeni özellik veya senaryo eklenmez.

## Kabul kriterleri

1. **Bağımsız Birim Testleri:** `tests/unit/test_yasam_kaniti.py` dosyasındaki sabit geçmiş koşu dosyalarına bağımlılık, sentetik fixture verilerine dönüştürülür. Tüm 10 kontrolün (sahiplik, çoklu süreç, PID yeniden kullanımı, kapatma isteği, çalışma dizini, temizlik hatası, süreç kalıntısı, alt süreç kimliği, eksik günlük) anlamsal içeriği korunur. Temiz bir kopyada hiçbir geçmiş ham kanıt dosyası olmadan `pytest -q` çalıştırıldığında tüm birim testleri eksiksiz geçer.
2. **Yapısal Görev Doğrulayıcı:** `otomasyon/dogrulama/demo_dogrula.py` betiğine `--structure-only` modu eklenir. Bu mod görev kimliklerini, görev dosyalarını, döngüleri ve bağımlılıkları denetler; geçmiş kanıtların içeriğinin ve dosya varlığının bu modda doğrulanmadığını açıkça bildirir. Mevcut `--tasks-only` modunun dosya varlığını şart koşan varsayılan davranışı aynen korunur.
3. **Tek Koşu Doğrulamasının Ayrılması:** `demo_dogrula.check()` tek koşu doğrulaması, proje geçmişinin (`validate_tasks()` ve geçmiş belge bağlantıları) denetiminden ayrılır. Yeni koşunun kaynak sürümü, kabul kriteri, süreç kimliği, adımları, günlükleri ve sonuç tutarlılığı kontrolleri eksiksiz korunur.
4. **Bağımsız Koşu Doğrulama Regresyon Testleri:** `tests/unit/test_kosu_dogrula.py` (7 birim testi) ile geçmiş kayıtlar olmadan geçerli yeni koşunun doğrulanabildiği; yeni koşunun kendi kanıtı eksik/bozuk olduğunda reddedildiği sınanır. Toplam birim test sayısı 67'ye ulaşır.
5. **Merkezi Kurulum ve Kullanım Rehberi (README):** README ana kurulum ve kullanım rehberi olarak güncellenir; kurulum, yapısal doğrulama, uçtan uca masaüstü koşusu ve HTML raporu komutlarını tek merkezde toplar.
6. **Teslim Bileşenleri Belgesi (`belgeler/teslim-bilesenleri.md`):** Teslim bileşenlerini (Git deposu, harici paket, yerel kanıtlar), kapsam sınırlarını ve tarihsel kanıtların ilgili kaynak sürümleriyle değerlendirilmesi gerektiğini açıklar; README'deki komutları kopyalamaz.
7. **Temiz Kopyada Doğrulama ve Gerçek Masaüstü Akışı:** Geçici bir çalışma alanında mevcut `.venv` ve geçmiş `raporlar/kosular` kayıtları olmadan yeni sanal ortam kurulur, hedef uygulama sağlanır; `pytest -q` birim testleri geçer ve masaüstü testi atlanır. `Closed` başlangıç modunda README'deki komut akışı (pytest masaüstü testi, `pytest-komut.json`, `pytest_dogrula.py` ve `html_rapor.py`) uçtan uca çalıştırılarak doğrulanır.
8. **Sınırlar ve Korumalar:** Kaynak kod Git'te, hedef uygulama harici pakette, geçmiş kanıtlar yerelde kalır. Geçmiş kanıt arşivi üretilmez/yayımlanmaz. Start'a basılmaz, CAN başlatılmaz, kullanıcının açık süreci kapatılmaz. Push yapılmaz.
