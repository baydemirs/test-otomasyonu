import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('registry_validator', Path(__file__).resolve().parents[2]/'otomasyon/dogrulama/demo_dogrula.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class TaskRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'durum').mkdir()
        for i in range(4):
            (self.root/f'task-{i}.md').write_text('fixture', encoding='utf-8')
        (self.root/'proof.json').write_text('{}', encoding='utf-8')
        self.tasks = [self.record(i, [] if i == 0 else [f'GOREV-{i-1:03}']) for i in range(4)]

    def record(self, i, deps):
        return f'  - id: GOREV-{i:03}\n    dosya: task-{i}.md\n    oncelik: {i}\n    durum: tamamlandi\n    bagimliliklar: [{", ".join(deps)}]\n    engel: null\n    kanitlar: [proof.json]\n'

    def validate(self):
        (self.root/'durum/gorev-durumu.yaml').write_text('surum: 1\ngorevler:\n'+''.join(self.tasks), encoding='utf-8')
        return validator.validate_tasks(self.root)

    def test_valid_fourth_task(self):
        self.assertEqual(len(self.validate()), 4)

    def test_one_task_not_bound_to_three(self):
        self.tasks = self.tasks[:1]
        self.assertEqual(len(self.validate()), 1)

    def test_duplicate_identifier(self):
        self.tasks.append(self.tasks[0])
        with self.assertRaisesRegex(ValueError, 'Yinelenen görev kimliği'):
            self.validate()

    def test_unknown_dependency(self):
        self.tasks[3] = self.record(3, ['GOREV-999'])
        with self.assertRaisesRegex(ValueError, 'Bilinmeyen bağımlılık'):
            self.validate()

    def test_self_dependency(self):
        self.tasks[3] = self.record(3, ['GOREV-003'])
        with self.assertRaisesRegex(ValueError, 'Kendine bağımlılık'):
            self.validate()

    def test_cycle(self):
        self.tasks[0] = self.record(0, ['GOREV-003'])
        with self.assertRaisesRegex(ValueError, 'Bağımlılık döngüsü'):
            self.validate()

    def test_missing_task_file(self):
        (self.root/'task-3.md').unlink()
        with self.assertRaisesRegex(ValueError, 'Görev dosyası yok'):
            self.validate()

    def test_completed_task_requires_evidence(self):
        self.tasks[3] = self.tasks[3].replace('[proof.json]', '[]')
        with self.assertRaisesRegex(ValueError, 'kanıtı boş'):
            self.validate()

    def test_missing_evidence_file(self):
        (self.root/'proof.json').unlink()
        with self.assertRaisesRegex(ValueError, 'kanıt dosyası yok'):
            self.validate()

    def test_duplicate_field_rejected(self):
        self.tasks[3] += '    durum: hazir\n'
        with self.assertRaisesRegex(ValueError, 'Yinelenen görev alanı'):
            self.validate()

    def test_project_escape_rejected(self):
        self.tasks[3] = self.tasks[3].replace('task-3.md', '../outside.md')
        with self.assertRaisesRegex(ValueError, 'proje dışına'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
