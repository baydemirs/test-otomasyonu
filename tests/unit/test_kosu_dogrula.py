"""Bağımsız tek koşu doğrulama testleri.

TemporaryDirectory içinde izole proje kökü ve sentetik dosyalarla çalışır.
Gerçek CANRat.exe ve geçmiş kayıtlar olmadan çalışabilir; kontrolleri devre dışı bırakmaz.
"""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import otomasyon.dogrulama.demo_dogrula as demo_dogrula
from otomasyon.dogrulama.ortak import digest, project_path

REAL_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = {
    'hedef_uygulama/CANRAT_3min/CANRat.exe',
    'otomasyon/yurutme/canrat_ui_002.py',
    'otomasyon/yurutme/canrat_ui_002.ps1',
    'otomasyon/baglanti/canrat_toggle.ps1',
    'gereksinimler/CANRAT-UI-002.md',
}


class SingleRunVerificationTests(unittest.TestCase):
    def setUp(self):
        # İzole geçici proje kökü oluştur
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name).resolve()

        # Gerekli sentetik proje yapısını kur
        (self.root / 'hedef_uygulama/CANRAT_3min').mkdir(parents=True, exist_ok=True)
        (self.root / 'otomasyon/yurutme').mkdir(parents=True, exist_ok=True)
        (self.root / 'otomasyon/baglanti').mkdir(parents=True, exist_ok=True)
        (self.root / 'gereksinimler').mkdir(parents=True, exist_ok=True)

        # Sentetik hedef uygulama ve yardımcı dosyalar (gerçek CANRat.exe gerektirmez)
        (self.root / 'hedef_uygulama/CANRAT_3min/CANRat.exe').write_bytes(b'SYNTHETIC CANRAT EXECUTABLE FIXTURE')
        (self.root / 'otomasyon/yurutme/canrat_ui_002.ps1').write_text('# synthetic helper', encoding='utf-8')
        (self.root / 'otomasyon/baglanti/canrat_toggle.ps1').write_text('# synthetic toggle', encoding='utf-8')
        (self.root / 'gereksinimler/CANRAT-UI-002.md').write_text('# synthetic requirements', encoding='utf-8')

        # canrat_ui_002.py dosyasını gerçek kaynaktan kopyala (classify mantığını eksiksiz kullanmak için)
        real_ui_py = REAL_ROOT / 'otomasyon/yurutme/canrat_ui_002.py'
        (self.root / 'otomasyon/yurutme/canrat_ui_002.py').write_text(real_ui_py.read_text(encoding='utf-8'), encoding='utf-8')

        # İzole koşu klasörü
        self.run_dir = self.root / 'raporlar/kosular/canrat-mock-run'
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _build_valid_run(self):
        journal_path = self.run_dir / 'uia-adimlari.json'
        sonuc_path = self.run_dir / 'sonuc.json'

        # İzole kök üzerinden gerçek digest'leri hesapla
        versions = {}
        for filename in REQUIRED_FILES:
            file_path = project_path(self.root, filename)
            versions[filename] = digest(file_path)

        guard = {'toggle_state': 'Off', 'name': 'Start', 'active': False, 'idle': True}
        observed = {
            'schema_version': 1,
            'mode': 'Exercise',
            'phase': 'completed',
            'process_id': 1234,
            'process_start_ticks': '639000000000000000',
            'initial': 'Off',
            'expected_changed': 'On',
            'changed': 'On',
            'final': 'Off',
            'restored': True,
            'cleanup_attempted': True,
            'mutation_attempted': True,
            'changed_verified': True,
            'guard_before': [guard.copy(), guard.copy()],
            'guard_after': guard.copy(),
            'events': [
                {'phase': 'initial_saved'},
                {'phase': 'toggle_attempt'},
                {'phase': 'change_observed'},
                {'phase': 'restoring'},
                {'phase': 'completed'},
            ],
        }

        relative_kanit = str(sonuc_path.relative_to(self.root)).replace('\\', '/')

        report = {
            'sema_surumu': 1,
            'gorev_id': 'GOREV-001',
            'test_id': 'CANRAT-UI-002',
            'calistirma_id': self.run_dir.name,
            'zaman_utc': datetime.now(timezone.utc).isoformat(),
            'mod': 'Exercise',
            'tur': 'GERCEK_UI_TESTI',
            'kaynak': 'gereksinimler/CANRAT-UI-002.md',
            'kanit_yolu': relative_kanit,
            'beklenen': 'Off -> On -> Off',
            'test_verisi': {'initial': 'Off'},
            'komut': 'powershell ...',
            'surumler': versions,
            'gozlem': observed,
            'komutlar': [
                {
                    'cikis_kodu': 0,
                    'sure_asimi': False,
                    'argv': ['powershell.exe', '-Journal', str(journal_path), '-Mode', 'Exercise'],
                }
            ],
            'test_sonucu': 'GECTI',
        }
        return report, observed

    def _write_run(self, report, observed):
        (self.run_dir / 'uia-adimlari.json').write_text(json.dumps(observed, indent=2), encoding='utf-8')
        sonuc_path = self.run_dir / 'sonuc.json'
        sonuc_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        return sonuc_path

    def test_valid_single_run_passes_without_historical_evidence(self):
        report, observed = self._build_valid_run()
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            demo_dogrula.check(sonuc)

    def test_missing_process_id_fails(self):
        report, observed = self._build_valid_run()
        observed['process_id'] = None
        report['gozlem'] = observed
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Hedef süreç kimliği eksik'):
                demo_dogrula.check(sonuc)

    def test_invalid_events_sequence_fails(self):
        report, observed = self._build_valid_run()
        observed['events'] = [{'phase': 'initial_saved'}, {'phase': 'completed'}]
        report['gozlem'] = observed
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Zorunlu adım günlüğü eksik veya beklenmeyen sıra'):
                demo_dogrula.check(sonuc)

    def test_version_mismatch_fails(self):
        report, observed = self._build_valid_run()
        report['surumler']['otomasyon/yurutme/canrat_ui_002.py'] = '0' * 64
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Güncel dosya koşu sürümünden farklı'):
                demo_dogrula.check(sonuc)

    def test_command_failed_exit_code_fails(self):
        report, observed = self._build_valid_run()
        report['komutlar'][0]['cikis_kodu'] = 1
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Başarılı tek test komutu kanıtı gerekli'):
                demo_dogrula.check(sonuc)

    def test_test_sonucu_not_gecti_fails(self):
        report, observed = self._build_valid_run()
        report['test_sonucu'] = 'KALDI'
        sonuc = self._write_run(report, observed)
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Başarılı demo kabul koşulları sağlanmadı'):
                demo_dogrula.check(sonuc)

    def test_journal_mismatch_fails(self):
        report, observed = self._build_valid_run()
        mutated_observed = copy.deepcopy(observed)
        mutated_observed['changed'] = 'Off'
        (self.run_dir / 'uia-adimlari.json').write_text(json.dumps(mutated_observed, indent=2), encoding='utf-8')
        sonuc_path = self.run_dir / 'sonuc.json'
        sonuc_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        with patch.object(demo_dogrula, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'UIA günlüğü ve sonuç gözlemi farklı'):
                demo_dogrula.check(sonuc_path)


if __name__ == '__main__':
    unittest.main()
