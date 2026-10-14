# GOREV-006 pywinauto denemesi arşivi

Bu dizin, tamamlanmış karşılaştırmanın Python adaptörünü, yaşam döngüsü sarmalayıcısını, doğrulayıcılarını, sahte kontrol testlerini ve `pywinauto==0.6.9` bağımlılık tanımını korur. Denemenin gerçek PowerShell/UIA ve pywinauto koşuları, ilk pywinauto hatası, sahte kontrol sonuçları ve sınırlar [GOREV-006 raporunda](../../../raporlar/pywinauto-karsilastirma.md) kayıtlıdır. Eski `raporlar/kosular/` dosyaları değiştirilmemiştir.

Karşılaştırma ortamı: Python 3.14.4 (64-bit), pytest 9.1.1, pywinauto 0.6.9, comtypes 1.4.17, pywin32 312, six 1.17.0. Ayrıntılı kurulum kanıtı [pip-freeze.json](../../../raporlar/kosular/pywinauto-f0df9212aa884318b759563d910fe261/pip-freeze.json) dosyasındadır. `requirements-pywinauto.txt` tarihsel bağımlılık listesidir; aktif `requirements-pytest.txt` onu yüklemez.

Dosyalar, deneme kodunun tarihsel kaydıdır. İçlerinde eski `tests/`, `araclar/` ve `uygulama_baglantilari/` yolları bulunabilir; arşivden doğrudan çalıştırılacak aktif senaryo sayılmazlar. Aktif CANRAT-UI-002 yolu [README](../../../README.md) içindedir. Eski koşu kayıtlarındaki kaynak ve kanıt yolları tarihsel haliyle tutulur.
