"""GOREV-006 tamamlama: iki adaptörün gerçek ve sentetik kanıtlarını ayırır."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import demo_dogrula
import pytest_dogrula


ROOT = Path(__file__).resolve().parents[1]


def read(reference):
    return json.loads(pytest_dogrula.project_path(reference).read_text(encoding='utf-8-sig'))


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def check(base, audit):
    base = pytest_dogrula.project_path(base)
    audit = pytest_dogrula.project_path(audit)
    py = pytest_dogrula.check(base/'pywinauto-acik', 'Existing', 'pywinauto')
    ps = pytest_dogrula.check(base/'powershell-acik', 'Existing', 'powershell')
    closed = pytest_dogrula.check(base/'pywinauto-kapali-gecerli', 'Closed', 'pywinauto')
    require(py['process_id'] == ps['process_id'] and
            py['process_start_ticks'] == ps['process_start_ticks'] and
            py['observed_states'] == ps['observed_states'] == closed['observed_states'] ==
            ['Off', 'On', 'Off'], 'Aynı gerçek süreç/sonuç kıyası sağlanmadı.')
    setup = read(audit/'tespit-hazirlik.json')
    post = read(audit/'acik-son-kontrol.json')
    cleanup = read(audit/'tespit-hazirlik-temizlik.json')
    require(setup['owned_by_setup'] is True and setup['pid'] == py['process_id'] and
            setup['start_ticks'] == py['process_start_ticks'] and
            post['same_process_open'] is True and post['observed']['pid'] == setup['pid'] and
            post['observed']['start_ticks'] == setup['start_ticks'] and
            cleanup['identity']['pid'] == setup['pid'] and
            cleanup['identity']['start_ticks'] == setup['start_ticks'] and
            cleanup['guard']['idle'] is True and
            cleanup['close']['method'] == 'CloseMainWindow' and
            cleanup['close']['exited'] is True and cleanup['after'] == [],
            'Açık süreç sahipliği/sonraki temizlik kanıtı eksik.')
    failed = read(base/'pywinauto-kapali/pytest-link.json')
    require(failed['status'] == 'HATA' and failed['exit_code'] != 0 and
            failed['adapter'] == 'pywinauto', 'İlk gerçek hata başarı sayılmış.')
    failed_life = read(failed['lifecycle_report'])
    failed_child = read(failed_life['observed']['test']['report_path'])
    require(failed_life['result'] == 'HATA' and
            failed_life['observed']['owned'] is True and
            failed_life['observed']['close']['status'] == 'KAPANDI' and
            failed_child['test_sonucu'] == 'HATA' and
            failed_child['gozlem']['mutation_attempted'] is False and
            'Beklenmeyen kontrol türü' in failed_child['hata'],
            'Gerçek başarısızlık/normal kapatma kanıtı farklı.')
    xml = ET.parse(base/'pywinauto-kapali/pytest.xml').getroot()
    require(len(list(xml.iter('testcase'))) == 1 and
            list(xml.iter('testsuite'))[0].attrib['failures'] == '1',
            'İlk gerçek FAIL pytest kaydı yok.')
    fake = read(audit/'sahte-kontroller.json')
    require(fake['kind'] == 'SYNTHETIC_CONTROLS_NO_APP' and fake['exit_code'] == 0 and
            'Ran 6 tests' in fake['stderr'], 'Sentetik kontroller eksik.')
    compat = read(audit/'uyumluluk.json')
    require(compat['python'] == '3.14.4' and compat['import_ok'] is True and
            compat['packages'] == {'pywinauto':'0.6.9', 'comtypes':'1.4.17',
                                   'pywin32':'312', 'six':'1.17.0', 'pytest':'9.1.1'},
            'Kurulu ortam sürümleri farklı.')
    demo_dogrula.validate_tasks()
    return {'task':'GOREV-006', 'real_same_pid':py['process_id'],
            'real_same_start_ticks':py['process_start_ticks'],
            'powershell':'GECTI', 'pywinauto_existing':'GECTI',
            'pywinauto_closed':'GECTI', 'real_initial_error':'HATA',
            'synthetic_controls':'PASSED', 'all_required_checks':True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--audit-folder', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.base, args.audit_folder)
        if args.output:
            output = pytest_dogrula.project_path(args.output)
            with output.open('x', encoding='utf-8') as file:
                json.dump(result, file, ensure_ascii=False, indent=2)
        print('PYWINAUTO_KARSILASTIRMA_DOGRULANDI: aynı süreç, üç PASS, bir gerçek FAIL ve ayrı sahte kontroller.')
    except (OSError, ValueError, KeyError, TypeError, IndexError, ET.ParseError) as exc:
        parser.exit(2, 'PYWINAUTO_KARSILASTIRMA_REDDEDILDI: '+str(exc)+'\n')
