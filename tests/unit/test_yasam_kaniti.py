"""Sentetik fixture tabanlı yaşam döngüsü kontrolleri.

Geçmiş ham dosyalara bağımlı olmadan temiz klonlarda bağımsız çalışır.
Mevcut tüm 10 anlamsal kontrolü (sahiplik, çoklu süreç, PID yeniden kullanımı,
kapatma isteği, çalışma dizini, temizlik hatası, süreç kalıntısı, alt süreç kimliği,
eksik günlük) aynen korur.
"""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'otomasyon/dogrulama'))
import yasam_dogrula as validator


def make_mock_existing():
    exe_str = str(ROOT / 'hedef_uygulama/CANRAT_3min/CANRat.exe')
    workdir_str = str(ROOT / 'hedef_uygulama/CANRAT_3min')
    return {
        "schema_version": 1,
        "task": "GOREV-003",
        "expected": "Existing",
        "result": "GECTI",
        "error": None,
        "cleanup_error": None,
        "before": [
            {
                "pid": 18480,
                "start_ticks": "639274711768917415",
                "path": exe_str,
                "window": 263894,
            }
        ],
        "identity": {
            "pid": 18480,
            "start_ticks": "639274711768917415",
            "path": exe_str,
            "window": 263894,
        },
        "owned": False,
        "working_directory": workdir_str,
        "start": {
            "status": "MEVCUDA_BAGLANILDI",
            "exe": exe_str,
            "window": 263894,
            "window_ready": True,
        },
        "test": {
            "status": "GECTI",
            "exit_code": 0,
            "observed_identity": {
                "pid": 18480,
                "start_ticks": "639274711768917415",
            },
        },
        "close": {
            "status": "ACIK_BIRAKILDI",
            "request_sent": False,
            "still_running": True,
        },
        "after": [
            {
                "pid": 18480,
                "start_ticks": "639274711768917415",
                "path": exe_str,
                "window": 263894,
            }
        ],
        "events": [
            {"phase": "before", "time_utc": "2026-10-13T12:03:12.800000+00:00"},
            {"phase": "identity", "time_utc": "2026-10-13T12:03:12.810000+00:00"},
            {"phase": "window_ready", "time_utc": "2026-10-13T12:03:12.820000+00:00"},
            {"phase": "test_start", "time_utc": "2026-10-13T12:03:12.830000+00:00"},
            {"phase": "test_finished", "time_utc": "2026-10-13T12:03:12.840000+00:00"},
            {"phase": "finished", "time_utc": "2026-10-13T12:03:12.850000+00:00"},
        ],
    }


def make_mock_closed():
    exe_str = str(ROOT / 'hedef_uygulama/CANRAT_3min/CANRat.exe')
    workdir_str = str(ROOT / 'hedef_uygulama/CANRAT_3min')
    return {
        "schema_version": 1,
        "task": "GOREV-003",
        "expected": "Closed",
        "result": "GECTI",
        "error": None,
        "cleanup_error": None,
        "before": [],
        "identity": {
            "pid": 21568,
            "start_ticks": "639274898668202904",
            "path": exe_str,
            "window": 2033372,
        },
        "owned": True,
        "working_directory": workdir_str,
        "start": {
            "status": "BASLATILDI",
            "exe": exe_str,
            "working_directory": workdir_str,
            "window": 2033372,
            "window_ready": True,
        },
        "test": {
            "status": "GECTI",
            "exit_code": 0,
            "observed_identity": {
                "pid": 21568,
                "start_ticks": "639274898668202904",
            },
        },
        "close": {
            "status": "KAPANDI",
            "method": "CloseMainWindow",
            "request_sent": True,
            "exited": True,
            "exit_code": 0,
        },
        "after": [],
        "events": [
            {"phase": "before", "time_utc": "2026-10-13T12:04:25.570000+00:00"},
            {"phase": "launch_intent", "time_utc": "2026-10-13T12:04:25.580000+00:00"},
            {"phase": "identity", "time_utc": "2026-10-13T12:04:25.590000+00:00"},
            {"phase": "window_ready", "time_utc": "2026-10-13T12:04:25.600000+00:00"},
            {"phase": "test_start", "time_utc": "2026-10-13T12:04:25.610000+00:00"},
            {"phase": "test_finished", "time_utc": "2026-10-13T12:04:25.620000+00:00"},
            {"phase": "finished", "time_utc": "2026-10-13T12:04:25.630000+00:00"},
        ],
    }


class LifecycleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.existing = make_mock_existing()
        self.closed = make_mock_closed()

    def reject(self, source, expected, change):
        observed = copy.deepcopy(source)
        change(observed)
        with self.assertRaises(ValueError):
            validator.validate_observed(observed, expected)

    def test_real_record_shapes(self):
        validator.validate_observed(self.existing, 'Existing')
        validator.validate_observed(self.closed, 'Closed')

    def test_existing_must_not_be_owned(self):
        self.reject(self.existing, 'Existing', lambda o: o.update(owned=True))

    def test_multiple_instances_rejected(self):
        self.reject(self.existing, 'Existing', lambda o: o['before'].append(dict(o['identity'])))

    def test_reused_pid_different_start_rejected(self):
        self.reject(self.existing, 'Existing', lambda o: o['after'][0].update(start_ticks='1'))

    def test_existing_close_request_rejected(self):
        self.reject(self.existing, 'Existing', lambda o: o['close'].update(request_sent=True))

    def test_wrong_working_directory_rejected(self):
        self.reject(self.closed, 'Closed', lambda o: o['start'].update(working_directory=str(ROOT)))

    def test_cleanup_failure_rejected(self):
        self.reject(self.closed, 'Closed', lambda o: o.update(cleanup_error='timeout'))

    def test_leftover_process_rejected(self):
        self.reject(self.closed, 'Closed', lambda o: o['after'].append(dict(o['identity'])))

    def test_wrong_child_process_rejected(self):
        self.reject(self.closed, 'Closed', lambda o: o['test']['observed_identity'].update(pid=1))

    def test_partial_journal_rejected(self):
        self.reject(self.closed, 'Closed', lambda o: o['events'].pop())


if __name__ == '__main__':
    unittest.main()
