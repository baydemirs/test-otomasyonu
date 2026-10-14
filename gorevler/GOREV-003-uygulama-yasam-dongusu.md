# GOREV-003 — Uygulama yaşam döngüsü

## Amaç ve kaynak

Kullanıcının 2026-10-13 tarihli talimatıyla CanRat'ın kapalı/açık başlangıç durumunu yönetmek. Bağımlılık: GOREV-002. CANRAT-UI-002 kabul kriterleri değiştirilmez. Görev sayısı doğrulaması bu görev eklenmeden önce genelleştirilmiş ve ayrı fixture testleriyle sınanmıştır.

## Çalıştırmadan önce kabul kriterleri

- Tek hedef `hedef_uygulama/CANRAT_3min/CANRat.exe`. Farklı kopya veya yolu okunamayan süreçte test başlatılmaz. Birden çok CANRat süreci varsa belirsizlik açık raporlanır; örnek seçilmez/sonlandırılmaz.
- Hiç süreç yoksa bu EXE kendi klasörü çalışma dizini yapılarak başlatılır. PID ve UTC süreç başlangıç ticks değeri hemen kaydedilir; owned=true yalnız bu başarılı başlatmadan doğar. Pencere en fazla 15 saniye beklenir.
- Tek doğru örnek önceden açıksa ona bağlanılır; owned=false olur ve koşu sonunda aynı PID/başlangıç zamanıyla açık kaldığı doğrulanır. Bu dal kapatma çağrısı yapamaz.
- Hazır pencere üzerinde mevcut `CANRAT-UI-002 --mode Exercise` komutu çalışır. Start'a basılmaz, CAN bağlantısı başlatılmaz. Testin kendi ön koşulları, değişiklik doğrulaması ve geri yüklemesi aynen uygulanır. Test raporunun PID/başlangıç zamanı yaşam döngüsü kaydıyla eşleşmelidir.
- Yalnızca owned=true süreç için, PID, başlangıç zamanı ve EXE yolu tekrar eşleştiğinde normal CloseMainWindow yöntemi kullanılabilir. En fazla 10 saniye çıkış beklenir. Kapatma reddedilirse/zaman aşımına uğrarsa ayrıca hata kaydedilir; zorla öldürme yoktur.
- Hata halinde mümkün olduğunda yalnız sahip olunan süreç normal kapatılır. Test hâlâ çalışıyorsa veya aktif UI testi mutex'i tutuluyorsa kapatma denenmez. Kaynağı belirsiz etkin CAN göstergesi varsa kapatılmaz ve açık bırakma nedeni raporlanır.
- Başlatma/bağlanma, test ve kapatma/açık bırakma sonuçları ayrı tutulur. Genel GECTI için doğru dal, GECTI test ve doğru son süreç durumu birlikte gerekir.

## Gerçek doğrulama planı

1. Önceden açık kullanıcı örneğinde koşu: BEKLENEN bağlı/owned=false, test GECTI, açık bırakıldı. Kullanıcı örneği kapanmaz.
2. Kullanıcı açık örneği kendisi kapattığını bildirdikten sonra kapalı başlangıçta koşu: BEKLENEN başlatıldı/owned=true, doğru çalışma klasörü ve pencere hazır, test GECTI, normal kapandı.
3. Çoklu örnek/kimlik uyuşmazlığı/sahiplik korumaları sahte nesnelerle ayrıca sınanabilir; gerçek iki başlangıç durumunun yerine sayılmaz.

Üst yürütücü 110 saniye, test alt süreci 55 saniye sınırına sahiptir. Sınırda hâlâ çalışan hedefe zorla sonlandırma uygulanmaz. Ani süreç/OS kesintisinde kapanış garanti değildir; eldeki sahiplik kanıtı korunur ve başarı bildirilmez. CanRat'ın kendi arka plan davranışı denetlenmiş sayılmaz.

## Kanıt ve tamamlanma

Benzersiz koşu klasöründe komut, ortam/kod/EXE/kriter özetleri, başlangıç süreç listesi, sahiplik, pencere bekleme, test raporu yolu, kapatma çağrısı ve sonuç bulunur. Her iki dalın gerçek kanıtı olmadan görev tamamlanmaz. Eski koşu dosyaları yeniden yazılmaz; başlangıçta alınan dosya özetleri iş sonunda karşılaştırılır. Görev durumu yalnız `durum/gorev-durumu.yaml` içindedir.
