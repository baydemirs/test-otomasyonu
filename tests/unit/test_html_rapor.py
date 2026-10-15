"""Unit tests for otomasyon.dogrulama.html_rapor.

Tüm testler geçici dizinlerdeki sentetik sahte kanıt setleriyle bağımsız çalışır.
Eksiklik ile çelişkiyi ayırır; tutarlı KALDI, HATA ve ATLANDI kayıtlarının
doğrulanmış durumunu ve çelişkili durumlarda KANIT DOĞRULANAMADI sonucunu denetler.
"""
import json
from pathlib import Path
import tempfile
import unittest

from otomasyon.dogrulama.html_rapor import evaluate_run, generate_report, render_html

ROOT = Path(__file__).resolve().parents[2]


def build_valid_mock_run(folder_path, branch='Closed', pid=12345, ticks='639000000000000000'):
    """Eksiksiz, doğrulanabilir sentetik bir test koşu seti oluşturur."""
    f = Path(folder_path)
    run_dir = f / 'acik' if branch == 'Existing' else f / 'kapali'
    run_dir.mkdir(parents=True, exist_ok=True)
    ui_dir = f / 'mock_ui'
    ui_dir.mkdir(parents=True, exist_ok=True)
    life_dir = f / 'mock_life'
    life_dir.mkdir(parents=True, exist_ok=True)

    # 1. pytest.xml
    (run_dir / 'pytest.xml').write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuite errors="0" failures="0" name="pytest" skipped="0" tests="1" time="8.0">\n'
        '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="7.94"/>\n'
        '</testsuite>\n',
        encoding='utf-8'
    )

    # 2. UI sonuc.json
    ui_sonuc = {
        "test_id": "CANRAT-UI-002",
        "calistirma_id": ui_dir.name,
        "test_sonucu": "GECTI",
        "gozlem": {
            "schema_version": 1,
            "mode": "Exercise",
            "phase": "completed",
            "process_id": pid,
            "process_start_ticks": ticks,
            "initial": "Off",
            "expected_changed": "On",
            "changed": "On",
            "changed_verified": True,
            "final": "Off",
            "restored": True,
            "mutation_attempted": True,
            "cleanup_attempted": True,
            "active_collection": False,
            "error": None,
            "cleanup_error": None,
            "cleanup_journal_error": None,
            "events": [
                {"phase": "initial_saved"},
                {"phase": "toggle_attempt"},
                {"phase": "change_observed"},
                {"phase": "restoring"},
                {"phase": "completed"}
            ],
            "guard_before": [{"toggle_state": "Off", "name": "Start", "active": False, "idle": True}],
            "guard_after": {"toggle_state": "Off", "name": "Start", "active": False, "idle": True}
        }
    }
    (ui_dir / 'sonuc.json').write_text(json.dumps(ui_sonuc, indent=2), encoding='utf-8')
    (ui_dir / 'uia-adimlari.json').write_text(json.dumps(ui_sonuc["gozlem"], indent=2), encoding='utf-8')

    # 3. Yaşam döngüsü sonuc.json
    close_obj = (
        {"status": "ACIK_BIRAKILDI", "request_sent": False, "still_running": True}
        if branch == 'Existing' else
        {"status": "KAPANDI", "method": "CloseMainWindow", "request_sent": True, "exited": True, "exit_code": 0}
    )
    life_sonuc = {
        "task": "GOREV-003",
        "run_id": life_dir.name,
        "expected": branch,
        "result": "GECTI",
        "exit_code": 0,
        "observed": {
            "schema_version": 1,
            "task": "GOREV-003",
            "expected": branch,
            "owned": (branch == 'Closed'),
            "before": [] if branch == 'Closed' else [{"pid": pid, "start_ticks": ticks}],
            "identity": {"pid": pid, "start_ticks": ticks},
            "start": {"status": "MEVCUDA_BAGLANILDI" if branch == 'Existing' else "BASLATILDI"},
            "test": {
                "status": "GECTI",
                "exit_code": 0,
                "report_path": str(ui_dir / 'sonuc.json'),
                "observed_identity": {"pid": pid, "start_ticks": ticks}
            },
            "close": close_obj
        }
    }
    (life_dir / 'sonuc.json').write_text(json.dumps(life_sonuc, indent=2), encoding='utf-8')
    (life_dir / 'yasam-adimlari.json').write_text(json.dumps(life_sonuc["observed"], indent=2), encoding='utf-8')

    # 4. pytest-link.json
    link_data = {
        "task": "GOREV-005",
        "adapter": "powershell",
        "test_id": "CANRAT-UI-002",
        "run_id": run_dir.name,
        "expected_branch": branch,
        "expected_states": ["Off", "On", "Off"],
        "observed_states": ["Off", "On", "Off"],
        "time_utc": "2026-10-14T12:00:00+00:00",
        "duration_seconds": 7.94,
        "exit_code": 0,
        "status": "DOGRULANDI",
        "process_id": pid,
        "process_start_ticks": ticks,
        "start": "MEVCUDA_BAGLANILDI" if branch == 'Existing' else "BASLATILDI",
        "test": "GECTI",
        "close": "ACIK_BIRAKILDI" if branch == 'Existing' else "KAPANDI",
        "lifecycle_report": str(life_dir / 'sonuc.json'),
        "ui_report": str(ui_dir / 'sonuc.json'),
        "lifecycle_journal": str(life_dir / 'yasam-adimlari.json'),
        "ui_journal": str(ui_dir / 'uia-adimlari.json')
    }
    (run_dir / 'pytest-link.json').write_text(json.dumps(link_data, indent=2), encoding='utf-8')

    return run_dir, ui_dir, life_dir


class TestHtmlRapor(unittest.TestCase):

    def test_baseline_valid_mock_run_produces_dogrulandi(self):
        """Eksiksiz geçerli sahte kanıt setinin DOĞRULANDI ürettiğini sına."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'GECTI')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'GECTI (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'pass')
            self.assertEqual(len(info['verification_reasons']), 0)

            html = render_html(info)
            self.assertIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('DOGRULANDI', html)
            self.assertNotIn('http://', html)
            self.assertNotIn('https://', html)

    # === YENİ 4 SORUN DENETİMİ ===

    # 1. pytest-link observed_states, UI gözlemleriyle çelişiyor
    def test_link_observed_states_contradicts_ui(self):
        """Link observed_states ile UI gözlemleri çelişiyorsa KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # Link ['Off', 'On', 'Off'] diyor fakat UI sonucunda ['Off', 'On', 'On'] var
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['gozlem']['final'] = 'On'
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('çelişiyor' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    # 2. UI process_start_ticks eksik
    def test_ui_process_start_ticks_missing(self):
        """UI process_start_ticks eksik veya geçersizse KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            del data['gozlem']['process_start_ticks']  # Eksik!
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('process_start_ticks eksik' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    # 3. Start active=true/toggle_state=On iken idle=true
    def test_start_active_or_on_while_idle_true(self):
        """Start butonu active=True veya toggle_state=On iken idle=True ise çelişki bildirmeli."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            # Çelişkili guard: active=True iken idle=True
            data['gozlem']['guard_after'] = {
                "toggle_state": "On",
                "name": "Stop",
                "active": True,
                "idle": True
            }
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('Start butonu çelişkili' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    # 4. XML tests=1 fakat testcase öğesi yok
    def test_xml_tests_one_but_no_testcase(self):
        """XML tests=1 beyan edip testcase öğesi içermiyorsa KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # testcase tag'i yok
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="0" name="pytest" skipped="0" tests="1" time="0.0">\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('testcase öğesi yok' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    # === TUTARLI BAŞARISIZLIK VE ATLANMA TESTLERİ ===

    def test_consistent_kaldi_produces_dogrulandi(self):
        """Tutarlı KALDI kaydı sırf başarısız olduğu için 'kanıt doğrulanamadı' sayılmamalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            # Test başarısız: kutu değişmedi (Off -> Off) ve UI dürüstçe KALDI bildirdi
            ui_path = ui_dir / 'sonuc.json'
            ui_data = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_data['test_sonucu'] = 'KALDI'
            ui_data['gozlem']['changed'] = 'Off'
            ui_data['gozlem']['restored'] = False
            ui_path.write_text(json.dumps(ui_data), encoding='utf-8')
            (ui_dir / 'uia-adimlari.json').write_text(json.dumps(ui_data['gozlem']), encoding='utf-8')

            # Yaşam döngüsü de alt testin KALDI olduğunu bildiriyor
            life_path = life_dir / 'sonuc.json'
            life_data = json.loads(life_path.read_text(encoding='utf-8'))
            life_data['result'] = 'KALDI'
            life_data['observed']['test']['status'] = 'KALDI'
            life_path.write_text(json.dumps(life_data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(life_data['observed']), encoding='utf-8')

            # Link de UI ile tutarlı olarak failure yansıtıyor
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'KALDI'
            link_data['test'] = 'KALDI'
            link_data['exit_code'] = 1
            link_data['observed_states'] = ['Off', 'Off', 'Off']
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            # XML de KALDI (failures=1)
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="1" name="pytest" skipped="0" tests="1" time="8.0">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="7.94">\n'
                '    <failure message="Off -> On -> Off doğrulanmadı"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'KALDI')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'KALDI (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'fail')

            html = render_html(info)
            self.assertIn('KALDI (DOĞRULANDI)', html)
            self.assertIn('Kayıtlı Test Sonucu: KALDI &bull; Kanıt Doğrulama: DOĞRULANDI', html)
            self.assertNotIn('KANIT DOĞRULANAMADI', html)

    def test_consistent_atlandi_produces_dogrulandi(self):
        """Tutarlı ATLANDI kaydı doğrulanmış kanıt olarak sunulmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # XML test atlandı
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="0" name="pytest" skipped="1" tests="1" time="0.0">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="0.0">\n'
                '    <skipped message="desktop mark skipped"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )
            # Gerçekte atlanan testte köprü UI/yaşam döngüsü yürütmez
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'ATLANDI'
            link_data['test'] = 'ATLANDI'
            link_data['exit_code'] = 0
            link_data.pop('ui_report', None)
            link_data.pop('lifecycle_report', None)
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'ATLANDI')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'ATLANDI (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'warn')

            html = render_html(info)
            self.assertIn('ATLANDI (DOĞRULANDI)', html)
            self.assertIn('Kayıtlı Test Sonucu: ATLANDI &bull; Kanıt Doğrulama: DOĞRULANDI', html)
            self.assertNotIn('KANIT DOĞRULANAMADI', html)

    # === ÖNCEKİ TESTLERİN KORUNMASI ===

    def test_ui_changed_same_as_initial_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['gozlem']['changed'] = 'Off'
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')

    def test_lifecycle_failure_or_close_mismatch_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['result'] = 'HATA'
            life_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')

    def test_ui_pid_mismatch_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed', pid=12345)
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['gozlem']['process_id'] = 99999
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')

    def test_pytest_xml_tests_zero_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="0" name="pytest" skipped="0" tests="0" time="0.0"/>\n',
                encoding='utf-8'
            )
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')

    def test_lifecycle_json_empty_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            (life_dir / 'sonuc.json').write_text('{}', encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')

    def test_generate_report_writes_file_and_returns_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            out_file, info = generate_report(run_dir)
            self.assertTrue(out_file.is_file())
            self.assertEqual(out_file.name, 'rapor.html')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')

    # === REGRESYON TESTLERİ ===

    def test_link_hata_exit_1_while_gecti_fails_verification(self):
        """Link status=HATA ve exit_code=1 iken XML GECTI dese bile KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'HATA'
            link_data['exit_code'] = 1
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('HATA (exit=1)' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_ui_hata_populated_while_gecti_fails_verification(self):
        """UI hata alanı doluyken GECTI rozeti gösterilmemeli, KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            ui_data = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_data['hata'] = 'Beklenmeyen UIA kontrol hatası'
            ui_path.write_text(json.dumps(ui_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('hata alanı dolu' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_xml_testcase_failure_with_zero_counters_fails_verification(self):
        """XML testsuite failures=0 iken testcase içinde failure varsa KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="0" name="pytest" skipped="0" tests="1" time="8.0">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="7.94">\n'
                '    <failure message="Gizli başarısızlık"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('failures sayacı' in r and 'çelişiyor' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_xml_skipped_with_ui_life_gecti_contradiction_fails_verification(self):
        """XML skipped iken UI ve yaşam döngüsü GECTI diyorsa çelişki nedeniyle KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="0" name="pytest" skipped="1" tests="1" time="0.0">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="0.0">\n'
                '    <skipped message="test skipped"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('skipped' in r and 'GECTI' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('ATLANDI (DOĞRULANDI)', html)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_consistent_hata_produces_dogrulandi(self):
        """Tutarlı HATA kaydı dürüst bir hata durumunda HATA (DOĞRULANDI) üretmeli."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="1" failures="0" name="pytest" skipped="0" tests="1" time="1.0">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="1.0">\n'
                '    <error message="Fixture setup failed"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'HATA'
            link_data['test'] = 'HATA'
            link_data['exit_code'] = 1
            link_data['error'] = 'Fixture setup failed'
            link_data.pop('ui_report', None)
            link_data.pop('lifecycle_report', None)
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'HATA')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'HATA (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'fail')

            html = render_html(info)
            self.assertIn('HATA (DOĞRULANDI)', html)
            self.assertIn('Kayıtlı Test Sonucu: HATA &bull; Kanıt Doğrulama: DOĞRULANDI', html)
            self.assertNotIn('KANIT DOĞRULANAMADI', html)

    # === YENİ 3 AÇIK REGRESYON TESTLERİ ===

    def test_ui_test_sonucu_hata_with_xml_pass_fails_verification(self):
        """Yalnız UI test_sonucu=HATA yapıldığında XML PASS olsa bile KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # XML PASS ve link DOGRULANDI iken yalnızca UI test_sonucu HATA yapılıyor
            ui_path = ui_dir / 'sonuc.json'
            ui_data = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_data['test_sonucu'] = 'HATA'
            ui_path.write_text(json.dumps(ui_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'HATA')
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('UI test sonucu' in r and 'çelişki' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_invalid_branch_and_close_not_exited_fails_verification(self):
        """expected_branch=Invalid ve yaşam döngüsü close.status=KAPANMADI, exited=False iken KANIT DOĞRULANAMADI olmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            # Link expected_branch geçersiz yapılıyor
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['expected_branch'] = 'Invalid'
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            # Yaşam döngüsü kapanışı başarısız yapılıyor
            life_path = life_dir / 'sonuc.json'
            life_data = json.loads(life_path.read_text(encoding='utf-8'))
            life_data['observed']['close']['status'] = 'KAPANMADI'
            life_data['observed']['close']['exited'] = False
            life_path.write_text(json.dumps(life_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('başlangıç modu' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)

    def test_ui_gozlem_error_and_cleanup_error_fails_verification(self):
        """UI gozlem.error ve gozlem.cleanup_error doluyken GECTI (DOĞRULANDI) üretilmemeli."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            ui_data = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_data['gozlem']['error'] = 'UIA element not found'
            ui_data['gozlem']['cleanup_error'] = 'Failed to restore checkbox'
            ui_path.write_text(json.dumps(ui_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertEqual(info['badge_text'], 'KANIT DOĞRULANAMADI')
            self.assertTrue(any('gözlem hata alanı dolu' in r or 'temizleme' in r for r in info['verification_reasons']))

            html = render_html(info)
            self.assertNotIn('GECTI (DOĞRULANDI)', html)
            self.assertIn('KANIT DOĞRULANAMADI', html)


    # === GOREV-009 KANIT GÜVENLİĞİ VE RAPOR KORUMASI TESTLERİ ===

    def test_link_mandatory_fields_missing(self):
        """Köprüde test_id, run_id, status veya exit_code eksikse KANIT DOĞRULANAMADI olmalı."""
        for field in ("test_id", "run_id", "status", "exit_code"):
            with tempfile.TemporaryDirectory() as tmpdir:
                run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
                link_path = run_dir / 'pytest-link.json'
                data = json.loads(link_path.read_text(encoding='utf-8'))
                del data[field]
                link_path.write_text(json.dumps(data), encoding='utf-8')

                info = evaluate_run(run_dir)
                self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
                self.assertTrue(any(f"zorunlu alan eksik: '{field}'" in r for r in info['verification_reasons']))

    def test_link_expected_or_observed_states_missing(self):
        """Köprüde expected_states veya observed_states eksikse KANIT DOĞRULANAMADI olmalı."""
        for field in ("expected_states", "observed_states"):
            with tempfile.TemporaryDirectory() as tmpdir:
                run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
                link_path = run_dir / 'pytest-link.json'
                data = json.loads(link_path.read_text(encoding='utf-8'))
                del data[field]
                link_path.write_text(json.dumps(data), encoding='utf-8')

                info = evaluate_run(run_dir)
                self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
                self.assertTrue(any(field in r for r in info['verification_reasons']))

    def test_ui_changed_verified_false_fails_verification(self):
        """UI changed_verified=False iken başarılı test sonucu doğrulanamamalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['gozlem']['changed_verified'] = False
            ui_path.write_text(json.dumps(data), encoding='utf-8')
            (ui_dir / 'uia-adimlari.json').write_text(json.dumps(data['gozlem']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('changed_verified' in r for r in info['verification_reasons']))

    def test_ui_incomplete_phase_or_schema_fails_verification(self):
        """UI phase completed değilse veya şema sürümü geçersizse doğrulanamamalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['gozlem']['phase'] = 'in_progress'
            ui_path.write_text(json.dumps(data), encoding='utf-8')
            (ui_dir / 'uia-adimlari.json').write_text(json.dumps(data['gozlem']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('UI aşaması tamamlanmamış' in r for r in info['verification_reasons']))

    def test_closed_branch_owned_false_fails_verification(self):
        """Kapalı başlangıçta (Closed) owned=False ise KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['owned'] = False
            life_path.write_text(json.dumps(data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(data['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('süreç sahipliği zorunludur' in r for r in info['verification_reasons']))

    def test_existing_branch_owned_true_fails_verification(self):
        """Önceden açık uygulamada (Existing) owned=True ise KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Existing')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['owned'] = True
            life_path.write_text(json.dumps(data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(data['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('süreç sahiplenilemez' in r for r in info['verification_reasons']))

    def test_existing_branch_close_request_sent_fails_verification(self):
        """Önceden açık uygulamada kapatma isteği gönderildiyse (request_sent=True) doğrulanamaz."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Existing')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['close']['request_sent'] = True
            life_path.write_text(json.dumps(data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(data['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('kapatma isteği gönderilmemelidir' in r for r in info['verification_reasons']))

    def test_ui_journal_missing_or_mismatched_fails_verification(self):
        """UI günlüğü (uia-adimlari.json) eksik veya sonuc.json ile uyumsuzsa KANIT DOĞRULANAMADI olmalı."""
        # 1. Eksik jurnal
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (ui_dir / 'uia-adimlari.json').unlink()
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('uia-adimlari.json' in r and 'bulunamadı' in r for r in info['verification_reasons']))

        # 2. Uyumsuz jurnal
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            (ui_dir / 'uia-adimlari.json').write_text('{"phase": "farkli"}', encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('uia-adimlari.json' in r and 'çelişiyor' in r for r in info['verification_reasons']))

    def test_lifecycle_journal_missing_or_mismatched_fails_verification(self):
        """Yaşam döngüsü günlüğü (yasam-adimlari.json) eksik veya sonuc.json ile uyumsuzsa KANIT DOĞRULANAMADI olmalı."""
        # 1. Eksik jurnal
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            (life_dir / 'yasam-adimlari.json').unlink()
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('yasam-adimlari.json' in r and 'bulunamadı' in r for r in info['verification_reasons']))

        # 2. Uyumsuz jurnal
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            (life_dir / 'yasam-adimlari.json').write_text('{"phase": "farkli"}', encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('yasam-adimlari.json' in r and 'çelişiyor' in r for r in info['verification_reasons']))

    def test_xml_failure_with_automation_hata_classified_as_hata(self):
        """pytest.fail kaynaklı XML failure durumunda kayıtlı sonuç HATA olarak sınıflandırılmalı ve doğrulanmalı."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # XML pytest.fail nedeniyle failure içerir
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="1" name="pytest" skipped="0" tests="1" time="1.5">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="1.5">\n'
                '    <failure message="Yaşam döngüsü başarısız: Süreç başlatılamadı"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )
            # Link dürüstçe HATA durumunu ve hatayı belgeler
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'HATA'
            link_data['test'] = 'HATA'
            link_data['exit_code'] = 1
            link_data['error'] = 'Yaşam döngüsü başarısız: Süreç başlatılamadı'
            link_data.pop('ui_report', None)
            link_data.pop('lifecycle_report', None)
            link_path.write_text(json.dumps(link_data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'HATA')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'HATA (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'fail')

    def test_output_path_refuses_overwriting_raw_evidence(self):
        """--output ile verilen yol ham kanıt dosyalarını ezmeyi kesinlikle reddetmelidir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            with self.assertRaises(ValueError) as ctx1:
                generate_report(run_dir, run_dir / 'pytest-link.json')
            self.assertIn('Ham kanıt dosyası', str(ctx1.exception))

            with self.assertRaises(ValueError) as ctx2:
                generate_report(run_dir, run_dir / 'pytest.xml')
            self.assertIn('Ham kanıt dosyası', str(ctx2.exception))

            with self.assertRaises(ValueError) as ctx3:
                generate_report(run_dir, ui_dir / 'sonuc.json')
            self.assertIn('Ham kanıt dosyası', str(ctx3.exception))

    def test_output_path_refuses_non_html_extension(self):
        """--output uzantısı .html veya .htm değilse ValueError fırlatılmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            with self.assertRaises(ValueError) as ctx:
                generate_report(run_dir, run_dir / 'rapor.json')
            self.assertIn('Geçersiz rapor dosya uzantısı', str(ctx.exception))

    def test_output_path_in_different_folder_calculates_relative_links(self):
        """Çıktı klasörü kanıt klasöründen farklıysa göreli bağlantılar çıktı klasörüne göre hesaplanmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            out_file = Path(tmpdir) / 'ozet_klasor' / 'ozet.html'
            report_path, info = generate_report(run_dir, out_file)
            self.assertTrue(report_path.is_file())
            html_text = report_path.read_text(encoding='utf-8')
            # Göreli bağlantı run_dir içindeki dosyalara '../' ile gitmeli
            self.assertIn('href="../kapali/pytest.xml"', html_text)
            self.assertIn('href="../kapali/pytest-link.json"', html_text)

    def test_report_generation_does_not_modify_raw_evidence_hashes(self):
        """Rapor üretimi öncesinde ve sonrasında ham kanıtların özet değerleri (hash) değişmemelidir."""
        import hashlib
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, life_dir = build_valid_mock_run(tmpdir, branch='Closed')

            def get_all_hashes():
                h = {}
                for d in (run_dir, ui_dir, life_dir):
                    for f in d.glob('*'):
                        if f.is_file() and not f.name.endswith('.html'):
                            h[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
                return h

            before_hashes = get_all_hashes()

            # Rapor üretimi
            generate_report(run_dir)

            # Başarısız raporlama denemesi (örneğin geçersiz çıktı)
            try:
                generate_report(run_dir, run_dir / 'pytest-link.json')
            except ValueError:
                pass

            after_hashes = get_all_hashes()
            self.assertEqual(before_hashes, after_hashes)

    # === GOREV-009 TAMAMLANMA İNCELEMESİ TESTLERİ ===

    # 1. Kimlik ve bağlantı doğrulaması
    def test_link_run_id_mismatch_folder_fails_verification(self):
        """Köprü run_id klasör adıyla eşleşmiyorsa KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            data = json.loads(link_path.read_text(encoding='utf-8'))
            data['run_id'] = 'farkli_id'
            link_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('Köprü run_id' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    def test_ui_test_id_mismatch_fails_verification(self):
        """UI test_id 'CANRAT-UI-002' değilse KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['test_id'] = 'CANRAT-UI-999'
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('UI test_id' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    def test_ui_calistirma_id_mismatch_fails_verification(self):
        """UI calistirma_id kayıt klasörü adıyla eşleşmiyorsa KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            data = json.loads(ui_path.read_text(encoding='utf-8'))
            data['calistirma_id'] = 'baska_klasor_id'
            ui_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('UI calistirma_id' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    def test_lifecycle_run_id_mismatch_fails_verification(self):
        """Yaşam döngüsü run_id kayıt klasörü adıyla eşleşmiyorsa KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['run_id'] = 'baska_life_id'
            life_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('Yaşam döngüsü run_id' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    def test_lifecycle_expected_mismatch_bridge_fails_verification(self):
        """Yaşam döngüsü başlangıç modu köprü expected_branch ile eşleşmiyorsa KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['expected'] = 'Existing'
            data['observed']['expected'] = 'Existing'
            life_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('başlangıç modu' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    def test_subtest_report_path_mismatch_fails_verification(self):
        """Alt test report_path köprü ui_report ile eşleşmiyorsa KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['test']['report_path'] = 'baska/bir/sonuc.json'
            life_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('report_path' in r and 'eşleşmiyor' in r for r in info['verification_reasons']))

    # 2. Başarılı koşunun zorunlu alanları
    def test_unknown_or_empty_bridge_status_rejected(self):
        """Köprüde bilinmeyen veya boş status KANIT DOĞRULANAMADI üretmelidir."""
        for bad_status in ('', 'BILINMIYOR', 'GECTI_FAKAT_SAHTE'):
            with tempfile.TemporaryDirectory() as tmpdir:
                run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
                link_path = run_dir / 'pytest-link.json'
                data = json.loads(link_path.read_text(encoding='utf-8'))
                data['status'] = bad_status
                link_path.write_text(json.dumps(data), encoding='utf-8')

                info = evaluate_run(run_dir)
                self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
                self.assertTrue(any('status değeri' in r for r in info['verification_reasons']))

    def test_subtest_missing_or_exit_code_non_zero_fails_verification(self):
        """Alt test eksikken veya exit_code!=0 (örn. 2) iken GECTI üretilmemelidir."""
        # 1. Alt test exit_code = 2
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['test']['exit_code'] = 2
            life_path.write_text(json.dumps(data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(data['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertNotEqual(info['recorded_result'], 'GECTI')
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('çıkış kodu' in r for r in info['verification_reasons']))

        # 2. Alt test kaydı tamamen eksik
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            del data['observed']['test']
            life_path.write_text(json.dumps(data), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(data['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertNotEqual(info['recorded_result'], 'GECTI')
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('alt test' in r and 'eksik' in r for r in info['verification_reasons']))

    # 3. Yaşam döngüsü temizleme ve hata alanları
    def test_lifecycle_cleanup_error_populated_fails_verification(self):
        """observed.cleanup_error doluyken GECTI (DOĞRULANDI) üretilmemelidir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            data = json.loads(life_path.read_text(encoding='utf-8'))
            data['observed']['cleanup_error'] = 'Kapatma sırasında işlem sonlandırma hatası'
            life_path.write_text(json.dumps(data), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertNotEqual(info['recorded_result'], 'GECTI')
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('temizleme' in r for r in info['verification_reasons']))

    # 4. Gerçek yürütücü davranışı: HATA zinciri
    def test_real_runner_hata_chain_produces_hata_dogrulandi(self):
        """XML failure + köprü HATA + UI HATA + Yaşam döngüsü HATA dürüstçe HATA (DOĞRULANDI) üretmelidir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, life_dir = build_valid_mock_run(tmpdir, branch='Closed', pid=11223, ticks='639000000000123456')

            err_msg = "PowerShell UI otomasyonu hata ile bitti (kod=1): Checkbox not found"

            # 1. XML (pytest.fail çağrısı JUnit XML'de failure öğesi üretir)
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="1" name="pytest" skipped="0" tests="1" time="2.5">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="2.5">\n'
                f'    <failure message="{err_msg}"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            # 2. UI (UIA adımı toggle_attempt sırasında kopmuş, sonraki adımlar koşulamamış)
            ui_sonuc = {
                "test_id": "CANRAT-UI-002",
                "calistirma_id": ui_dir.name,
                "test_sonucu": "HATA",
                "hata": err_msg,
                "gozlem": {
                    "schema_version": 1,
                    "mode": "Exercise",
                    "phase": "toggle_attempt",
                    "process_id": 11223,
                    "process_start_ticks": "639000000000123456",
                    "initial": "Off",
                    "expected_changed": "On",
                    "changed": None,
                    "changed_verified": False,
                    "final": None,
                    "restored": False,
                    "mutation_attempted": True,
                    "cleanup_attempted": False,
                    "active_collection": False,
                    "error": err_msg,
                    "cleanup_error": None,
                    "cleanup_journal_error": None,
                    "events": [
                        {"phase": "initial_saved"},
                        {"phase": "toggle_attempt"}
                    ],
                    "guard_before": [{"toggle_state": "Off", "name": "Start", "active": False, "idle": True}],
                    "guard_after": None
                }
            }
            (ui_dir / 'sonuc.json').write_text(json.dumps(ui_sonuc, indent=2), encoding='utf-8')
            (ui_dir / 'uia-adimlari.json').write_text(json.dumps(ui_sonuc["gozlem"], indent=2), encoding='utf-8')

            # 3. Yaşam döngüsü (Alt test hata verdi, ancak süreç teardown'da başarıyla kapatıldı)
            life_sonuc = {
                "task": "GOREV-003",
                "run_id": life_dir.name,
                "expected": "Closed",
                "result": "HATA",
                "exit_code": 1,
                "error": err_msg,
                "observed": {
                    "schema_version": 1,
                    "task": "GOREV-003",
                    "expected": "Closed",
                    "owned": True,
                    "before": [],
                    "identity": {"pid": 11223, "start_ticks": "639000000000123456"},
                    "start": {"status": "BASLATILDI"},
                    "test": {
                        "status": "HATA",
                        "exit_code": 1,
                        "report_path": str(ui_dir / 'sonuc.json'),
                        "observed_identity": {"pid": 11223, "start_ticks": "639000000000123456"}
                    },
                    "close": {
                        "status": "KAPANDI",
                        "method": "CloseMainWindow",
                        "request_sent": True,
                        "exited": True,
                        "exit_code": 0
                    },
                    "error": err_msg
                }
            }
            (life_dir / 'sonuc.json').write_text(json.dumps(life_sonuc, indent=2), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(life_sonuc["observed"], indent=2), encoding='utf-8')

            # 4. Köprü (HATA durumunu dürüstçe yansıtıyor)
            link_data = {
                "task": "GOREV-005",
                "adapter": "powershell",
                "test_id": "CANRAT-UI-002",
                "run_id": run_dir.name,
                "expected_branch": "Closed",
                "expected_states": ["Off", "On", "Off"],
                "observed_states": ["Off", None, None],
                "time_utc": "2026-10-15T12:00:00+00:00",
                "duration_seconds": 2.5,
                "exit_code": 1,
                "status": "HATA",
                "error": err_msg,
                "process_id": 11223,
                "process_start_ticks": "639000000000123456",
                "start": "BASLATILDI",
                "test": "HATA",
                "close": "KAPANDI",
                "lifecycle_report": str(life_dir / 'sonuc.json'),
                "ui_report": str(ui_dir / 'sonuc.json'),
                "lifecycle_journal": str(life_dir / 'yasam-adimlari.json'),
                "ui_journal": str(ui_dir / 'uia-adimlari.json')
            }
            (run_dir / 'pytest-link.json').write_text(json.dumps(link_data, indent=2), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'HATA')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'HATA (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'fail')
            self.assertEqual(len(info['verification_reasons']), 0)

            html = render_html(info)
            self.assertIn('HATA (DOĞRULANDI)', html)
            self.assertNotIn('KANIT DOĞRULANAMADI', html)

    # === GOREV-009 İKİ GRUP DERİNLEŞTİRME TESTLERİ ===

    # Grup 1: Başarılı koşuda zorunlu alanlar: silinme, boşluk, yanlış değer ve beklenti değiştirme kontrolleri
    def test_bridge_test_id_missing_empty_or_mismatch(self):
        """Köprü test_id eksik, boş veya CANRAT-UI-002 dışındaysa KANIT DOĞRULANAMADI olmalı."""
        # 1. Silinme
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            del d['test_id']
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any("zorunlu alan eksik: 'test_id'" in r for r in info['verification_reasons']))

        # 2. Boş bırakılma
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            d['test_id'] = '   '
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any("zorunlu alan eksik: 'test_id'" in r for r in info['verification_reasons']))

        # 3. Yanlış değer
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            d['test_id'] = 'CANRAT-UI-999'
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('beklenen senaryoyla' in r for r in info['verification_reasons']))

    def test_ui_calistirma_id_missing_or_empty(self):
        """UI calistirma_id eksik veya boş olduğunda reddedilmelidir."""
        # 1. Silinme
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            d = json.loads(ui_path.read_text(encoding='utf-8'))
            del d['calistirma_id']
            ui_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('UI calistirma_id eksik veya boş' in r for r in info['verification_reasons']))

        # 2. Boş bırakılma
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            ui_path = ui_dir / 'sonuc.json'
            d = json.loads(ui_path.read_text(encoding='utf-8'))
            d['calistirma_id'] = ''
            ui_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('UI calistirma_id eksik veya boş' in r for r in info['verification_reasons']))

    def test_lifecycle_run_id_missing_or_empty(self):
        """Yaşam döngüsü run_id eksik veya boş olduğunda reddedilmelidir."""
        # 1. Silinme
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            del d['run_id']
            life_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('Yaşam döngüsü run_id eksik veya boş' in r for r in info['verification_reasons']))

        # 2. Boş bırakılma
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            d['run_id'] = '   '
            life_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('Yaşam döngüsü run_id eksik veya boş' in r for r in info['verification_reasons']))

    def test_subtest_report_path_missing_or_empty(self):
        """Alt test report_path eksik veya boş olduğunda reddedilmelidir."""
        # 1. Silinme
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            del d['observed']['test']['report_path']
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('alt test report_path eksik veya boş' in r for r in info['verification_reasons']))

        # 2. Boş bırakılma
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            d['observed']['test']['report_path'] = '  '
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('alt test report_path eksik veya boş' in r for r in info['verification_reasons']))

    def test_lifecycle_expected_top_and_observed_independent_validation(self):
        """Üst expected değerinin bulunması observed.expected kontrolünü atlatmamalıdır."""
        # 1. observed.expected eksik
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            del d['observed']['expected']
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('observed.expected değeri eksik veya boş' in r for r in info['verification_reasons']))

        # 2. Üst expected eksik
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            del d['expected']
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('üst expected değeri eksik veya boş' in r for r in info['verification_reasons']))

        # 3. Üst ile observed çelişkisi
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            d['expected'] = 'Closed'
            d['observed']['expected'] = 'Existing'
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('üst expected' in r and 'observed.expected' in r for r in info['verification_reasons']))

    def test_expected_states_rules_and_manipulation_rejected(self):
        """expected_states başlangıç -> karşıtı -> başlangıç kuralına uymalı; beklenti değiştirilerek başarı kazanılamaz."""
        # 1. Karşıt durum yok: ['Off', 'Off', 'Off']
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            d['expected_states'] = ['Off', 'Off', 'Off']
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('karşıt durum aynı olamaz' in r for r in info['verification_reasons']))

        # 2. Başlangıca geri dönüş yok: ['Off', 'On', 'On']
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            d['expected_states'] = ['Off', 'On', 'On']
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('geri dönüş içermelidir' in r for r in info['verification_reasons']))

        # 3. Gerçekleşen durumlar ile beklenen durumlar uyuşmuyor
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, _ = build_valid_mock_run(tmpdir, branch='Closed')
            link_path = run_dir / 'pytest-link.json'
            d = json.loads(link_path.read_text(encoding='utf-8'))
            d['observed_states'] = ['Off', 'Off', 'Off']
            link_path.write_text(json.dumps(d), encoding='utf-8')
            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('gözlemlenen durumlarla' in r and 'uyuşmalıdır' in r for r in info['verification_reasons']))

    # Grup 2: Uygulama başlamadan oluşan gerçek HATA
    def test_early_failure_before_process_start_produces_hata_dogrulandi(self):
        """Süreç başlamadan oluşan erken hata (identity=null, owned=False, test=CALISTIRILMADI, close=DENENMEDI) HATA (DOĞRULANDI) üretmelidir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir)
            run_dir = f / 'kapali'
            run_dir.mkdir(parents=True, exist_ok=True)
            life_dir = f / 'yasam-erken-hata'
            life_dir.mkdir(parents=True, exist_ok=True)

            err_msg = 'Kapalı başlangıç bekleniyordu; mevcut uygulamaya dokunulmadı.'

            # 1. XML (pytest.fail)
            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="1" name="pytest" skipped="0" tests="1" time="0.5">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="0.5">\n'
                f'    <failure message="Yaşam döngüsü başarısız: {err_msg}"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            # 2. Yaşam döngüsü (canrat_yasam.ps1 erken hata şeması)
            life_sonuc = {
                "schema_version": 1,
                "task": "GOREV-003",
                "run_id": life_dir.name,
                "expected": "Closed",
                "result": "HATA",
                "exit_code": 2,
                "error": err_msg,
                "observed": {
                    "schema_version": 1,
                    "task": "GOREV-003",
                    "expected": "Closed",
                    "owned": False,
                    "before": [{"pid": 9999, "start_ticks": "639000000000000000"}],
                    "identity": None,
                    "start": {"status": "BASLATILMADI"},
                    "test": {"status": "CALISTIRILMADI"},
                    "close": {"status": "DENENMEDI"},
                    "error": err_msg,
                    "cleanup_error": None
                }
            }
            (life_dir / 'sonuc.json').write_text(json.dumps(life_sonuc, indent=2), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(life_sonuc["observed"], indent=2), encoding='utf-8')

            # 3. Köprü
            link_data = {
                "task": "GOREV-005",
                "adapter": "powershell",
                "test_id": "CANRAT-UI-002",
                "run_id": run_dir.name,
                "expected_branch": "Closed",
                "expected_states": ["Off", "On", "Off"],
                "observed_states": None,
                "time_utc": "2026-10-15T12:00:00+00:00",
                "duration_seconds": 0.5,
                "exit_code": 1,
                "status": "HATA",
                "error": err_msg,
                "process_id": None,
                "process_start_ticks": None,
                "start": "BASLATILMADI",
                "test": "CALISTIRILMADI",
                "close": "DENENMEDI",
                "lifecycle_report": str(life_dir / 'sonuc.json'),
                "ui_report": None,
                "lifecycle_journal": str(life_dir / 'yasam-adimlari.json'),
                "ui_journal": None
            }
            (run_dir / 'pytest-link.json').write_text(json.dumps(link_data, indent=2), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['recorded_result'], 'HATA')
            self.assertEqual(info['verification_status'], 'DOGRULANDI')
            self.assertEqual(info['badge_text'], 'HATA (DOĞRULANDI)')
            self.assertEqual(info['badge_class'], 'fail')
            self.assertEqual(len(info['verification_reasons']), 0)

            html = render_html(info)
            self.assertIn('HATA (DOĞRULANDI)', html)
            self.assertNotIn('KANIT DOĞRULANAMADI', html)

    def test_early_failure_without_error_message_rejected(self):
        """Süreç başlatılamadı hatasında hata açıklaması (error) eksikse KANIT DOĞRULANAMADI olmalıdır."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir)
            run_dir = f / 'kapali'
            run_dir.mkdir(parents=True, exist_ok=True)
            life_dir = f / 'yasam-erken-hata'
            life_dir.mkdir(parents=True, exist_ok=True)

            (run_dir / 'pytest.xml').write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<testsuite errors="0" failures="1" name="pytest" skipped="0" tests="1" time="0.5">\n'
                '  <testcase classname="tests.desktop.test_canrat_ui_002_pytest" name="test_canrat_ui_002_via_lifecycle" time="0.5">\n'
                '    <failure message="Bilinmeyen hata"/>\n'
                '  </testcase>\n'
                '</testsuite>\n',
                encoding='utf-8'
            )

            life_sonuc = {
                "schema_version": 1,
                "task": "GOREV-003",
                "run_id": life_dir.name,
                "expected": "Closed",
                "result": "HATA",
                "exit_code": 2,
                "error": None,  # Hata mesajı yok!
                "observed": {
                    "schema_version": 1,
                    "task": "GOREV-003",
                    "expected": "Closed",
                    "owned": False,
                    "before": [],
                    "identity": None,
                    "start": {"status": "BASLATILMADI"},
                    "test": {"status": "CALISTIRILMADI"},
                    "close": {"status": "DENENMEDI"},
                    "error": None
                }
            }
            (life_dir / 'sonuc.json').write_text(json.dumps(life_sonuc, indent=2), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(life_sonuc["observed"]), encoding='utf-8')

            link_data = {
                "task": "GOREV-005",
                "adapter": "powershell",
                "test_id": "CANRAT-UI-002",
                "run_id": run_dir.name,
                "expected_branch": "Closed",
                "expected_states": ["Off", "On", "Off"],
                "observed_states": None,
                "time_utc": "2026-10-15T12:00:00+00:00",
                "duration_seconds": 0.5,
                "exit_code": 1,
                "status": "HATA",
                "error": None,  # Hata mesajı yok!
                "process_id": None,
                "process_start_ticks": None,
                "start": "BASLATILMADI",
                "test": "CALISTIRILMADI",
                "close": "DENENMEDI",
                "lifecycle_report": str(life_dir / 'sonuc.json'),
                "ui_report": None,
                "lifecycle_journal": str(life_dir / 'yasam-adimlari.json'),
                "ui_journal": None
            }
            (run_dir / 'pytest-link.json').write_text(json.dumps(link_data, indent=2), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('hata açıklaması (error) eksik' in r for r in info['verification_reasons']))

    def test_started_process_cannot_hide_missing_identity_or_close(self):
        """Gerçekte başlamış bir süreç erken hata süsü verilerek eksik kimlik veya eksik kapanış gizleyemez."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _, life_dir = build_valid_mock_run(tmpdir, branch='Closed')
            # Süreç başladı olarak kaydedilmiş ancak identity silinmiş
            life_path = life_dir / 'sonuc.json'
            d = json.loads(life_path.read_text(encoding='utf-8'))
            d['observed']['identity'] = None
            life_path.write_text(json.dumps(d), encoding='utf-8')
            (life_dir / 'yasam-adimlari.json').write_text(json.dumps(d['observed']), encoding='utf-8')

            info = evaluate_run(run_dir)
            self.assertEqual(info['verification_status'], 'DOGRULANAMADI')
            self.assertTrue(any('identity eksik' in r for r in info['verification_reasons']))


if __name__ == '__main__':
    unittest.main()



