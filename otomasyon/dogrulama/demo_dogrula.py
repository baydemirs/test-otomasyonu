"""Yerel belge, görev alanı ve CANRAT-UI-002 kanıt tutarlılığı denetimi."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
from datetime import datetime
from collections import deque
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import digest, project_path

ROOT = Path(__file__).resolve().parents[2]


def parse_tasks(text):
    """Read the project's explicit YAML subset; reject unsupported/ambiguous syntax.

    Supports plain scalars, full-line comments and inline dependency/evidence lists.
    No aliases, tags, multiline values or implicit type conversions are accepted.
    """
    tasks, current = [], None
    version_seen = tasks_seen = False
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        if not tasks_seen and re.fullmatch(r'surum: [1-9][0-9]*', raw):
            if version_seen:
                raise ValueError('Yinelenen surum alanı.')
            version_seen = True
            continue
        if raw == 'gorevler:' and version_seen and not tasks_seen:
            tasks_seen = True
            continue
        match = re.fullmatch(r'  - id: (GOREV-[0-9]{3,})', raw)
        if match and tasks_seen:
            current = {'id': match.group(1)}
            tasks.append(current)
            continue
        field = re.fullmatch(r'    ([a-z_]+): (.*)', raw)
        if current is None or not field:
            raise ValueError(f'Desteklenmeyen görev kaydı biçimi, satır {number}.')
        key, value = field.groups()
        if key in current:
            raise ValueError(f'Yinelenen görev alanı: {current["id"]}.{key}')
        if key not in {'dosya', 'oncelik', 'durum', 'bagimliliklar', 'engel', 'kanitlar'}:
            raise ValueError('Bilinmeyen görev alanı: '+key)
        if key in ('bagimliliklar', 'kanitlar'):
            if not re.fullmatch(r'\[[^\[\]\n]*\]', value):
                raise ValueError('Tek satırlı liste gerekli: '+key)
            body = value[1:-1].strip()
            values = [item.strip() for item in body.split(',')] if body else []
            if any(not item or not re.fullmatch(r'[A-Za-z0-9_./\\-]+', item) for item in values):
                raise ValueError('Geçersiz liste öğesi: '+key)
            current[key] = values
        elif key == 'oncelik':
            if not re.fullmatch(r'[0-9]+', value):
                raise ValueError('Öncelik negatif olmayan tamsayı olmalı.')
            current[key] = int(value)
        else:
            current[key] = value
    if not version_seen or not tasks_seen or not tasks:
        raise ValueError('Sürüm veya görev listesi eksik/boş.')
    return tasks


def validate_tasks(root=None, state_path=None, check_evidence=True):
    root = (ROOT if root is None else Path(root)).resolve()
    state_path = root/'durum/gorev-durumu.yaml' if state_path is None else Path(state_path)
    tasks = parse_tasks(state_path.read_text(encoding='utf-8'))
    by_id = {}
    required = {'id', 'dosya', 'oncelik', 'durum', 'bagimliliklar', 'engel', 'kanitlar'}
    statuses = {'hazir', 'devam_ediyor', 'dogrulaniyor', 'engellendi', 'tamamlandi'}

    def require_file(reference, label):
        path = Path(reference)
        if path.is_absolute():
            raise ValueError(label+' proje içi göreli yol olmalı: '+reference)
        path = (root/path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(label+' proje dışına çıkıyor: '+reference) from exc
        if not path.is_file():
            raise ValueError(label+' yok: '+reference)

    for task in tasks:
        identifier = task['id']
        if identifier in by_id:
            raise ValueError('Yinelenen görev kimliği: '+identifier)
        by_id[identifier] = task
        if set(task) != required:
            raise ValueError('Eksik görev alanları: '+identifier)
        if task['durum'] not in statuses:
            raise ValueError('Geçersiz görev durumu: '+identifier)
        require_file(task['dosya'], 'Görev dosyası')
        if check_evidence:
            if task['durum'] == 'tamamlandi' and not task['kanitlar']:
                raise ValueError('Tamamlanan görevin kanıtı boş: '+identifier)
            for reference in task['kanitlar']:
                require_file(reference, 'Görev kanıt dosyası')
        if len(set(task['bagimliliklar'])) != len(task['bagimliliklar']):
            raise ValueError('Yinelenen bağımlılık: '+identifier)
    indegree = {identifier: 0 for identifier in by_id}
    children = {identifier: [] for identifier in by_id}
    for task in tasks:
        for dependency in task['bagimliliklar']:
            if dependency not in by_id:
                raise ValueError(f'Bilinmeyen bağımlılık: {task["id"]} -> {dependency}')
            if dependency == task['id']:
                raise ValueError('Kendine bağımlılık: '+dependency)
            children[dependency].append(task['id'])
            indegree[task['id']] += 1
    queue = deque(identifier for identifier, count in indegree.items() if count == 0)
    visited = 0
    while queue:
        identifier = queue.popleft()
        visited += 1
        for child in children[identifier]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited != len(tasks):
        raise ValueError('Bağımlılık döngüsü: '+', '.join(i for i, count in indegree.items() if count))
    return tasks


def check(report_path):
    path = Path(report_path).resolve()
    path.relative_to(ROOT)
    report = json.loads(path.read_text(encoding='utf-8'))
    for field in ['gorev_id', 'test_id', 'calistirma_id', 'zaman_utc', 'surumler', 'komut', 'beklenen', 'test_verisi', 'gozlem', 'kanit_yolu']:
        if not report.get(field):
            raise ValueError('Eksik koşu alanı: ' + field)
    if report.get('sema_surumu') != 1 or report['gorev_id'] != 'GOREV-001' or report['test_id'] != 'CANRAT-UI-002' or report['mod'] != 'Exercise' or report['tur'] != 'GERCEK_UI_TESTI':
        raise ValueError('Gerçek CANRAT-UI-002 koşusu gerekli.')
    if report['calistirma_id'] != path.parent.name or datetime.fromisoformat(report['zaman_utc']).tzinfo is None:
        raise ValueError('Koşu kimliği veya zaman bilgisi geçersiz.')
    required_files = {
        'hedef_uygulama/CANRAT_3min/CANRat.exe', 'otomasyon/yurutme/canrat_ui_002.py',
        'otomasyon/yurutme/canrat_ui_002.ps1', 'otomasyon/baglanti/canrat_toggle.ps1',
        'gereksinimler/CANRAT-UI-002.md',
    }
    if not isinstance(report['surumler'], dict) or {p.replace('\\', '/') for p in report['surumler']} != required_files:
        raise ValueError('Zorunlu sürüm kanıtı kümesi eksik veya beklenmeyen dosya içeriyor.')
    if report.get('kaynak') != 'gereksinimler/CANRAT-UI-002.md':
        raise ValueError('Kabul kriteri kaynağı uyuşmuyor.')
    if report.get('hata') or report.get('geri_yukleme_hatasi') or report.get('kurtarma'):
        raise ValueError('Hatalı/kurtarılmış koşu başarılı tamamlama kanıtı olamaz.')
    if (ROOT/report['kanit_yolu']).resolve() != path:
        raise ValueError('Kanıt yolu uyuşmuyor.')
    for filename, expected in report['surumler'].items():
        file = project_path(ROOT, filename)
        if digest(file) != expected:
            raise ValueError('Güncel dosya koşu sürümünden farklı: ' + filename)
    observed = json.loads((path.parent/'uia-adimlari.json').read_text(encoding='utf-8'))
    if observed != report['gozlem']:
        raise ValueError('UIA günlüğü ve sonuç gözlemi farklı.')
    if observed.get('phase') != 'completed' or observed.get('mode') != 'Exercise' or observed.get('cleanup_attempted') is not True:
        raise ValueError('Yarım kalmış veya temizlik kanıtı eksik koşu.')
    if type(observed.get('process_id')) is not int or observed['process_id'] <= 0 or not str(observed.get('process_start_ticks', '')).isdigit():
        raise ValueError('Hedef süreç kimliği eksik.')
    phases = [event.get('phase') for event in observed.get('events', [])]
    if phases != ['initial_saved', 'toggle_attempt', 'change_observed', 'restoring', 'completed']:
        raise ValueError('Zorunlu adım günlüğü eksik veya beklenmeyen sıra.')
    commands = report.get('komutlar')
    if not isinstance(commands, list) or len(commands) != 1 or commands[0].get('cikis_kodu') != 0 or commands[0].get('sure_asimi'):
        raise ValueError('Başarılı tek test komutu kanıtı gerekli.')
    argv = commands[0].get('argv', [])
    if '-Mode' not in argv or argv[-2:] != ['-Mode', 'Exercise'] or '-Journal' not in argv:
        raise ValueError('Gerçek test komutu eksik veya yanlış mod.')
    if Path(argv[argv.index('-Journal')+1]).resolve() != path.parent/'uia-adimlari.json':
        raise ValueError('Komut günlüğü başka koşuya ait.')
    spec = importlib.util.spec_from_file_location('demo_test', ROOT/'otomasyon/yurutme/canrat_ui_002.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected_verdict = module.classify(observed, 'Exercise', report['komutlar'][0]['cikis_kodu'])
    if expected_verdict != report['test_sonucu'] or expected_verdict != 'GECTI':
        raise ValueError('Başarılı demo kabul koşulları sağlanmadı.')
    print('DEMO_KANITI_DOGRULANDI: CANRAT-UI-002; sürümler, günlük, süreç kimliği ve sonuç tutarlı.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--report', type=Path)
    group.add_argument('--tasks-only', action='store_true', help='Görev kaydını ve kanıt dosyalarının varlığını denetler.')
    group.add_argument('--structure-only', action='store_true', help='Yalnızca görev kimliklerini, görev dosyalarını ve bağımlılıkları denetler; kanıt varlığı aramaz.')
    args = parser.parse_args()
    try:
        if args.structure_only:
            tasks = validate_tasks(check_evidence=False)
            print(f'GOREV_YAPISI_DOGRULANDI: {len(tasks)} benzersiz görev; kimlikler, dosyalar ve bağımlılıklar geçerli. Geçmiş kanıtların içeriği ve dosya varlığı bu modda doğrulanmadı.')
        elif args.tasks_only:
            tasks = validate_tasks(check_evidence=True)
            for file in [ROOT/'README.md', ROOT/'gorevler/GOREV-001-ilk-demo-testi.md', ROOT/'gereksinimler/CANRAT-UI-002.md', ROOT/'raporlar/canrat-ui-002.md']:
                if file.exists():
                    for link in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
                        if '://' not in link and not (file.parent/link.split('#')[0]).exists():
                            raise ValueError('Eksik belge/kanıt bağlantısı: ' + link)
            print(f'GOREV_KAYDI_DOGRULANDI: {len(tasks)} benzersiz görev; dosyalar, kanıtlar ve bağımlılıklar geçerli.')
        else:
            check(args.report)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, 'DOĞRULAMA_HATASI: ' + str(exc) + '\n')
