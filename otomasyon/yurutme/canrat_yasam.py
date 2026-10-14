"""GOREV-003 supervisor; ownership and cleanup are recorded by the PS helper."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main(expected):
    folder = ROOT/'raporlar/kosular'/('yasam-'+uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    helper = ROOT/'otomasyon/yurutme/canrat_yasam.ps1'
    journal = folder/'yasam-adimlari.json'
    cmd = [shutil.which('powershell.exe'), '-NoProfile', '-NonInteractive', '-STA', '-File', str(helper),
           '-Journal', str(journal), '-Python', sys.executable, '-Expected', expected]
    files = [Path(__file__), helper, ROOT/'otomasyon/baglanti/canrat_yasam.ps1', ROOT/'gorevler/GOREV-003-uygulama-yasam-dongusu.md',
             ROOT/'otomasyon/baglanti/canrat_toggle.ps1', ROOT/'hedef_uygulama/CANRAT_3min/CANRat.exe']
    report = {'task': 'GOREV-003', 'adapter': 'powershell',
              'run_id': folder.name, 'time_utc': datetime.now(timezone.utc).isoformat(),
              'expected': expected, 'command': cmd, 'timeout_seconds': 110, 'result': 'HATA',
              'versions': {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    path = folder/'sonuc.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=110, cwd=ROOT)
        report.update(exit_code=proc.returncode, stderr=proc.stderr)
        observed = json.loads(journal.read_text(encoding='utf-8'))
        report['observed'] = observed
        if proc.returncode == 0 and observed.get('result') == 'GECTI':
            report['result'] = 'GECTI'
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report['error'] = str(exc)
        report['cleanup_uncertain'] = True
        if journal.exists():
            try: report['observed'] = json.loads(journal.read_text(encoding='utf-8'))
            except ValueError: pass
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    print('Rapor: '+str(path))
    return 0 if report['result'] == 'GECTI' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', choices=['Auto','Existing','Closed'], default='Auto')
    args = parser.parse_args()
    sys.exit(main(args.expected))
