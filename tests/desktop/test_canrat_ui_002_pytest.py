"""One opt-in pytest bridge to the existing CANRAT-UI-002 lifecycle."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _save(path, record): 
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


@pytest.mark.desktop
def test_canrat_ui_002_via_lifecycle(request):
    expected = request.config.getoption('--canrat-initial')
    evidence_arg = request.config.getoption('--evidence-dir')
    if expected not in ('Existing', 'Closed') or not evidence_arg:
        pytest.fail('Açık --canrat-initial=Existing|Closed ve --evidence-dir gerekli.', pytrace=False)
    evidence = Path(evidence_arg).resolve()
    runs = (ROOT / 'raporlar/kosular').resolve()
    if (evidence.parent.parent != runs or not evidence.parent.name.startswith('pytest-gecis-')
            or not evidence.is_dir()):
        pytest.fail('Kanıt klasörü raporlar/kosular/pytest-gecis-*/<dal> altında olmalı.', pytrace=False)
    link = evidence / 'pytest-link.json'
    if link.exists():
        pytest.fail('Pytest kanıtı üzerine yazılamaz.', pytrace=False)

    source = ROOT / 'otomasyon/yurutme/canrat_yasam.py'
    command = [sys.executable, str(source), '--expected', expected]
    record = {
        'task': 'GOREV-005', 'adapter': 'powershell',
        'test_id': 'CANRAT-UI-002', 'run_id': evidence.name,
        'expected_branch': expected, 'expected_states': ['Off', 'On', 'Off'],
        'time_utc': datetime.now(timezone.utc).isoformat(),
        'command': command, 'timeout_seconds': 125, 'status': 'HATA',
        'versions': {
            'tests/desktop/test_canrat_ui_002_pytest.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'otomasyon/yurutme/canrat_yasam.py': hashlib.sha256(source.read_bytes()).hexdigest(),
            'gereksinimler/CANRAT-UI-002.md': hashlib.sha256((ROOT/'gereksinimler/CANRAT-UI-002.md').read_bytes()).hexdigest(),
        },
        'pytest_version': pytest.__version__,
    }
    _save(link, record)
    error = None
    try:
        started = time.monotonic()
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=125, check=False)
        record['duration_seconds'] = round(time.monotonic() - started, 3)
        record['exit_code'] = proc.returncode
        record['stderr'] = proc.stderr[-4000:]
        lines = [line.removeprefix('Rapor: ').strip() for line in proc.stdout.splitlines()
                 if line.startswith('Rapor: ')]
        if len(lines) != 1:
            raise ValueError('Tam bir yeni yaşam döngüsü raporu yolu okunamadı.')
        path = Path(lines[0]).resolve()
        if path.parent.parent != runs or path.name != 'sonuc.json':
            raise ValueError('Yaşam döngüsü raporu beklenen koşu klasöründe değil.')
        life = json.loads(path.read_text(encoding='utf-8'))
        record['lifecycle_report'] = str(path.relative_to(ROOT))
        if datetime.fromisoformat(life['time_utc']) < datetime.fromisoformat(record['time_utc']):
            raise ValueError('Eski yaşam döngüsü kanıtı reddedildi.')
        if proc.returncode != 0 or life.get('result') != 'GECTI':
            raise ValueError('Yaşam döngüsü başarısız: ' + str(life.get('observed', {}).get('error') or life.get('error') or proc.stderr[-500:]))
        sys.path.insert(0, str(ROOT/'otomasyon/dogrulama'))
        import yasam_dogrula
        yasam_dogrula.check(path, expected)
        nested = (ROOT/life['observed']['test']['report_path']).resolve()
        nested.relative_to(ROOT)
        child = json.loads(nested.read_text(encoding='utf-8'))
        observed = child['gozlem']
        record['ui_report'] = str(nested.relative_to(ROOT))
        record['ui_journal'] = str((nested.parent/'uia-adimlari.json').relative_to(ROOT))
        record['lifecycle_journal'] = str((path.parent/'yasam-adimlari.json').relative_to(ROOT))
        record['observed_states'] = [observed['initial'], observed['changed'], observed['final']]
        record['process_id'] = life['observed']['identity']['pid']
        record['process_start_ticks'] = life['observed']['identity']['start_ticks']
        record['start'] = life['observed']['start']['status']
        record['test'] = life['observed']['test']['status']
        record['close'] = life['observed']['close']['status']
        if record['observed_states'] != record['expected_states'] or observed['restored'] is not True:
            raise ValueError('Off → On → Off ve geri yükleme doğrulanmadı.')
        record['status'] = 'DOGRULANDI'
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.TimeoutExpired) as exc:
        error = str(exc)
        record['error'] = error
    finally:
        _save(link, record)
    if error:
        pytest.fail(error, pytrace=False)
