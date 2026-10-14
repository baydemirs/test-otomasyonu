"""GOREV-002 isolated audit scenarios; fixture evidence is not a product test."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT/'raporlar/kosular/canrat-ui-002-6b9739a5a4924ba4a0fca7b401aeb47f/sonuc.json'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv, folder, timeout=60):
    folder.mkdir(parents=True, exist_ok=True)
    meta = dict(command=list(map(str, argv)), start_utc=datetime.now(timezone.utc).isoformat())
    write(folder/'command.json', meta)
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        meta.update(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired as exc:
        meta.update(returncode=None, timeout=True, stderr=str(exc))
    meta['elapsed_seconds'] = round(time.monotonic()-start, 3)
    write(folder/'command.json', meta)
    return meta


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AttemptBudget:
    def __init__(self, path):
        self.path = path

    def claim(self):
        count = json.loads(self.path.read_text())['attempts'] if self.path.exists() else 0
        if count >= 2:
            return False
        write(self.path, {'attempts': count+1, 'limit': 2})
        return True


def mock_suite(folder):
    expectations = {
        'absent': ('D01', 'HATA', 0), 'missing': ('D02', 'HATA', 0),
        'nochange': ('D03', 'KALDI', 1), 'timeout': ('D04', 'HATA', 2),
        'cleanupfail': ('D05', 'HATA', 2), 'indeterminate': ('D12a', 'HATA', 0),
        'active': ('D12b', 'ATLANDI', 0),
    }
    results = []
    for scenario, (case_id, verdict, toggles) in expectations.items():
        case = folder/(case_id+'-'+scenario)
        fixture = case/'fixture-workspace'
        manifest = {'id': case_id, 'type': 'SAHTE_ADAPTOR_GERCEK_POWERSHELL',
                    'expected_test_result': verdict, 'expected_toggle_calls': toggles,
                    'expected_before_execution_utc': datetime.now(timezone.utc).isoformat(), 'sources': {}}
        for relative in ['otomasyon/yurutme/canrat_ui_002.py', 'otomasyon/yurutme/canrat_ui_002.ps1', 'gereksinimler/CANRAT-UI-002.md']:
            dst = fixture/relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, dst)
            manifest['sources'][relative] = sha(dst)
        adapter = fixture/'otomasyon/baglanti/canrat_toggle.ps1'
        adapter.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'tests/audit/sahte_canrat.ps1', adapter)
        manifest['adapter_sha256'] = sha(adapter)
        # Not executable, never launched. Only used by the production report hash function.
        exe = fixture/'hedef_uygulama/CANRAT_3min/CANRat.exe'
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b'AUDIT FIXTURE NOT AN EXECUTABLE')
        write(fixture/'fixture.json', {'scenario': scenario, 'state': 'Indeterminate' if scenario == 'indeterminate' else 'Off', 'toggle_calls': 0})
        write(case/'manifest.json', manifest)
        observed_command = command([sys.executable, str(fixture/'otomasyon/yurutme/canrat_ui_002.py'), '--mode', 'Exercise'], case, 50)
        reports = list((fixture/'raporlar/kosular').glob('*/sonuc.json'))
        report = json.loads(reports[0].read_text(encoding='utf-8')) if len(reports) == 1 else {}
        state = json.loads((fixture/'fixture.json').read_text())
        checks = {'exit_nonzero': observed_command.get('returncode') == 2,
                  'test_result': report.get('test_sonucu') == verdict,
                  'toggle_count': state['toggle_calls'] == toggles}
        if scenario == 'timeout':
            checks.update(timeout_real=report.get('komutlar', [{}])[0].get('sure_asimi') is True,
                          duration=30 <= observed_command['elapsed_seconds'] < 50,
                          recovery=report.get('kurtarma', {}).get('restored') is True,
                          final_state=state['state'] == 'Off',
                          bounded_attempts=len(report.get('komutlar', [])) == 2)
        if scenario == 'cleanupfail':
            checks.update(cleanup_error=bool(report.get('geri_yukleme_hatasi')),
                          not_restored=report.get('gozlem', {}).get('restored') is False)
        item = dict(manifest, checks=checks, audit_passed=all(checks.values()),
                    report=str(reports[0].relative_to(ROOT)) if reports else None,
                    fixture_final=state, elapsed_seconds=observed_command['elapsed_seconds'])
        write(case/'audit-result.json', item)
        results.append(item)
        print(case_id, scenario, item['audit_passed'], flush=True)

    # Same failed-operation limit persisted across fresh Python processes.
    retry_dir = folder/'D11-retry'
    write(retry_dir/'manifest.json', {'expected_before_execution_utc': datetime.now(timezone.utc).isoformat(),
                                    'expected': 'two failures, third command rejected before invocation', 'type': 'SAHTE_ISLEM'})
    invocations = []
    for i in range(3):
        invocations.append(command([sys.executable, str(Path(__file__)), '--folder', str(retry_dir), '--stage', 'retry-child'], retry_dir/str(i)))
    checks = [x['returncode'] for x in invocations] == [7, 7, 3]
    result = {'id': 'D11', 'type': 'SAHTE_ISLEM', 'audit_passed': checks,
              'exit_codes': [x['returncode'] for x in invocations], 'attempts': json.loads((retry_dir/'budget.json').read_text())}
    write(retry_dir/'audit-result.json', result)
    results.append(result)
    write(folder/'mock-summary.json', results)
    return all(r['audit_passed'] for r in results)


def evidence_suite(folder):
    write(folder/'manifest.json', {'type': 'YAPAY_KANIT_KOPYALARI',
                                  'expected_before_execution_utc': datetime.now(timezone.utc).isoformat(),
                                  'validator_sha256': sha(ROOT/'otomasyon/dogrulama/demo_dogrula.py'),
                                  'audit_driver_sha256': sha(Path(__file__))})
    checker = load_module(ROOT/'otomasyon/dogrulama/demo_dogrula.py', 'audit_checker')
    base = json.loads(ORIGINAL.read_text(encoding='utf-8'))
    results = []
    for case_id in ['valid', 'missing_report', 'missing_journal', 'missing_field', 'missing_hash', 'stale_hash', 'unfinished', 'wrong_task']:
        case = folder/case_id/base['calistirma_id']
        candidate = json.loads(json.dumps(base))
        candidate['kanit_yolu'] = str((case/'sonuc.json').relative_to(ROOT))
        for entry in candidate['komutlar']:
            argv = entry['argv']
            argv[argv.index('-Journal')+1] = str(case/'uia-adimlari.json')
        expected_reject = case_id != 'valid'
        write(case/'manifest.json', {'type': 'YAPAY_KANIT_KOPYASI', 'expected_reject': expected_reject,
                                    'expected_before_execution_utc': datetime.now(timezone.utc).isoformat()})
        if case_id == 'missing_field': candidate.pop('beklenen')
        if case_id == 'missing_hash': candidate['surumler'].pop('tests\\gui\\canrat_ui_002.ps1')
        if case_id == 'stale_hash': candidate['surumler']['tests\\gui\\canrat_ui_002.ps1'] = '0'*64
        if case_id == 'unfinished': candidate['gozlem']['phase'] = 'toggle_attempt'
        if case_id == 'wrong_task': candidate['gorev_id'] = 'GOREV-999'
        if case_id != 'missing_report': write(case/'sonuc.json', candidate)
        if case_id != 'missing_journal': write(case/'uia-adimlari.json', candidate['gozlem'])
        rejected, reason = False, ''
        try:
            with contextlib.redirect_stdout(io.StringIO()): checker.check(case/'sonuc.json')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rejected, reason = True, str(exc)
        item = {'case': case_id, 'type': 'YAPAY_KANIT_KOPYASI', 'expected_reject': expected_reject,
                'rejected': rejected, 'reason': reason, 'audit_passed': rejected == expected_reject}
        write(case/'audit-result.json', item)
        results.append(item)
    write(folder/'evidence-summary.json', results)
    print(json.dumps(results, ensure_ascii=True))
    return all(r['audit_passed'] for r in results)


def broken_document(folder):
    """Isolated file snapshot; never edit the real task registry."""
    import re
    workspace = folder/'workspace'
    report = json.loads(ORIGINAL.read_text(encoding='utf-8'))
    state = (ROOT/'durum/gorev-durumu.yaml').read_text(encoding='utf-8')
    files = set(report['surumler'])
    files.update(['otomasyon/dogrulama/demo_dogrula.py', 'durum/gorev-durumu.yaml'])
    files.update(re.findall(r'^    dosya: (.+)$', state, re.M))
    for line in re.findall(r'^    kanitlar: \[(.*)\]$', state, re.M):
        files.update(p.strip() for p in line.split(',') if p.strip())
    for name in files:
        dst = workspace/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, dst)
    path = workspace/'raporlar/kosular'/report['calistirma_id']/'sonuc.json'
    report['kanit_yolu'] = str(path.relative_to(workspace))
    argv = report['komutlar'][0]['argv']
    argv[argv.index('-Journal')+1] = str(path.parent/'uia-adimlari.json')
    write(path, report)
    write(path.parent/'uia-adimlari.json', report['gozlem'])
    write(folder/'manifest.json', {'type': 'IZOLE_DOSYA_KOPYASI', 'expected': 'missing task path rejected',
                                  'expected_before_execution_utc': datetime.now(timezone.utc).isoformat()})
    (workspace/'durum/gorev-durumu.yaml').write_text(state.replace('dosya: gorevler/GOREV-001-ilk-demo-testi.md', 'dosya: gorevler/MISSING.md'), encoding='utf-8')
    result = command([sys.executable, str(workspace/'otomasyon/dogrulama/demo_dogrula.py'), '--report', str(path)], folder)
    ok = result['returncode'] == 2 and 'gorevler/MISSING.md' in result['stderr']
    write(folder/'audit-result.json', {'id': 'D10', 'type': 'IZOLE_DOSYA_KOPYASI', 'audit_passed': ok, 'actual': result})
    return ok


def parse_report(command_result):
    for line in command_result.get('stdout', '').splitlines():
        if line.startswith('{'):
            data = json.loads(line)
            if data.get('test_id') == 'CANRAT-UI-002':
                return data
    raise ValueError('Yeni süreç sonuç raporu bulunamadı.')


def live_suite(folder):
    """Approved desktop only. No launch/close/Start; restore checkpoint in finally."""
    powershell = shutil.which('powershell.exe')
    exe = ROOT/'hedef_uygulama/CANRAT_3min/CANRat.exe'
    helper = ROOT/'otomasyon/yurutme/canrat_ui_002.ps1'
    audit_helper = ROOT/'tests/audit/gercek_deneme.ps1'
    write(folder/'manifest.json', {'type': 'GERCEK_UI', 'expected_before_execution_utc': datetime.now(timezone.utc).isoformat(),
                                  'expected': 'D02 missing selector rejects; D06 two passes; D07 interruption 91, fresh state read, restore',
                                  'sources': {str(p.relative_to(ROOT)): sha(p) for p in [helper, audit_helper, ROOT/'otomasyon/baglanti/canrat_toggle.ps1', ROOT/'otomasyon/yurutme/canrat_ui_002.py']}})
    inspect_cmd = [sys.executable, str(ROOT/'otomasyon/yurutme/canrat_ui_002.py'), '--mode', 'Inspect']
    pre = parse_report(command(inspect_cmd, folder/'preflight'))
    if pre['inceleme_durumu'] != 'HAZIR':
        write(folder/'live-summary.json', {'audit_passed': False, 'blocked': 'preflight not ready', 'preflight': pre})
        return False
    journal = folder/'missing-control.json'
    missing = command([powershell, '-NoProfile', '-NonInteractive', '-STA', '-File', str(audit_helper), '-Journal', str(journal), '-Mode', 'MissingControl'], folder/'missing-command')
    missing_data = json.loads(journal.read_text(encoding='utf-8'))
    missing_ok = missing['returncode'] == 2 and '__GOREV002_MISSING__' in (missing_data.get('error') or '') and missing_data['mutation_attempted'] is False
    repeats = []
    for i in range(2):
        result = command([sys.executable, str(ROOT/'otomasyon/yurutme/canrat_ui_002.py'), '--mode', 'Exercise'], folder/('repeat-'+str(i+1)))
        data = parse_report(result)
        repeats.append(data)
        if result['returncode'] != 0 or data['test_sonucu'] != 'GECTI':
            write(folder/'live-summary.json', {'audit_passed': False, 'blocked': 'repeat failed; no further interaction', 'repeats': repeats})
            return False

    interrupted = folder/'interrupted.json'
    recovery_journal = folder/'recovery.json'
    summary = {'type': 'GERCEK_UI', 'missing_control_ok': missing_ok, 'repeats': repeats,
               'preflight': pre, 'interrupted_test_result': 'HATA', 'audit_passed': False}
    try:
        stop = command([powershell, '-NoProfile', '-NonInteractive', '-STA', '-File', str(audit_helper), '-Journal', str(interrupted), '-Mode', 'Interrupt'], folder/'interrupt-command', 30)
        summary['interrupt_command'] = stop
        checkpoint = json.loads(interrupted.read_text(encoding='utf-8'))
        summary['checkpoint'] = checkpoint
        # Fresh process reads the actual state; no stale initial state assumption.
        resumed = parse_report(command(inspect_cmd, folder/'resume-inspect'))
        summary['resume_read'] = resumed
    except (OSError, ValueError, KeyError) as exc:
        summary['error'] = str(exc)
    finally:
        # Preserve interrupted evidence; recover a copy, with original identity guards.
        try:
            checkpoint = json.loads(interrupted.read_text(encoding='utf-8'))
            if checkpoint.get('initial') not in ('Off', 'On'):
                raise ValueError('No known initial state for recovery')
            shutil.copyfile(interrupted, recovery_journal)
            recovery = command([powershell, '-NoProfile', '-NonInteractive', '-STA', '-File', str(helper), '-TargetExe', str(exe), '-Journal', str(recovery_journal), '-Mode', 'Recover'], folder/'recovery-command', 12)
            summary['recovery_command'] = recovery
            summary['recovery'] = json.loads(recovery_journal.read_text(encoding='utf-8'))
        except (OSError, ValueError, KeyError) as exc:
            summary['recovery_error'] = str(exc)
        write(folder/'live-summary.json', summary)
    post = parse_report(command(inspect_cmd, folder/'postflight'))
    summary['postflight'] = post
    cp, resumed, recovery = summary.get('checkpoint', {}), summary.get('resume_read', {}), summary.get('recovery', {})
    initial = pre.get('gozlem', {}).get('initial')
    checks = {
        'missing_control': missing_ok,
        'repeat_same_initial': all(r['gozlem']['initial'] == initial and r['gozlem']['final'] == initial for r in repeats),
        'interrupted_own_helper': summary.get('interrupt_command', {}).get('returncode') == 91,
        'checkpoint_incomplete': cp.get('phase') == 'interrupted_after_change',
        'fresh_read_differs': resumed.get('inceleme_durumu') == 'HAZIR' and resumed.get('gozlem', {}).get('initial') == cp.get('current') and cp.get('current') != cp.get('initial'),
        'same_process': resumed.get('gozlem', {}).get('process_id') == cp.get('process_id') == recovery.get('process_id') and resumed.get('gozlem', {}).get('process_start_ticks') == cp.get('process_start_ticks') == recovery.get('process_start_ticks'),
        'restored': recovery.get('restored') is True and recovery.get('final') == cp.get('initial') == initial,
        'recovery_exit': summary.get('recovery_command', {}).get('returncode') == 0,
        'postflight': post.get('inceleme_durumu') == 'HAZIR' and post.get('gozlem', {}).get('initial') == initial,
    }
    summary['checks'] = checks
    summary['audit_passed'] = all(checks.values()) and not summary.get('error') and not summary.get('recovery_error')
    write(folder/'live-summary.json', summary)
    print(json.dumps({'checks': checks, 'audit_passed': summary['audit_passed'], 'initial': initial,
                      'interrupted_current': cp.get('current'), 'final': post.get('gozlem', {}).get('initial')}, ensure_ascii=True))
    return summary['audit_passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path)
    parser.add_argument('--stage', choices=['new', 'mock', 'evidence', 'retry-child', 'broken-document', 'live'], required=True)
    args = parser.parse_args()
    if args.stage == 'new':
        folder = ROOT/'raporlar/kosular'/('denetim-'+uuid4().hex)
        folder.mkdir()
        write(folder/'plan.json', {'task': 'GOREV-002', 'time_utc': datetime.now(timezone.utc).isoformat(),
                                 'plan_sha256': sha(ROOT/'gereksinimler/GOREV-002-denetim-plani.md'),
                                 'original_criteria_sha256': sha(ROOT/'gereksinimler/CANRAT-UI-002.md')})
        print(folder)
        return 0
    folder = args.folder.resolve()
    folder.relative_to(ROOT/'raporlar/kosular')
    if args.stage == 'retry-child':
        if not AttemptBudget(folder/'budget.json').claim():
            print('RETRY_LIMIT_REACHED: invocation refused')
            return 3
        print('FIXTURE_OPERATION_FAILED')
        return 7
    if args.stage == 'mock':
        return 0 if mock_suite(folder) else 2
    if args.stage == 'broken-document':
        return 0 if broken_document(folder) else 2
    if args.stage == 'live':
        return 0 if live_suite(folder) else 2
    return 0 if evidence_suite(folder) else 2


if __name__ == '__main__':
    sys.exit(main())
