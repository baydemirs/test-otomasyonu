"""GOREV-005: pytest sonucu ile yeni ve mevcut JSON kanitlarini baglar."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import yasam_dogrula
from ortak import (
    check_guard_consistency,
    check_states_match,
    check_ticks_validity,
    check_xml_cases,
    evaluate_run_evidence,
    project_path as _project_path,
    read_json,
    require,
    require_versions,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = {'tests/desktop/test_canrat_ui_002_pytest.py',
                'otomasyon/yurutme/canrat_yasam.py', 'gereksinimler/CANRAT-UI-002.md'}


def project_path(reference):
    return _project_path(ROOT, reference)


def check(folder, expected):
    folder = project_path(folder)
    require(folder.parent.name.startswith('pytest-gecis-') and
            folder.parent.parent == ROOT/'raporlar/kosular', 'Beklenmeyen pytest kanit klasoru.')
    info = evaluate_run_evidence(folder, root=ROOT, expected_branch=expected)
    require(info['verification_status'] == 'DOGRULANDI',
            f"Kanıt doğrulanamadı: {'; '.join(info['reasons'])}")
    require(info['recorded_result'] == 'GECTI',
            f"Kayıtlı test sonucu GECTI değil: {info['recorded_result']}")
    link = read_json(folder/'pytest-link.json')
    require(link['task'] == 'GOREV-005' and link.get('adapter', 'powershell') == 'powershell' and
            link['test_id'] == 'CANRAT-UI-002' and
            link['run_id'] == folder.name and link['expected_branch'] == expected and
            link['status'] == 'DOGRULANDI' and link['exit_code'] == 0 and
            not link.get('error'), 'Pytest koprusu basarisiz veya eksik.')
    require(link['expected_states'] in (['Off', 'On', 'Off'], ['On', 'Off', 'On']), 'Gecersiz beklenen durumlar.')
    require(link['observed_states'] == link['expected_states'], 'Durum gecisi eslesmiyor.')
    require(link['pytest_version'] == '9.1.1', 'Pytest surumu uyusmuyor.')
    require_versions(ROOT, link['versions'], SOURCE_FILES, 'Test surum dosyalari eksik.')
    life_path = project_path(link['lifecycle_report'])
    ui_path = project_path(link['ui_report'])
    require(life_path.parent.parent == ROOT/'raporlar/kosular' and
            ui_path.parent.parent == ROOT/'raporlar/kosular' and
            life_path.name == ui_path.name == 'sonuc.json', 'Ic kanit yolu beklenmiyor.')
    life = yasam_dogrula.check(life_path, expected)
    require(project_path(link['lifecycle_journal']) == life_path.parent/'yasam-adimlari.json'
            and project_path(link['ui_journal']) == ui_path.parent/'uia-adimlari.json'
            and project_path(life['observed']['test']['report_path']) == ui_path,
            'Pytest ve JSON kanit yollari farkli.')
    ui = read_json(ui_path)
    initial = ui['gozlem'].get('initial')
    require(initial in ('Off', 'On'), 'UI baslangic durumu gecersiz.')
    ui_expected = [initial, 'On' if initial == 'Off' else 'Off', initial]
    require(link['expected_states'] == ui_expected, 'Köprü beklenen durumları ile UI beklenen durumları eşleşmiyor.')
    require(ui['test_sonucu'] == 'GECTI' and ui['gozlem']['restored'] is True and
            [ui['gozlem'][key] for key in ('initial', 'changed', 'final')] == ui_expected,
            'UI sonucu/geri yuklemesi beklenmiyor.')
    v_states, err_states = check_states_match(link['observed_states'], [ui['gozlem'][k] for k in ('initial', 'changed', 'final')])
    require(v_states, err_states)
    v_ticks, err_ticks = check_ticks_validity(ui['gozlem'].get('process_start_ticks'))
    require(v_ticks, err_ticks)
    for g in ui['gozlem'].get('guard_before', []):
        v_g, err_g = check_guard_consistency(g)
        require(v_g, err_g)
    if ui['gozlem'].get('guard_after'):
        v_g, err_g = check_guard_consistency(ui['gozlem']['guard_after'])
        require(v_g, err_g)
    observed = life['observed']
    require(link['process_id'] == observed['identity']['pid'] and
            link['process_start_ticks'] == observed['identity']['start_ticks'] and
            [link['start'], link['test'], link['close']] ==
            [observed['start']['status'], observed['test']['status'], observed['close']['status']],
            'Asama veya surec kimligi farkli.')
    xml = ET.parse(folder/'pytest.xml').getroot()
    v_xml, err_xml, *_ = check_xml_cases(xml)
    require(v_xml, err_xml)
    suites = list(xml.iter('testsuite'))
    cases = list(xml.iter('testcase'))
    require(len(suites) == len(cases) == 1 and
            all(suites[0].attrib.get(k) == v for k, v in
                {'tests': '1', 'errors': '0', 'failures': '0', 'skipped': '0'}.items()) and
            cases[0].attrib.get('name') == 'test_canrat_ui_002_via_lifecycle' and
            not any(child.tag in ('failure', 'error', 'skipped') for child in cases[0]),
            'Pytest sonucu PASS degil.')
    command = read_json(folder/'pytest-komut.json')
    argv = command['argv']
    require(command['exit_code'] == 0 and
            project_path(argv[0]) == ROOT/'.venv/Scripts/python.exe' and
            argv[1:3] == ['-m', 'pytest'] and
            '--run-desktop' in argv and
            argv[argv.index('--canrat-initial')+1] == expected and
            '--canrat-adapter' not in argv and
            project_path(argv[argv.index('--evidence-dir')+1]) == folder and
            project_path(argv[argv.index('--junitxml')+1]) == folder/'pytest.xml',
            'Gercek pytest komutu eksik/yanlis.')
    return link


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path)
    parser.add_argument('--expected', choices=('Existing', 'Closed'))
    parser.add_argument('--existing', type=Path)
    parser.add_argument('--closed', type=Path)
    args = parser.parse_args()
    try:
        if args.folder is not None:
            require(args.expected is not None and args.existing is None and args.closed is None,
                    'Tek koşu için --folder ve --expected gerekir.')
            check(args.folder, args.expected)
            print('PYTEST_KANITI_DOGRULANDI: '+args.expected+'; pytest XML, yaşam döngüsü ve UI JSON eşleşiyor.')
        else:
            require(args.expected is None and args.existing is not None and args.closed is not None,
                    'İki dal için --existing ve --closed gerekir.')
            first = check(args.existing, 'Existing')
            second = check(args.closed, 'Closed')
            require(first['run_id'] != second['run_id'], 'Iki ayri pytest kosusu gerekli.')
            print('PYTEST_KANITI_DOGRULANDI: Existing + Closed; pytest XML, yaşam döngüsü ve UI JSON eşleşiyor.')
    except (OSError, ValueError, KeyError, TypeError, IndexError, ET.ParseError) as exc:
        parser.exit(2, 'PYTEST_KANITI_REDDEDILDI: '+str(exc)+'\n')
