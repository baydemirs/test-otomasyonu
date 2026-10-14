"""Synthetic UI controls; no real CanRat process is touched."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if sys.platform == 'win32':
    sys.path.insert(0, str(ROOT/'uygulama_baglantilari'))
    sys.path.insert(0, str(ROOT/'tests'))
    from canrat_pywinauto import checkbox, guard, state, unique_control
    from canrat_ui_002 import classify


class FakeControl:
    def __init__(self, automation_id, control_type, class_name, name='', toggle=0,
                 enabled=True, visible=True):
        self.element_info = type('Info', (), dict(automation_id=automation_id,
                                control_type=control_type, class_name=class_name,
                                name=name))()
        self.value = toggle
        self.enabled = enabled
        self.visible = visible

    def get_toggle_state(self):
        return self.value

    def is_enabled(self):
        return self.enabled

    def is_visible(self):
        return self.visible


class FakeWindow:
    def __init__(self, *controls):
        self.controls = controls

    def descendants(self):
        return self.controls


@unittest.skipUnless(sys.platform == 'win32', 'Windows UIA adapter only')
class PywinautoSyntheticControls(unittest.TestCase):
    def test_missing_control_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Kontrol bulunamadı'):
            checkbox(FakeWindow())

    def test_duplicate_control_is_rejected(self):
        c = FakeControl('MainWindow.centralwidget.cboxAppendRecieved', 'CheckBox', 'QCheckBox')
        with self.assertRaisesRegex(ValueError, 'sayı=2'):
            checkbox(FakeWindow(c, c))

    def test_wrong_type_and_disabled_target_are_rejected(self):
        c = FakeControl('MainWindow.centralwidget.cboxAppendRecieved', 'Button', 'QCheckBox')
        with self.assertRaisesRegex(ValueError, 'Beklenmeyen kontrol türü'):
            checkbox(FakeWindow(c))
        c = FakeControl('MainWindow.centralwidget.cboxAppendRecieved', 'CheckBox', 'QCheckBox', enabled=False)
        with self.assertRaisesRegex(ValueError, 'etkin/görünür'):
            checkbox(FakeWindow(c))

    def test_indeterminate_state_is_not_success(self):
        c = FakeControl('id', 'CheckBox', 'QCheckBox', toggle=2)
        with self.assertRaisesRegex(ValueError, 'Belirsiz ToggleState'):
            state(c)

    def test_start_is_read_only_and_mapped_as_checkbox(self):
        c = FakeControl('MainWindow.centralwidget.btnStart', 'CheckBox', 'QPushButton', 'Start')
        self.assertTrue(guard(FakeWindow(c))['idle'])
        self.assertEqual(c.value, 0)

    def test_error_and_cleanup_failure_never_pass(self):
        observed = {'schema_version': 1, 'guard_before': [{'toggle_state': 'Off', 'name': 'Start', 'idle': True}] * 2,
                    'guard_after': {'toggle_state': 'Off', 'name': 'Start', 'idle': True},
                    'initial': 'Off', 'expected_changed': 'On', 'changed': 'On', 'final': 'Off',
                    'changed_verified': True, 'mutation_attempted': True, 'restored': True}
        self.assertEqual(classify(observed, 'Exercise', 0), 'GECTI')
        self.assertEqual(classify({**observed, 'error': 'sentetik UI hatası'}, 'Exercise', 0), 'HATA')
        self.assertEqual(classify({**observed, 'cleanup_error': 'sentetik geri yükleme hatası'}, 'Exercise', 0), 'HATA')


if __name__ == '__main__':
    unittest.main()
