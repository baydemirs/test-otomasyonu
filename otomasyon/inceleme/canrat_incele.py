"""CanRat UI Automation envanteri. Test sonucu üretmez; uygulamayı değiştirmez."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4


def sha256(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def collect(exe_path, timeout=25, system=None, runner=None):
    """Windows child process is bounded; no GUI action, launch, or close is issued."""
    system = platform.system() if system is None else system
    runner = subprocess.run if runner is None else runner
    report = {
        'sema_surumu': 1,
        'tur': 'ARAYUZ_INCELEMESI',
        'gorev_id': 'GOREV-000',
        'calistirma_id': uuid4().hex,
        'zaman_utc': datetime.now(timezone.utc).isoformat(),
        'ortam': {'sistem': system, 'python': platform.python_version()},
        'inceleme_durumu': 'ENGELLENDI',
        'test_sonucu': None,
        'aciklama': '',
        'uygulama_yolu': str(Path(exe_path).resolve()),
        'uygulama_sha256': None,
        'arac_sha256': sha256(__file__),
        'sure_siniri_saniye': timeout,
        'gozlem': None,
    }
    if system != 'Windows':
        report['aciklama'] = 'Bu inceleme Windows masaüstü oturumunda çalıştırılmalıdır.'
        return report
    exe = Path(exe_path).resolve()
    if not exe.is_file() or exe.name.lower() != 'canrat.exe':
        report['aciklama'] = 'Mevcut CANRat.exe dosyasının tam yolunu verin.'
        return report
    powershell = shutil.which('powershell.exe')
    if powershell is None:
        report['aciklama'] = 'Windows PowerShell bulunamadı.'
        return report
    helper = Path(__file__).with_name('canrat_uia.ps1')
    try:
        report['uygulama_sha256'] = sha256(exe)
        report['uia_araci_sha256'] = sha256(helper)
        command = [powershell, '-NoProfile', '-NonInteractive', '-STA',
                   '-File', str(helper), '-TargetExe', str(exe)]
        report['alt_komut'] = command
        proc = runner(command, capture_output=True, text=True,
                      encoding='utf-8', errors='replace', timeout=timeout,
                      check=False)
        report['alt_komut_cikis_kodu'] = proc.returncode
        if proc.returncode != 0:
            report['aciklama'] = 'UIA incelemesi tamamlanamadı. Hata kaydını inceleyin.'
            report['hata'] = proc.stderr[-6000:]
            return report
        observed = json.loads(proc.stdout.lstrip('\ufeff').strip())
        if not isinstance(observed, dict) or observed.get('schema_version') != 1:
            raise ValueError('Geçersiz UIA çıktı şeması.')
        if not isinstance(observed.get('process_id'), int) or observed['process_id'] <= 0:
            raise ValueError('Geçerli süreç kimliği bulunamadı.')
        if not isinstance(observed.get('window'), dict):
            raise ValueError('Ana pencere kaydı bulunamadı.')
        if not isinstance(observed.get('controls'), list):
            raise ValueError('Kontrol listesi bulunamadı.')
        report['gozlem'] = observed
        if observed.get('truncated') or observed.get('read_errors'):
            report['aciklama'] = 'Kısmi envanter alındı; eksik kontroller ayrıca incelenmeli.'
        elif not observed['controls']:
            report['aciklama'] = 'Pencere bulundu, alt kontroller okunamadı. Erişim yöntemi incelenmeli.'
        else:
            report['inceleme_durumu'] = 'GOZLEM_ALINDI'
            report['aciklama'] = 'Kontrol envanteri alındı. Bu kayıt testin geçtiği anlamına gelmez.'
    except subprocess.TimeoutExpired:
        report['aciklama'] = 'İnceleme süre sınırını aştı. İnceleme süreci durduruldu; CanRat kapatılmadı.'
    except (OSError, ValueError, TypeError) as exc:
        report['aciklama'] = 'İnceleme hatası: ' + str(exc)
    return report


def save_report(report, output_root):
    folder = Path(output_root) / ('inceleme-' + report['calistirma_id'])
    folder.mkdir(parents=True, exist_ok=False)
    target = folder / 'arayuz-envanteri.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True, help='Açık olan CANRat.exe dosyasının tam yolu')
    parser.add_argument('--timeout', type=int, default=25)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'raporlar' / 'kosular')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 120:
        parser.error('--timeout 1 ile 120 arasında olmalıdır')
    report = collect(args.exe, timeout=args.timeout)
    report['komut'] = [sys.executable, *sys.argv]
    try:
        target = save_report(report, args.output)
    except OSError as exc:
        print('Rapor kaydedilemedi: ' + str(exc), file=sys.stderr)
        return 3
    print(report['aciklama'])
    print('Rapor: ' + str(target.resolve()))
    return 0 if report['inceleme_durumu'] == 'GOZLEM_ALINDI' else 2


if __name__ == '__main__':
    sys.exit(main())
