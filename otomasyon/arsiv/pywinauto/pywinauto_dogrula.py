"""Validate the alternate UI adapter against the unchanged CANRAT-UI-002 criterion."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

import yasam_dogrula


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = yasam_dogrula.VERSION_FILES - {'tests/gui/canrat_yasam.ps1'} | {
    'tests/gui/canrat_yasam_pywinauto.ps1', 'tests/canrat_ui_002_pywinauto.py',
    'uygulama_baglantilari/canrat_pywinauto.py',
    'gereksinimler/CANRAT-UI-002.md', 'requirements-pywinauto.txt',
}
UI_FILES = {'tests/canrat_ui_002_pywinauto.py',
            'uygulama_baglantilari/canrat_pywinauto.py',
            'tests/canrat_ui_002.py', 'gereksinimler/CANRAT-UI-002.md',
            'hedef_uygulama/CANRAT_3min/CANRat.exe'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check(path, expected):
    path = yasam_dogrula.project_path(path)
    report = read(path)
    require(report.get('task') == 'GOREV-006' and report.get('adapter') == 'pywinauto' and
            report.get('expected') == expected and report.get('run_id') == path.parent.name and
            report.get('result') == 'GECTI' and report.get('exit_code') == 0 and
            not report.get('error') and not report.get('cleanup_uncertain'), 'Yaşam döngüsü başarılı değil.')
    versions = {p.replace('\\', '/'): value for p, value in report['versions'].items()}
    require(set(versions) == VERSION_FILES, 'Yaşam döngüsü sürüm kümesi eksik.')
    for name, digest in versions.items():
        require(hashlib.sha256(yasam_dogrula.project_path(name).read_bytes()).hexdigest() == digest,
                'Eski yaşam döngüsü kaynağı: '+name)
    observed = read(path.parent/'yasam-adimlari.json')
    require(report['observed'] == observed and observed.get('task') == 'GOREV-006' and
            observed.get('adapter') == 'pywinauto', 'Yaşam döngüsü günlüğü farklı.')
    yasam_dogrula.validate_observed({**observed, 'task': 'GOREV-003'}, expected)
    command = report['command']
    require(yasam_dogrula.project_path(command[command.index('-File')+1]) ==
            ROOT/'tests/gui/canrat_yasam_pywinauto.ps1' and
            yasam_dogrula.project_path(command[command.index('-Journal')+1]) ==
            path.parent/'yasam-adimlari.json' and
            command[command.index('-Expected')+1] == expected,
            'Yaşam döngüsü komutu farklı.')
    child_path = yasam_dogrula.project_path(observed['test']['report_path'])
    child = read(child_path)
    ui = read(child_path.parent/'uia-adimlari.json')
    require(child['gorev_id'] == 'GOREV-006' and child['test_id'] == 'CANRAT-UI-002' and
            child['calistirma_id'] == child_path.parent.name and
            child['adapter'] == ui['adapter'] == 'pywinauto' and
            child['test_sonucu'] == 'GECTI' and not child['hata'] and
            not child['geri_yukleme_hatasi'] and child['gozlem'] == ui and
            yasam_dogrula.project_path(child['kanit_yolu']) == child_path,
            'İç UI testi sonucu/günlüğü farklı.')
    child_versions = {p.replace('\\', '/'): value for p, value in child['surumler'].items()}
    require(set(child_versions) == UI_FILES, 'İç UI kaynak kümesi eksik.')
    for name, digest in child_versions.items():
        require(hashlib.sha256(yasam_dogrula.project_path(name).read_bytes()).hexdigest() == digest,
                'Eski iç UI kaynağı: '+name)
    from sys import path as module_path
    module_path.insert(0, str(ROOT/'tests'))
    from canrat_ui_002 import classify
    require(classify(ui, 'Exercise', 0) == 'GECTI' and
            ui['phase'] == 'completed' and ui['cleanup_attempted'] is True and
            [ui[key] for key in ('initial', 'changed', 'final')] == ['Off', 'On', 'Off'],
            'CANRAT-UI-002 kabul ölçütü veya Off-On-Off sağlanmadı.')
    require(observed['test']['observed_identity'] ==
            {'pid': ui['process_id'], 'start_ticks': ui['process_start_ticks']},
            'İç UI süreci farklı.')
    times = [datetime.fromisoformat(event['time_utc'].replace('Z', '+00:00'))
             for event in ui['events']]
    outer_times = {event['phase']: datetime.fromisoformat(event['time_utc'].replace('Z', '+00:00'))
                   for event in observed['events']}
    require([event['phase'] for event in ui['events']] ==
            ['initial_saved', 'toggle_attempt', 'change_observed', 'restoring', 'completed'] and
            all(outer_times['test_start'] <= moment <= outer_times['test_finished'] for moment in times),
            'İç UI olay sırası/zamanı uyuşmuyor.')
    stdout = yasam_dogrula.project_path(observed['test']['stdout'])
    require(stdout.parent == path.parent and
            [json.loads(line) for line in stdout.read_text(encoding='utf-8').splitlines()
             if line.startswith('{')] == [child], 'İç test stdout/JSON farklı.')
    return report
