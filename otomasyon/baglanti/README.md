# Uygulama Bağlantı Katmanı

`canrat_toggle.ps1`, açık hedef EXE/pencere eşleştirmesi, benzersiz kontrol sorgusu, Start göstergesinin salt okunur kontrolü, ToggleState okuma ve yalnızca izinli kutuya Toggle çağrısını içerir. Windows UI Automation kullanır; uygulamayı açmaz/kapatmaz ve Start'a girdi göndermez.

Beklenen sonucun doğru olup olmadığını test kodu değerlendirecek. Bağlantı katmanı gerçek gözlemi döndürür; test geçti kararı üretmez. Ana servise uyarlamada bu bölüm ve hedefe özgü senaryolar genişleyecek.
