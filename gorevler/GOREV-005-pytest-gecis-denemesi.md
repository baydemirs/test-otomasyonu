# GOREV-005 — Pytest geçiş denemesi

## Kapsam ve bağımlılık

Kullanıcının 2026-10-14 talimatı. GOREV-003 yaşam döngüsü ve CANRAT-UI-002 işlev testi yeniden kullanılır. GOREV-004 teslim işi için ayrılmıştır; bu görevin bağımlılığı değildir. Bir pytest masaüstü testi eklenir. Uygulamaya erişen PowerShell/UIA kodu ve önceki kabul kriterleri değiştirilmez. Toplu test bağımlılıkları ve HTML raporu sonraki görev kapsamındadır.

## Koşudan önce kabul kriterleri

1. Proje `.venv` içinde sürümü kayıtlı pytest kurulu olacak. Gerçek komut bu sanal ortamın Python yorumlayıcısını kullanacak.
2. Varsayılan `python -m pytest` ve mevcut `python -m unittest discover -s tests/unit` CanRat açmayacak ve UIA işlemi başlatmayacak. Masaüstü testi yalnız açık `--run-desktop` seçeneğiyle yürütülecek.
3. Tek pytest testinin `--canrat-initial=Existing|Closed` seçeneği, başlangıç koşulunu zorunlu kılacak. Mevcut tek doğru örnekte kutu Off → On → Off ve Start Off/Start doğrulanacak; aynı PID/başlangıç zamanı açık kalacak. Kapalı başlangıçta doğru EXE doğru çalışma klasöründen açılacak, kutu Off → On → Off doğrulanacak ve yalnız testin açtığı örnek normal `CloseMainWindow` ile kapanacak.
4. Yaşam döngüsü komutunun çıkış kodu, `sonuc.json`, `yasam-adimlari.json` ve iç CANRAT-UI-002 `sonuc.json`/UIA günlüğü birlikte doğrulanacak. Başlatma, test veya temizlik hatası pytest PASS olamaz. Kanıt bulunamaz, güncel sürümle uyuşmaz veya ara durum belirsizse FAIL olur.
5. Her gerçek pytest koşusunun kimliği, pytest sürümü, test kodu özeti, gerçek komutu, pytest sonucu ve ilişkilendirilmiş yeni yaşam döngüsü/iç test JSON yolları yeni koşu klasöründe saklanacak. Eski koşu kayıtları değiştirilmez.
6. Hem Existing hem Closed dalı gerçek Windows masaüstünde bu pytest testi üzerinden çalışıp kanıt doğrulamasını geçmedikçe GOREV-005 tamamlanmaz. Kullanıcının açtığı örnek otomatik kapatılmaz. Start'a basılmaz ve CAN bağlantısı başlatılmaz.

## Doğrulama

- Varsayılan birim testleri ve varsayılan pytest koleksiyonu; masaüstü testi atlanır.
- Proje sanal ortamı içinde açık masaüstü pytest komutu, her başlangıç dalında ayrı gerçek koşu.
- Yeni ve eski kanıtların dosya özetleri; eski kayıtlar değişmemiş olmalı.
