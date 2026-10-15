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
            "final": "Off",
            "restored": True,
            "guard_before": [{"toggle_state": "Off", "name": "Start", "active": False, "idle": True}],
            "guard_after": {"toggle_state": "Off", "name": "Start", "active": False, "idle": True}
        }
    }
    (ui_dir / 'sonuc.json').write_text(json.dumps(ui_sonuc, indent=2), encoding='utf-8')
    (ui_dir / 'uia-adimlari.json').write_text('{"phase":"completed"}', encoding='utf-8')

    # 3. Yaşam döngüsü sonuc.json
    close_obj = (
        {"status": "ACIK_BIRAKILDI", "request_sent": False, "still_running": True}
        if branch == 'Existing' else
        {"status": "KAPANDI", "method": "CloseMainWindow", "exited": True, "exit_code": 0}
    )
    life_sonuc = {
        "task": "GOREV-003",
        "result": "GECTI",
        "exit_code": 0,
        "observed": {
            "identity": {"pid": pid, "start_ticks": ticks},
            "start": {"status": "MEVCUDA_BAGLANILDI" if branch == 'Existing' else "BASLATILDI"},
            "test": {"status": "GECTI"},
            "close": close_obj
        }
    }
    (life_dir / 'sonuc.json').write_text(json.dumps(life_sonuc, indent=2), encoding='utf-8')
    (life_dir / 'yasam-adimlari.json').write_text('{"phase":"finished"}', encoding='utf-8')

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
            run_dir, ui_dir, _ = build_valid_mock_run(tmpdir, branch='Closed')
            # Test başarısız: kutu değişmedi (Off -> Off) ve UI dürüstçe KALDI bildirdi
            ui_path = ui_dir / 'sonuc.json'
            ui_data = json.loads(ui_path.read_text(encoding='utf-8'))
            ui_data['test_sonucu'] = 'KALDI'
            ui_data['gozlem']['changed'] = 'Off'
            ui_data['gozlem']['restored'] = False
            ui_path.write_text(json.dumps(ui_data), encoding='utf-8')

            # Link de UI ile tutarlı olarak failure yansıtıyor
            link_path = run_dir / 'pytest-link.json'
            link_data = json.loads(link_path.read_text(encoding='utf-8'))
            link_data['status'] = 'KALDI'
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
            self.assertTrue(any('UI hata alanı dolu' in r or 'test_sonucu GECTI olamaz' in r for r in info['verification_reasons']))

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


if __name__ == '__main__':
    unittest.main()

