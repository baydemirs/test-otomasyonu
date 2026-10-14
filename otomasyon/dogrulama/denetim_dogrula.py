"""GOREV-002 kanıtlarını, mevcut sürümleri ve ham koşu kayıtlarını denetler."""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from ortak import read_json as read, require, digest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'otomasyon/dogrulama'))
from demo_dogrula import check as check_demo


def check(folder):
    folder = folder.resolve()
    folder.relative_to(ROOT/'raporlar/kosular')
    plan = read(folder/'plan.json')
    require(plan['original_criteria_sha256'] == digest(ROOT/'gereksinimler/CANRAT-UI-002.md') == '7c55db26c7fb8a7f5783231f88f86de73326f58a6d8ad390440d7c03e5593e1c', 'Başarılı testin kabul kriteri değişmiş.')
    require(plan['plan_sha256'] == digest(ROOT/'gereksinimler/GOREV-002-denetim-plani.md'), 'Denetim planı koşudan sonra değişmiş.')
    mock = read(folder/'mock/mock-summary.json')
    expected = {'D01': ('HATA', 0), 'D02': ('HATA', 0), 'D03': ('KALDI', 1), 'D04': ('HATA', 2), 'D05': ('HATA', 2), 'D12a': ('HATA', 0), 'D12b': ('ATLANDI', 0)}
    require({r['id'] for r in mock} == set(expected)|{'D11'}, 'Eksik veya fazladan sahte denetim senaryosu.')
    for item in mock:
        require(item['audit_passed'] is True, 'Denetim başarısız: '+item['id'])
        if item['id'] == 'D11':
            codes = [read(folder/f'mock/D11-retry/{i}/command.json')['returncode'] for i in range(3)]
            require(codes == [7, 7, 3] and read(folder/'mock/D11-retry/budget.json')['attempts'] == 2, 'Tekrar sınırı doğrulanmadı.')
            continue
        for file, expected_hash in item['sources'].items():
            require(digest(ROOT/file) == expected_hash, 'Eski denetim kodu/kriteri: '+file)
        require(digest(ROOT/'tests/audit/sahte_canrat.ps1') == item['adapter_sha256'], 'Sahte adaptör sürümü değişmiş.')
        report_path = (ROOT/item['report']).resolve()
        report_path.relative_to(folder)
        raw = read(report_path)
        verdict, calls = expected[item['id']]
        require(raw['test_sonucu'] == verdict and item['fixture_final']['toggle_calls'] == calls, 'Beklenen sonuç/çağrı sayısı uyuşmuyor.')
        if item['id'] == 'D04':
            require(raw['komutlar'][0].get('sure_asimi') is True and raw['komutlar'][0]['sure_siniri_saniye'] == 30, 'Gerçek 30 saniye timeout kaydı eksik.')
            require(len(raw['komutlar']) == 2 and raw['komutlar'][1]['sure_siniri_saniye'] == 12 and raw['kurtarma']['restored'] is True, 'Sınırlı kurtarma kanıtı eksik.')
        if item['id'] == 'D05':
            require(bool(raw['geri_yukleme_hatasi']) and raw['gozlem']['restored'] is False, 'Ayrı geri yükleme hatası yok.')
    evidence_manifest = read(folder/'evidence-final/manifest.json')
    require(evidence_manifest['validator_sha256'] == digest(ROOT/'otomasyon/dogrulama/demo_dogrula.py'), 'Kanıt reddi denetimi eski doğrulayıcı sürümüne ait.')
    require(evidence_manifest['audit_driver_sha256'] == digest(ROOT/'tests/audit/denetim.py'), 'Denetim yürütücüsü değişmiş; kanıtı yeniden değerlendir.')
    require(digest(folder/'D10-document/workspace/otomasyon/dogrulama/demo_dogrula.py') == digest(ROOT/'otomasyon/dogrulama/demo_dogrula.py'), 'Bozuk belge denetimi eski doğrulayıcıya ait.')
    evidence = read(folder/'evidence-final/evidence-summary.json')
    require({r['case'] for r in evidence} == {'valid','missing_report','missing_journal','missing_field','missing_hash','stale_hash','unfinished','wrong_task'}, 'Eksik kanıt denetimi.')
    require(all(r['audit_passed'] is True and r['rejected'] == (r['case'] != 'valid') for r in evidence), 'Eksik/eski kanıt reddi başarısız.')
    broken = read(folder/'D10-document/audit-result.json')
    require(broken['audit_passed'] is True and broken['actual']['returncode'] == 2 and 'gorevler/MISSING.md' in broken['actual']['stderr'], 'Eksik görev yolu reddedilmedi.')
    live = read(folder/'live/live-summary.json')
    require(live['audit_passed'] is True and all(live['checks'].values()), 'Gerçek UI denetimi eksik/başarısız.')
    for file, expected_hash in read(folder/'live/manifest.json')['sources'].items():
        require(digest(ROOT/file) == expected_hash, 'Eski gerçek denetim kanıtı: '+file)
    require(len(live['repeats']) == 2, 'İki tekrar gerekli.')
    for report in live['repeats']:
        report_path = ROOT/report['kanit_yolu']
        require(read(report_path) == report, 'Gerçek tekrar raporu değişmiş.')
        check_demo(report_path)
    checkpoint = read(folder/'live/interrupted.json')
    recovered = read(folder/'live/recovery.json')
    require(checkpoint == live['checkpoint'] and recovered == live['recovery'], 'Kesinti/kurtarma günlüğü uyuşmuyor.')
    require(read(folder/'live/interrupt-command/command.json')['returncode'] == 91, 'Kontrollü kesinti çıkışı yok.')
    require(live['interrupted_test_result'] == 'HATA' and checkpoint['phase'] == 'interrupted_after_change', 'Kesinti başarı sayılmış.')
    fresh = read(ROOT/live['resume_read']['kanit_yolu'])
    require(fresh == live['resume_read'] and fresh['gozlem']['initial'] == checkpoint['current'] != checkpoint['initial'], 'Kesinti sonrası gerçek durum farkı okunmamış.')
    require(fresh['gozlem']['process_id'] == checkpoint['process_id'] == recovered['process_id'] and fresh['gozlem']['process_start_ticks'] == checkpoint['process_start_ticks'] == recovered['process_start_ticks'], 'Kurtarma süreç kimliği farklı.')
    require(recovered['restored'] is True and recovered['final'] == checkpoint['initial'] and not recovered['cleanup_error'], 'Başlangıca dönüş doğrulanmadı.')
    post = read(ROOT/live['postflight']['kanit_yolu'])
    require(post == live['postflight'] and post['inceleme_durumu'] == 'HAZIR' and post['gozlem']['initial'] == checkpoint['initial'], 'Son kontrol durumu doğrulanmadı.')
    current_files = ['otomasyon/dogrulama/demo_dogrula.py', 'otomasyon/dogrulama/denetim_dogrula.py', 'tests/audit/denetim.py', 'tests/audit/gercek_deneme.ps1', 'tests/audit/sahte_canrat.ps1']
    return {'task': 'GOREV-002', 'all_required_checks': True, 'time_utc': datetime.now(timezone.utc).isoformat(),
            'original_criteria_unchanged': True, 'sources': {p:digest(ROOT/p) for p in current_files},
            'live_final_state': post['gozlem']['initial'], 'unmet_criteria': []}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.folder)
        if args.output:
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('GOREV_002_KANITLARI_DOGRULANDI')
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(2, 'DENETIM_REDDEDILDI: '+str(exc)+'\n')
