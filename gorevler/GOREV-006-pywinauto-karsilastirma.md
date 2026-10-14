# GOREV-006 — Pywinauto karşılaştırma denemesi

## Kaynak ve sınır

2026-10-14 kullanıcı talimatı. Bağımlılık GOREV-005. GOREV-004 teslim işi olarak ayrılmıştır. `gereksinimler/CANRAT-UI-002.md` kabul kriterleri değişmez. Mevcut PowerShell/UIA adaptörü ve varsayılan pytest yolu korunur. Yeni pywinauto yolu ayrı Python adaptörüdür. Bu görev tek kutu testiyle sınırlıdır.

## Çalıştırmadan önce kabul kriterleri

1. Proje Python 3.14.4 ve pywinauto sürümü/bağımlılık uyumluluğu kurulum ve import ile doğrulanacak. Kurulum yalnız proje `.venv` ortamına yapılacak; sürümler kaydedilecek. Paket üst verisi 3.14 uyumu kanıtı sayılmayacak.
2. Tek mevcut `tests/desktop/test_canrat_ui_002_pytest.py` testi `--canrat-adapter=powershell|pywinauto` ile iki yöntemi seçecek. Seçenek verilmezse `powershell` seçilir. Varsayılan pytest masaüstünde işlem başlatmaz.
3. Her yöntemde aynı tek hedef EXE, tek doğru süreç, aynı `MainWindow.centralwidget.cboxAppendRecieved` QCheckBox ve yalnız okunan Start koruması geçerli. Start Off/Start kesin değilse kutuya dokunulmaz. Başlangıç ToggleState Off veya On kesin ve kararlı okunur. Yalnız hedef TogglePattern bir kez çağrılır; en çok 2 saniyede karşıt durum iki kez doğrulanır. finally içinde gerçek durum okunarak gerekirse başlangıç geri yüklenir ve iki kez doğrulanır. Belirsiz ara/son durum ya da geri yükleme hatası başarı değildir.
4. İlk karşılaştırmada GOREV-003 yaşam döngüsü ilkeleri ve mevcut `uygulama_baglantilari/canrat_yasam.ps1` süreç işlevleri kullanılır; bu dosya ve mevcut `tests/gui/*.ps1`, `uygulama_baglantilari/canrat_toggle.ps1` değiştirilmez. Sahiplik PID, başlangıç zamanı ve EXE yoluyla belirlenir. Önceden açık süreç kapatılmaz, yalnız koşunun başlattığı süreç normal kapanır. Başlatma/test/temizlik ayrı kaydedilir.
5. Gerçek CanRat'ta her iki adaptörle başarılı Off → On → Off koşusu, mümkünse aynı açık süreçte; gerçek süreçlerin PID/başlangıç zamanı ve ürün sürümü SHA-256 ile kaydedilir. Kontrol bulunamaması ve etkileşim/temizlik hata kayıtları ayrı kontrollü sahte kontrollerle değerlendirilir; bunlar gerçek uygulama hatası olarak sunulmaz.
6. Pytest XML sonucu, yaşam döngüsü ve UI JSON kanıtlarına bağlanır; eski kayıtlar değiştirilmez. Pywinauto Python 3.14 altında veya gerçek UI üzerinde çalışmazsa GOREV-006 tamamlanmaz, neden ve eldeki kanıt raporlanır.

## Karşılaştırma raporu

Kod satırı/sorumluluk farkı, pywinauto'nun sadeleştirdiği erişim işlemleri, getirdiği paketler ve eski yönteme göre karşılanamayan davranışlar açıkça listelenir. Kriterler deney sonucuna göre gevşetilmez.
