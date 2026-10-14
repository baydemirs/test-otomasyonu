"""GOREV-003 icin iki gercek baslangic dalinin guncel kanitlarini dogrular."""
import argparse
from datetime import datetime
import json
from pathlib import Path

import demo_dogrula
from ortak import project_path as _project_path, read_json, require, require_versions

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILES = {
    'otomasyon/yurutme/canrat_yasam.py', 'otomasyon/yurutme/canrat_yasam.ps1',
    'otomasyon/baglanti/canrat_yasam.ps1',
    'gorevler/GOREV-003-uygulama-yasam-dongusu.md',
    'otomasyon/baglanti/canrat_toggle.ps1',
    'hedef_uygulama/CANRAT_3min/CANRat.exe',
}


def project_path(value):
    return _project_path(ROOT, value)


def validate_observed(o, expected):
    """Semantic checks, also exercised with synthetic negative records."""
    require(o['schema_version'] == 1 and o['task'] == 'GOREV-003', 'Yanlis sema/gorev.')
    require(o['expected'] == expected and o['result'] == 'GECTI', 'Dal/sonuc uyusmuyor.')
    require(not o['error'] and not o['cleanup_error'], 'Test veya kapatma hatasi var.')
    identity = o['identity']
    require(type(identity['pid']) is int and identity['pid'] > 0 and
            str(identity['start_ticks']).isdigit(), 'Surec kimligi eksik.')
    exe = ROOT / 'hedef_uygulama/CANRAT_3min/CANRat.exe'
    require(project_path(identity['path']) == exe and project_path(o['start']['exe']) == exe,
            'Hedef EXE uyusmuyor.')
    require(project_path(o['working_directory']) == exe.parent, 'Calisma klasoru yanlis.')
    require(o['start']['window_ready'] is True and o['start']['window'] > 0, 'Pencere hazir degil.')
    t, c = o['test'], o['close']
    require(t['status'] == 'GECTI' and t['exit_code'] == 0, 'Alt test basarili degil.')
    require(t['observed_identity'] == {key: identity[key] for key in ('pid', 'start_ticks')},
            'Alt test baska surece ait.')
    phases = ['before', 'identity', 'window_ready', 'test_start', 'test_finished', 'finished']
    if expected == 'Existing':
        require(o['owned'] is False and o['before'] == [identity], 'Mevcut surec sahiplenilemez.')
        require(o['start']['status'] == 'MEVCUDA_BAGLANILDI', 'Baglanma kaniti yok.')
        require(c['status'] == 'ACIK_BIRAKILDI' and c['request_sent'] is False and
                c['still_running'] is True, 'Mevcut surece kapatma uygulanmis.')
        require(len(o['after']) == 1 and all(o['after'][0][k] == identity[k]
                for k in ('pid', 'start_ticks', 'path')), 'Ayni surec acik kalmamis.')
    elif expected == 'Closed':
        phases.insert(1, 'launch_intent')
        require(o['owned'] is True and o['before'] == [], 'Kapali baslangic/sahiplik yok.')
        require(o['start']['status'] == 'BASLATILDI' and
                project_path(o['start']['working_directory']) == exe.parent, 'Baslatma klasoru yanlis.')
        require(c['status'] == 'KAPANDI' and c['method'] == 'CloseMainWindow' and
                c['request_sent'] is True and c['exited'] is True and c['exit_code'] == 0,
                'Normal kapatma kaniti yok.')
        require(o['after'] == [], 'Kapanis sonrasi surec kalmis.')
    else:
        raise ValueError('Tamamlama icin Existing veya Closed dali gerekli.')
    events = o['events']
    require([e['phase'] for e in events] == phases, 'Eksik/yarim adim gunlugu.')
    times = [datetime.fromisoformat(e['time_utc'].replace('Z', '+00:00')) for e in events]
    require(all(t.tzinfo is not None for t in times) and times == sorted(times), 'Zaman sirasi hatali.')


def check(path, expected):
    path = project_path(path)
    r = read_json(path)
    require(r['task'] == 'GOREV-003' and r['run_id'] == path.parent.name and
            r['expected'] == expected and r['result'] == 'GECTI' and r['exit_code'] == 0 and
            not r.get('error') and not r.get('cleanup_uncertain'), 'Basarili kosu gerekli.')
    require_versions(ROOT, r['versions'], VERSION_FILES, 'Surum kaniti kumesi eksik.')
    o = read_json(path.parent/'yasam-adimlari.json')
    require(r['observed'] == o, 'Sonuc ve gunluk farkli.')
    validate_observed(o, expected)
    cmd = r['command']
    require(project_path(cmd[cmd.index('-Journal')+1]) == path.parent/'yasam-adimlari.json' and
            project_path(cmd[cmd.index('-File')+1]) == ROOT/'otomasyon/yurutme/canrat_yasam.ps1' and
            cmd[cmd.index('-Expected')+1] == expected, 'Komut kaniti uyusmuyor.')
    nested = project_path(o['test']['report_path'])
    demo_dogrula.check(nested)
    t = read_json(nested)
    require(o['test']['observed_identity'] == {'pid': t['gozlem']['process_id'],
            'start_ticks': t['gozlem']['process_start_ticks']}, 'Alt rapor kimligi farkli.')
    event_times = {e['phase']: datetime.fromisoformat(e['time_utc'].replace('Z', '+00:00'))
                   for e in o['events']}
    child_times = [datetime.fromisoformat(e['time_utc'].replace('Z', '+00:00'))
                   for e in t['gozlem']['events']]
    require(all(event_times['test_start'] <= time <= event_times['test_finished']
                for time in child_times), 'Alt test baska zamana ait; eski kanit reddedildi.')
    stdout = project_path(o['test']['stdout'])
    require(stdout.parent == path.parent, 'Baska kosunun stdout kaniti.')
    lines = [json.loads(line) for line in stdout.read_text(encoding='utf-8').splitlines()
             if line.startswith('{')]
    require(lines == [t], 'Test stdout ve rapor farkli.')
    return r


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--existing', required=True, type=Path)
    parser.add_argument('--closed', required=True, type=Path)
    args = parser.parse_args()
    try:
        existing = check(args.existing, 'Existing')
        closed = check(args.closed, 'Closed')
        require(existing['run_id'] != closed['run_id'], 'Iki ayri gercek kosu gerekli.')
        print('YASAM_KANITI_DOGRULANDI: Existing + Closed; sahiplik, test, kapatma ve guncel surumler tutarli.')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(2, 'DOGRULAMA_HATASI: '+str(exc)+'\n')
