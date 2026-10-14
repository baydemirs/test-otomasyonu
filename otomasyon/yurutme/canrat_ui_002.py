"""CANRAT-UI-002: yalnızca izinli kutuyu değiştirir ve ilk duruma döndürür."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
TEST_ID = 'CANRAT-UI-002'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(observed, mode, returncode=0):
    """Fail closed: process exit alone is never a passed GUI test."""
    if not isinstance(observed, dict) or observed.get('schema_version') != 1:
        return 'HATA'
    if observed.get('active_collection') is True and observed.get('mutation_attempted') is False:
        return 'ATLANDI'
    if returncode != 0 or observed.get('error') or observed.get('cleanup_error') or observed.get('cleanup_journal_error'):
        return 'HATA'
    guards = observed.get('guard_before')
    after = observed.get('guard_after')
    if not isinstance(guards, list) or len(guards) < 2 or not isinstance(after, dict):
        return 'HATA'
    if any(g.get('toggle_state') != 'Off' or g.get('name') != 'Start' or g.get('idle') is not True
           for g in [*guards, after] if isinstance(g, dict)) or any(not isinstance(g, dict) for g in guards):
        return 'HATA'
    initial = observed.get('initial')
    if initial not in ('Off', 'On'):
        return 'HATA'
    if mode == 'Inspect':
        return 'HAZIR' if observed.get('mutation_attempted') is False else 'HATA'
    expected = 'On' if initial == 'Off' else 'Off'
    if observed.get('mutation_attempted') is not True or observed.get('restored') is not True:
        return 'HATA'
    if observed.get('final') != initial or observed.get('expected_changed') != expected:
        return 'HATA'
    if observed.get('changed') not in ('On', 'Off'):
        return 'HATA'
    if observed.get('changed') != expected:
        return 'KALDI'
    return 'GECTI' if observed.get('changed_verified') is True else 'HATA'


def run(mode):
    folder = ROOT / 'raporlar' / 'kosular' / ('canrat-ui-002-' + uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    journal = folder / 'uia-adimlari.json'
    result_path = folder / 'sonuc.json'
    helper = ROOT / 'otomasyon/yurutme/canrat_ui_002.ps1'
    exe = ROOT / 'hedef_uygulama/CANRAT_3min/CANRat.exe'
    report = {
        'sema_surumu': 1, 'gorev_id': 'GOREV-001', 'test_id': TEST_ID,
        'calistirma_id': folder.name, 'zaman_utc': datetime.now(timezone.utc).isoformat(),
        'tur': 'ON_KOSUL_INCELEMESI' if mode == 'Inspect' else 'GERCEK_UI_TESTI',
        'mod': mode, 'komut': [sys.executable, *sys.argv], 'calisma_klasoru': str(ROOT),
        'ortam': {'sistem': platform.system(), 'python': platform.python_version()},
        'beklenen': {'ilk': 'kesin Off veya On', 'degisim': 'ilk değerin karşıtı', 'son': 'ilk değer', 'start': 'Off / Start'},
        'test_verisi': {'kontrol_id': 'MainWindow.centralwidget.cboxAppendRecieved'},
        'kaynak': 'gereksinimler/CANRAT-UI-002.md',
        'surumler': {}, 'test_sonucu': None, 'inceleme_durumu': None,
        'gozlem': None, 'hata': None, 'geri_yukleme_hatasi': None,
        'kurtarma': None, 'komutlar': [], 'kanit_yolu': str(result_path.relative_to(ROOT)),
    }
    # Save a skeleton before execution; no successful result is pre-populated.
    def save():
        result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def execute(operation, path, timeout):
        command = [shutil.which('powershell.exe'), '-NoProfile', '-NonInteractive', '-STA',
                   '-File', str(helper), '-TargetExe', str(exe), '-Journal', str(path), '-Mode', operation]
        entry = {'argv': command, 'sure_siniri_saniye': timeout, 'cikis_kodu': None}
        report['komutlar'].append(entry)
        save()
        started = time.monotonic()
        try:
            proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                  errors='replace', timeout=timeout, check=False, cwd=ROOT)
            entry.update(cikis_kodu=proc.returncode, stderr=proc.stderr[-6000:])
            return proc.returncode
        except subprocess.TimeoutExpired:
            entry['sure_asimi'] = True
            raise
        finally:
            entry['sure_saniye'] = round(time.monotonic() - started, 3)
            save()

    started = time.monotonic()
    try:
        if platform.system() != 'Windows' or not shutil.which('powershell.exe'):
            raise RuntimeError('Windows ve Windows PowerShell gereklidir.')
        for path in [exe, Path(__file__), helper, ROOT/'otomasyon/baglanti/canrat_toggle.ps1', ROOT/report['kaynak']]:
            report['surumler'][str(path.relative_to(ROOT))] = digest(path)
        save()
        code = execute(mode, journal, 30)
        observed = json.loads(journal.read_text(encoding='utf-8'))
        report['gozlem'] = observed
        verdict = classify(observed, mode, code)
        report['test_verisi']['ilk_toggle_state'] = observed.get('initial')
        report['hata'] = observed.get('error') or observed.get('cleanup_journal_error') or (report['komutlar'][-1].get('stderr') if code != 0 else None)
        report['geri_yukleme_hatasi'] = observed.get('cleanup_error')
        report['inceleme_durumu' if mode == 'Inspect' else 'test_sonucu'] = verdict
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report['hata'] = type(exc).__name__ + ': ' + str(exc)
        report['inceleme_durumu' if mode == 'Inspect' else 'test_sonucu'] = 'HATA'
        if mode == 'Exercise':
            # Original journal remains intact; recover only a known original state.
            try:
                observed = json.loads(journal.read_text(encoding='utf-8'))
                report['gozlem'] = observed
                if observed.get('mutation_attempted') is True and observed.get('initial') in ('Off', 'On'):
                    recovery_path = folder / 'kurtarma-adimlari.json'
                    shutil.copyfile(journal, recovery_path)
                    recovery_code = execute('Recover', recovery_path, 12)
                    recovered = json.loads(recovery_path.read_text(encoding='utf-8'))
                    report['kurtarma'] = recovered
                    if recovery_code != 0 or recovered.get('restored') is not True or recovered.get('final') != observed['initial']:
                        report['geri_yukleme_hatasi'] = recovered.get('cleanup_error') or recovered.get('error') or 'Kurtarma doğrulanamadı.'
                elif observed.get('mutation_attempted') is True:
                    report['geri_yukleme_hatasi'] = 'İlk durum bilinmediği için tahminle kurtarma yapılmadı.'
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as recovery_error:
                report['geri_yukleme_hatasi'] = 'Geri yükleme kanıtı alınamadı: ' + str(recovery_error)
    finally:
        report['sure_saniye'] = round(time.monotonic() - started, 3)
        save()
    print(json.dumps(report, ensure_ascii=True))
    print('Rapor: ' + str(result_path))
    verdict = report['inceleme_durumu'] if mode == 'Inspect' else report['test_sonucu']
    return 0 if verdict in ('HAZIR', 'GECTI') else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['Inspect', 'Exercise'], default='Inspect')
    sys.exit(run(parser.parse_args().mode))
