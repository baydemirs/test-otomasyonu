# Mimari Kararlar

## Karar 1 Tek proje ve tek geliştirme ajanı

Talimatlar, test kodu, görevler ve rapor kayıtları tek proje altında tutulur. İlk geliştirme oturumlarında Codex kullanıldı; proje devri belirli bir LLM'e bağlı değildir. Aynı proje üzerinde tek geliştirme ajanı çalışır. Ayrı bir ajan uygulaması veya otomatik LLM geçişi uygulanmadı. Gerekçe: Küçük demo için ek yürütme altyapısı gerektirmeden çalışma düzenini sınayabilmek.

## Karar 2 Uygulamaya özgü kodun ayrılması

Test senaryosu neyin doğrulanacağını, uygulama bağlantı katmanı işlemin hedef uygulamada nasıl yapılacağını tanımlayacak. Ana servise geçerken bağlantı kodu ve ilgili senaryolar değişebilir. Test çalıştırma ve raporlama düzenini yeniden kullanmak hedeflenir, tamamen değişikliksiz geçiş garanti edilmez.

## Karar 3 Kriterler testten önce belirlenir

Geliştirici ve mentör doğru davranışı belirler; görevi üstlenen geliştirme ajanı bu davranışı test eden kodu yazar. Uygulama kusurunun doğru tespiti, testin kalmasıyla birlikte otomasyonun doğru çalıştığını gösterebilir. Bu nedenle test sonucu ile geliştirme görevinin durumu ayrı tutulur.

## Karar 4 Denetim aşamalı kurulacak

İlk paket rehber ve kayıtla başladı. Demo geliştirmede belge yolları, zorunlu görev alanları, test sonuçları ve kanıt varlığı için kontrol komutu eklendi. Tamamlanma kararı, bu kontrolün sonucu ve kanıt incelemesiyle verilir. Geliştirme ajanı kontrol kodunu da değiştirebiliyorsa bu komut tek başına bir güvenlik sınırı değildir. Daha güçlü ayrım gerekirse geliştirici incelemesi ve ayrı bir doğrulama ortamı eklenir.

## Karar 5 Belge erişimi ve RAG genişlemesi

İlgili gereksinimler başlangıçta kimlik ve kaynak konumuyla bulunacak. Her kaynağın sürümü ve dosya özeti tutulacak. Farklı belgelerde ilişkili bilgiyi bulmak zorlaşırsa RAG bu erişim adımına eklenecek; test yürütücüsü RAG sonucuna çalışma anında bağımlı olmayacak. RAG çıktısı taslaktır, kabul kriteri olarak kullanılmadan kaynakla kontrol edilir. Gereksinim kimliği, belge özeti, bölüm, adım, şekil/tablo ilişkisi korunur. Arama kalitesi bilinen sorular ve beklenen kaynaklarla ölçülür. RAG görev sırasını veya doğrulama kurallarını tek başına uygulamaz.

## CanRat uygulama kararı

2026-10-13: CANRAT-UI-002 için ek GUI paketi kurmadan mevcut Python standart kütüphanesi + PowerShell/.NET UIA seçildi. Gerekçe: aynı sürümde kontrol ve TogglePattern erişimi gerçek koşuyla kanıtlandı; yalnızca bir kutu hedefleniyor. Uygulamaya özgü UI sorgu ve Toggle işlemleri `otomasyon/baglanti/canrat_toggle.ps1`, senaryo/geri yükleme `otomasyon/yurutme/canrat_ui_002.ps1`, süreç sınırı ve sonuç sınıflandırması `otomasyon/yurutme/canrat_ui_002.py` içindedir. Bu seçim başka uygulamalar için genel uyumluluk iddiası değildir.

İlk envanter aracı Python standart kütüphanesi ve Windows UI Automation kullanır; ek Python paketi gerektirmez. JSON inceleme çıktısı seçildi. Aktif test kütüphanesi pytest, varsayılan uygulama erişimi PowerShell/UIA ve tek güncel görev kaydı `durum/gorev-durumu.yaml` dosyasıdır.

## Karar 6 Genişletilebilir ortak kayıtlar

Gerçek test kataloğunda test kimliği, gereksinim kimliği, kaynak sürümü/konumu, hedef uygulama/cihaz, ön koşullar, test verileri, adımlar, karşılaştırma ölçütü, zaman sınırı ve temizlik tanımlanacak. Sonuç; koşu kimliği, uygulama ve otomasyon sürümü, gerçek ölçüm, beklenen değer, sonuç ve kanıtı taşıyacak. Gelecekteki şemalar sürümlenecek; eski kayıtlar sessizce dönüştürülmeyecek.

Sorumluluklar: gereksinim kataloğu neyin doğru olduğunu; uygulama adaptörü işlemin nasıl yapılacağını; test yürütücüsü hazırlık/süre/temizliği; doğrulama kodu karşılaştırmayı; raporlama kanıtları yönetir. CanRat'ın sahip olmadığı ECU sıcaklığı gibi özellikler ortak adaptöre zorla eklenmez. İhtiyaç ortaya çıktıkça küçük arayüzler tanımlanır.

## Karar 7 Ek ajanların yeri

Tek geliştirme ajanıyla çalışılır; aynı proje üzerinde iki geliştirme ajanı eşzamanlı işlem yapmaz. Ayrı denetçi eklenirse görev tanımı, değişiklik listesi ve aynı sürüme ait kanıtları alır; bulgu üretir. Test kriterlerini veya başarı kararını tek başına değiştirmez. Ek ajan gereksinimi, inceleme kalitesine katkı ve zaman/maliyet üzerinden değerlendirilir. Paylaşılan donanım kullanan testler, kaynak paylaşım kontrolü olmadan paralel çalıştırılmaz.

## Karar 8 Ortam ve fiziksel adımlar

Donanımsız inceleme, simülasyon, gerçek donanım ve insan katılımlı testler ayrı etiketlenecek. Birinin başarısı diğerinin yerine geçmez. Flash, kalibrasyon ve kayıt silme görevlerinde hedef cihaz, uygun dosya, başlangıç durumu ve kurtarma/temizlik planı testten önce tanımlanır. Yarıda kalmış yazma işlemi kendiliğinden tekrar başlatılmaz; cihazın gerçek durumu incelenir. Dosya/kodla denetlenebilir kurallar otomatikleştirilir; geliştirme ajanının değiştirebildiği kontrol kodu bağımsız bir güvenlik sınırı sayılmaz.

## Karar 9 CanRat süreç sahipliği

2026-10-13 kullanıcı talimatıyla yaşam döngüsü ayrı katman olarak eklendi. `otomasyon/yurutme/canrat_yasam.py` süre/kanıt sınırını, `otomasyon/yurutme/canrat_yasam.ps1` başlatma-test-kapatma akışını, `otomasyon/baglanti/canrat_yasam.ps1` süreç kimliği/pencere/normal kapatmayı yönetir. Mevcut CANRAT-UI-002 kodu ve kriterleri değişmez. Yeni servis veya sürekli dinleyen yerel çalıştırıcı kurulmaz; mevcut komut bazlı onay yöntemi kullanılır.

Sahiplik yalnız başarılı başlatma ile edinilir; her işlem PID + UTC başlangıç zamanı + EXE yolu ile doğrulanır. Önceden açık süreç kapanmaz. Aynı oturumdaki yaşam döngüsü koşuları mutex ile seri çalışır; kapatma sırasında mevcut UI testi mutex'i de alınır. Bu kilitler kullanıcı müdahalesini veya kilide uymayan başka programları engelleyen bir güvenlik sınırı değildir. Zaman aşımında zorla uygulama sonlandırma yapılmaz; kesinti/temizlik hataları başarı olarak sınıflandırılmaz.

## Karar 10 Pytest geçişinin sınırı

2026-10-14 GOREV-005 kapsamında eklenen tek masaüstü pytest testi aktif yürütme yoludur. Pytest proje `.venv` ortamında sürüme sabitlenir; yaşam döngüsü/PowerShell/UIA kodu kullanılır. `--run-desktop` yoksa masaüstü testi atlanır. Pytest XML sonucu ve uygulama JSON kanıtları ayrı kayıtlar olarak bağlanır ve doğrulanır. Toplu masaüstü testleri mevcut kapsamda değildir; tekil koşular için bağımsız HTML rapor üretimi GOREV-008 ile desteklenmektedir.

## Karar 11 Alternatif pywinauto yolu

2026-10-14 GOREV-006, pywinauto 0.6.9 ile gerçek CanRat üzerinde tamamlanan karşılaştırma denemesidir. Sonuçlar [karşılaştırma raporunda](../raporlar/pywinauto-karsilastirma.md), deneme kodu ve sürüm bilgisi `otomasyon/arsiv/pywinauto/` altındadır. Aktif pytest testinde adaptör seçimi yoktur; PowerShell/UIA tek varsayılan yoldur. Tarihsel koşu kanıtları değiştirilmez. Karşılaştırmanın sınırı tek kontrol ve tek gerçek CanRat sürümüdür; sonuç başka Qt/Windows sürümlerine otomatik genellenmez.

## Karar 12 Gelecek ihtiyaç: Ortam hazırlığı, bağımlılık ve temizlik akışı

Ana servis yazılımında bazı senaryolar ortam hazırlığına veya başka testlerin sonuçlarına bağlı olabilir. Gerçek gereksinimler geldiğinde hazırlık, bağımlılık ve temizlik akışı tasarlanacaktır. Şimdilik bu işlevler geliştirilmez ve varsayımsal örnek senaryo üretilmez.

