"""Synthetic mutations of real records; these are NOT additional UI runs."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'otomasyon/dogrulama'))
import yasam_dogrula as validator


class LifecycleEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.existing = json.loads((ROOT/'raporlar/kosular/yasam-e3da51bf022a4bf49311ac64e927c2b9/sonuc.json').read_text(encoding='utf-8'))['observed']
        cls.closed = json.loads((ROOT/'raporlar/kosular/yasam-ec0cd28b53e746119103326a7da341b6/sonuc.json').read_text(encoding='utf-8'))['observed']

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
