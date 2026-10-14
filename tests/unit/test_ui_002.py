"""Sahte gözlemler: ürün testi değil, hatalı başarı kararına karşı kontroller."""
import copy
import importlib.util
from pathlib import Path
import unittest
import contextlib
import io
import json
import subprocess
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('ui002', Path(__file__).resolve().parents[2]/'otomasyon/yurutme/canrat_ui_002.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VerdictTests(unittest.TestCase):
    def setUp(self):
        guard = dict(toggle_state='Off', name='Start', idle=True)
        self.observed = dict(schema_version=1, initial='Off', expected_changed='On', changed='On',
                             changed_verified=True, final='Off', restored=True, mutation_attempted=True,
                             guard_before=[guard.copy(), guard.copy()], guard_after=guard.copy())

    def test_both_initial_states(self):
        self.assertEqual(module.classify(self.observed, 'Exercise'), 'GECTI')
        self.observed.update(initial='On', expected_changed='Off', changed='Off', final='On')
        self.assertEqual(module.classify(self.observed, 'Exercise'), 'GECTI')

    def test_unknown_initial_or_intermediate_never_passes(self):
        for field in ('initial', 'changed', 'final'):
            for value in (None, 'Indeterminate', 'unknown'):
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(self.observed)
                    data[field] = value
                    self.assertEqual(module.classify(data, 'Exercise'), 'HATA')

    def test_restoration_failure_is_separate_and_not_passed(self):
        for patch in (dict(restored=False), dict(cleanup_error='restore failed'), dict(cleanup_journal_error='disk failed')):
            data = dict(self.observed, **patch)
            self.assertEqual(module.classify(data, 'Exercise'), 'HATA')

    def test_unchanged_checkbox_is_failed_not_passed(self):
        self.observed.update(changed='Off', changed_verified=False)
        self.assertEqual(module.classify(self.observed, 'Exercise'), 'KALDI')

    def test_unconfirmed_change_never_passes(self):
        self.observed['changed_verified'] = False
        self.assertEqual(module.classify(self.observed, 'Exercise'), 'HATA')

    def test_active_collection_skips_only_before_mutation(self):
        self.observed.update(active_collection=True, mutation_attempted=False)
        self.assertEqual(module.classify(self.observed, 'Exercise', 2), 'ATLANDI')
        self.observed['mutation_attempted'] = True
        self.observed['guard_after']['toggle_state'] = 'On'
        self.assertEqual(module.classify(self.observed, 'Exercise'), 'HATA')

    def test_stale_or_malformed_evidence_cannot_pass(self):
        for value in (None, {}, dict(self.observed, guard_after=None), dict(self.observed, guard_before=[None])):
            self.assertEqual(module.classify(value, 'Exercise'), 'HATA')
        self.assertEqual(module.classify(self.observed, 'Exercise', 1), 'HATA')

    def test_preflight_is_not_functional_pass(self):
        self.observed['mutation_attempted'] = False
        self.assertEqual(module.classify(self.observed, 'Inspect'), 'HAZIR')

    def test_timeout_recovery_never_converts_timeout_to_pass(self):
        for restored in (True, False):
            with self.subTest(restored=restored), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for filename in ['otomasyon/yurutme/canrat_ui_002.py', 'otomasyon/yurutme/canrat_ui_002.ps1',
                                 'hedef_uygulama/CANRAT_3min/CANRat.exe',
                                 'otomasyon/baglanti/canrat_toggle.ps1', 'gereksinimler/CANRAT-UI-002.md']:
                    target = root/filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('fixture', encoding='utf-8')
                calls = []

                def fake_run(command, **kwargs):
                    operation = command[command.index('-Mode') + 1]
                    journal = Path(command[command.index('-Journal') + 1])
                    calls.append(operation)
                    data = copy.deepcopy(self.observed)
                    if operation == 'Exercise':
                        data.update(restored=False, final=None, process_id=123, process_start_ticks='456')
                        journal.write_text(json.dumps(data), encoding='utf-8')
                        raise subprocess.TimeoutExpired(command, kwargs['timeout'])
                    data.update(restored=restored, final='Off' if restored else 'On', cleanup_error=None if restored else 'restore failed')
                    journal.write_text(json.dumps(data), encoding='utf-8')
                    return subprocess.CompletedProcess(command, 0 if restored else 2, '', '')

                with patch.object(module, 'ROOT', root), patch.object(module, '__file__', str(root/'otomasyon/yurutme/canrat_ui_002.py')), \
                     patch.object(module.platform, 'system', return_value='Windows'), \
                     patch.object(module.shutil, 'which', return_value='powershell.exe'), \
                     patch.object(module.subprocess, 'run', side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.run('Exercise'), 2)
                report = json.loads(next((root/'raporlar/kosular').glob('*/sonuc.json')).read_text(encoding='utf-8'))
                self.assertEqual(calls, ['Exercise', 'Recover'])
                self.assertEqual(report['test_sonucu'], 'HATA')
                self.assertEqual(report['kurtarma']['restored'], restored)
                self.assertEqual(report['geri_yukleme_hatasi'] is None, restored)


if __name__ == '__main__':
    unittest.main()
