# GOREV-008 — HTML test raporu oluşturma

## Kapsam ve bağımlılık

Kaynak: Kullanıcının 2026-10-14 talimatı. Bağımlılık: GOREV-007.
CANRAT-UI-002 senaryosunun tamamlanmış pytest ve JSON/XML koşu kanıtlarından yerel, bağımsız ve okunabilir tek bir HTML rapor üretilir. Yeni masaüstü testi çalıştırılmaz; mevcut kanıtlar değiştirilmez.

## Kabul kriterleri

1. Rapor oluşturucu (`otomasyon/dogrulama/html_rapor.py`), verilen pytest koşu klasöründeki (`raporlar/kosular/pytest-gecis-*/<dal>`) mevcut `pytest-link.json`, `pytest.xml`, yaşam döngüsü ve UI `sonuc.json` kayıtlarını okur. Testi yeniden çalıştırmaz.
2. Üretilen HTML raporu şunları açıkça gösterir:
   - Test kimliği (`CANRAT-UI-002`), koşu kimliği (`run_id`), zaman damgası (UTC/yerel) ve başlangıç modu (`Existing` veya `Closed`).
   - Kayıtlı test sonucu (`GECTI`, `KALDI`, `HATA` veya `ATLANDI`) ile kanıt doğrulama durumu (`DOGRULANDI` / `DOGRULANAMADI`) birbirinden ayrı gösterilir.
   - Beklenen ve gerçekleşen başlangıç, değişiklik ve geri dönüş değerleri (`initial`, `changed`, `final`).
   - Start butonunun durumu (boşta/pasif kontrolü), başlangıç durumuna dönüş (`restored`) ve süreç temizliği/kapanış durumu.
   - Koşu süresi ve varsa hata/açıklama metni.
   - İlgili kaynak JSON/XML kanıt dosyalarına göreli bağlantılar.
3. Eksik, bozuk veya çelişkili kanıt durumunda (link status=HATA/exit_code=1 iken GECTI iddiası, UI hata alanı doluyken GECTI iddiası, XML testcase içinde failure varken sayaçların sıfır olması, XML skipped iken UI/yaşam döngüsünün çalışıp GECTI demesi, UI test_sonucu=HATA iken XML PASS iddiası, geçersiz/eksik başlangıç modu (expected_branch) veya yaşam döngüsü kapanış başarısızlığı (KAPANMADI/exited=False), UI gozlem.error ve gozlem.cleanup_error alanlarının dolu olması, link observed_states ile UI gözlemi çelişkisi, UI process_start_ticks eksikliği, Start butonu active/On iken idle=True çelişkisi, XML tests=1 iken testcase öğesi bulunmaması, UI changed değeri başlangıçla aynı olması, yaşam döngüsü başarısızlığı veya kapanış uyumsuzluğu, PID farklılığı veya boş yaşam döngüsü JSON'u) kesinlikle doğrulanmış başarı rozeti gösterilmez; "kanıt doğrulanamadı" açıklamasıyla birlikte eksiklik/çelişki gerekçeleri listelenir. Tutarlı KALDI, HATA ve ATLANDI kayıtları kanıtları eksiksizse doğrulanmış kabul edilir; eksiklik ile çelişki birbirinden ayrılır. Orijinal JSON/XML kayıtları değiştirilmez.
4. Raporlama hatası veya eksik kanıt, önceden kaydedilmiş test kanıtlarını ve çıkış kodlarını değiştirmez.
5. HTML raporu tamamen bağımsızdır; harici yazı tipi (font), CDN, JavaScript veya internet erişimi gerektirmez; yerel tarayıcıda doğrudan açılabilir (`file:///`). Kayıtlı test sonuçlarının kaynakları (Pytest XML, Pytest Köprü, UI, Yaşam Döngüsü) raporda ayrı bir kart olarak gösterilir.
6. Her koşunun HTML raporu kendi klasöründe `rapor.html` adıyla yer alır. Eski ham kanıtlar değiştirilmez.
7. Hem mevcut yerel `Existing` hem de `Closed` koşu kanıtları için geçerli `rapor.html` dosyaları üretilir ve doğrulanır.
8. `otomasyon/dogrulama/ortak.py` içindeki tekil ortak kanıt değerlendirme fonksiyonu (`evaluate_run_evidence`) hem `pytest_dogrula.py` hem de `html_rapor.py` tarafından kullanılır; HTML üreticisi bu değerlendirmenin sonucunu yalnız görselleştirir. Bağımsız sentetik sahte kanıt testleri (`tests/unit/test_html_rapor.py`) tüm çelişki senaryolarını, regresyon durumlarını ve geçerli başarısız/atlanan/hata durumlarını (21 birim testi) denetler ve eksiksiz geçer.
9. README ve DEVIR.md belgeleri rapor üretme/görüntüleme komutlarıyla güncellenir.
