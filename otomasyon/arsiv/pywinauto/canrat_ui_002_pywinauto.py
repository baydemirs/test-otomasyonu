"""CANRAT-UI-002 with pywinauto; same criterion, independent UI adapter."""
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'uygulama_baglantilari'))
from canrat_pywinauto import checkbox, connect, guard, stable_state, wait_state
from canrat_ui_002 import classify


@contextmanager
def ui_mutex(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateMutexW(None, False, f'Local\\CANRAT_UI_002_{pid}')
    if not handle:
        raise OSError(ctypes.get_last_error(), 'CreateMutexW failed')
    acquired = False
    try:
        result = kernel.WaitForSingleObject(handle, 0)
        if result not in (0, 0x80):
            raise RuntimeError(f'Aynı PID üzerinde UI koşusu etkin: WaitForSingleObject={result}')
        acquired = True
        yield
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def run():
    folder = ROOT/'raporlar/kosular'/('canrat-ui-002-pywinauto-'+uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    journal = folder/'uia-adimlari.json'
    report_path = folder/'sonuc.json'
    exe = ROOT/'hedef_uygulama/CANRAT_3min/CANRat.exe'
    observed = {'schema_version': 1, 'adapter': 'pywinauto', 'mode': 'Exercise',
                'phase': 'preflight', 'process_id': None, 'process_start_ticks': None,
                'guard_before': [], 'guard_after': None, 'initial': None,
                'expected_changed': None, 'changed': None, 'changed_verified': False,
                'final': None, 'restored': False, 'mutation_attempted': False,
                'cleanup_attempted': False, 'active_collection': False,
                'error': None, 'cleanup_error': None, 'events': []}
    files = [Path(__file__), ROOT/'uygulama_baglantilari/canrat_pywinauto.py',
             ROOT/'tests/canrat_ui_002.py', ROOT/'gereksinimler/CANRAT-UI-002.md', exe]
    report = {'sema_surumu': 1, 'gorev_id': 'GOREV-006', 'test_id': 'CANRAT-UI-002',
              'calistirma_id': folder.name, 'zaman_utc': datetime.now(timezone.utc).isoformat(),
              'tur': 'GERCEK_UI_TESTI', 'adapter': 'pywinauto', 'mod': 'Exercise',
              'komut': [sys.executable, *sys.argv], 'calisma_klasoru': str(ROOT),
              'ortam': {'sistem': platform.system(), 'python': platform.python_version()},
              'beklenen': {'ilk': 'kesin Off veya On', 'degisim': 'ilk değerin karşıtı',
                           'son': 'ilk değer', 'start': 'Off / Start'},
              'test_verisi': {'kontrol_id': 'MainWindow.centralwidget.cboxAppendRecieved'},
              'kaynak': 'gereksinimler/CANRAT-UI-002.md',
              'surumler': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in files},
              'test_sonucu': 'HATA', 'gozlem': None, 'hata': None,
              'geri_yukleme_hatasi': None, 'kanit_yolu': str(report_path.relative_to(ROOT))}

    def save(phase):
        observed['phase'] = phase
        observed['events'].append({'time_utc': datetime.now(timezone.utc).isoformat(),
                                   'phase': phase})
        temporary = journal.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(observed, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(journal)

    start = time.monotonic()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    control = None
    window = None
    try:
        pid = int(os.environ['CANRAT_EXPECTED_PID'])
        ticks = os.environ['CANRAT_EXPECTED_TICKS']
        expected_exe = Path(os.environ['CANRAT_EXPECTED_EXE']).resolve()
        if expected_exe != exe.resolve():
            raise ValueError('Belirtilen EXE yolu beklentiyle eşleşmiyor.')
        window, identity = connect(pid, ticks, expected_exe)
        observed['process_id'] = identity['pid']
        observed['process_start_ticks'] = identity['start_ticks']
        with ui_mutex(pid):
            try:
                for _ in range(2):
                    g = guard(window)
                    observed['guard_before'].append(g)
                    if g['active']:
                        observed['active_collection'] = True
                        raise RuntimeError('Veri toplama etkin; kutuya dokunulmadı.')
                    if not g['idle']:
                        raise RuntimeError('Start durumu belirsiz; kutuya dokunulmadı.')
                    time.sleep(0.15)
                control = checkbox(window)
                observed['initial'] = stable_state(control)
                observed['expected_changed'] = ('On' if observed['initial'] == 'Off' else 'Off')
                save('initial_saved')
                g = guard(window)
                observed['guard_before'].append(g)
                if not g['idle']:
                    observed['active_collection'] = g['active']
                    raise RuntimeError('Etkileşim öncesi Start durumu değişti.')
                if stable_state(control) != observed['initial']:
                    raise RuntimeError('Başlangıç durumu dışarıdan değişti.')
                observed['mutation_attempted'] = True
                save('toggle_attempt')
                control.toggle()  # UIA TogglePattern, never click Start.
                observed['changed'] = wait_state(control, observed['expected_changed'])
                observed['changed_verified'] = observed['changed'] == observed['expected_changed']
                save('change_observed')
            except Exception as exc:
                observed['error'] = str(exc)
            finally:
                if control is not None and observed['initial'] in ('Off', 'On') and observed['mutation_attempted']:
                    observed['cleanup_attempted'] = True
                    try:
                        save('restoring')
                        current = stable_state(control)
                        if current != observed['initial']:
                            control.toggle()
                        observed['final'] = wait_state(control, observed['initial'])
                        observed['restored'] = observed['final'] == observed['initial']
                        if not observed['restored']:
                            raise RuntimeError('Başlangıca dönüş doğrulanamadı.')
                    except Exception as exc:
                        observed['cleanup_error'] = str(exc)
                if window is not None:
                    try:
                        observed['guard_after'] = guard(window)
                    except Exception as exc:
                        observed['error'] = observed['error'] or ('Son Start durumu okunamadı: '+str(exc))
    except Exception as exc:
        observed['error'] = observed['error'] or str(exc)
    finally:
        save('completed')
        report['gozlem'] = observed
        report['hata'] = observed['error']
        report['geri_yukleme_hatasi'] = observed['cleanup_error']
        report['test_sonucu'] = classify(observed, 'Exercise',
                                         0 if not observed['error'] and not observed['cleanup_error'] else 2)
        report['sure_saniye'] = round(time.monotonic()-start, 3)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    print('Rapor: '+str(report_path))
    return 0 if report['test_sonucu'] == 'GECTI' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['Exercise'], required=True)
    parser.parse_args()
    sys.exit(run())
