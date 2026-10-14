"""Kontrollü sahte alt süreç sonuçları; gerçek CanRat testleri değildir."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[2] / 'otomasyon' / 'inceleme' / 'canrat_incele.py'
spec = importlib.util.spec_from_file_location('canrat_incele', MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.exe = Path(self.temp.name) / 'CANRat.exe'
        self.exe.write_bytes(b'UNIT TEST FIXTURE - NOT A WINDOWS EXECUTABLE')

    def collect(self, runner):
        with patch.object(probe.shutil, 'which', return_value='powershell.exe'):
            return probe.collect(self.exe, system='Windows', runner=runner)

    def test_non_windows_never_runs_process(self):
        def forbidden(*args, **kwargs):
            self.fail('Should not run on a non-Windows host')
        result = probe.collect(self.exe, system='Linux', runner=forbidden)
        self.assertEqual(result['inceleme_durumu'], 'ENGELLENDI')
        self.assertIsNone(result['test_sonucu'])

    def test_timeout_does_not_report_success(self):
        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
        result = self.collect(timeout)
        self.assertEqual(result['inceleme_durumu'], 'ENGELLENDI')
        self.assertIsNone(result['test_sonucu'])

    def test_process_error_preserved(self):
        result = self.collect(lambda *a, **k: subprocess.CompletedProcess(a[0], 2, '', 'No matching window'))
        self.assertEqual(result['inceleme_durumu'], 'ENGELLENDI')
        self.assertEqual(result['hata'], 'No matching window')

    def test_malformed_output_is_blocked(self):
        result = self.collect(lambda *a, **k: subprocess.CompletedProcess(a[0], 0, '{}', ''))
        self.assertEqual(result['inceleme_durumu'], 'ENGELLENDI')

    def test_inventory_is_not_a_passed_test(self):
        observed = dict(schema_version=1, process_id=123, window={'name': 'fixture'},
                        controls=[{'name': 'Scan'}], truncated=False, read_errors=[])
        result = self.collect(lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(observed), ''))
        self.assertEqual(result['inceleme_durumu'], 'GOZLEM_ALINDI')
        self.assertIsNone(result['test_sonucu'])

    def test_empty_or_partial_inventory_is_blocked(self):
        for controls, errors, truncated in [([], [], False), ([{}], ['error'], False), ([{}], [], True)]:
            with self.subTest(controls=controls, errors=errors, truncated=truncated):
                data = dict(schema_version=1, process_id=123, window={}, controls=controls,
                            read_errors=errors, truncated=truncated)
                result = self.collect(lambda *a, **k: subprocess.CompletedProcess(a[0], 0, json.dumps(data), ''))
                self.assertEqual(result['inceleme_durumu'], 'ENGELLENDI')

    def test_reports_cannot_overwrite_previous_run(self):
        result = probe.collect(self.exe, system='Linux')
        first = probe.save_report(result, self.temp.name)
        original = first.read_bytes()
        with self.assertRaises(FileExistsError):
            probe.save_report(result, self.temp.name)
        self.assertEqual(original, first.read_bytes())


if __name__ == '__main__':
    unittest.main()
