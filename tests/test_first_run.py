"""首次试用入口的文件保护与准备范围。只测准备器，不评价生成质量。"""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('first_run', ROOT / 'scripts/first_run.py')
first_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first_run)


class FirstRunTests(unittest.TestCase):
    def test_copies_only_raw_materials_with_exact_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / '中文 空格' / '初次试用'
            result = first_run.prepare(out)
            self.assertEqual(set(result['input_sha256']), set(first_run.DEMO['files']))
            self.assertEqual(result['generation'], 'NOT_RUN')
            self.assertNotIn('task.md', result['input_sha256'])
            for name, sha in result['input_sha256'].items():
                self.assertEqual(sha, first_run.digest(out / 'input' / name))
            self.assertIn(str(out / 'input'), (out / 'TASK.md').read_text('utf-8'))
            self.assertFalse((out / 'output').exists())

    def test_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'existing'
            out.mkdir()
            marker = out / 'keep.txt'
            marker.write_bytes(b'keep')
            with self.assertRaises(ValueError):
                first_run.prepare(out)
            self.assertEqual(marker.read_bytes(), b'keep')
            self.assertEqual(list(out.iterdir()), [marker])

    def test_rejects_output_in_skill(self):
        with self.assertRaises(ValueError):
            first_run.prepare(ROOT / 'new-first-use-output')

    def test_missing_materials_do_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'incomplete'
            root.mkdir()
            out = Path(temp) / 'output'
            with self.assertRaises(ValueError):
                first_run.prepare(out, root=root)
            self.assertFalse(out.exists())

    def test_absent_dependencies_are_not_a_success_claim(self):
        with patch.object(first_run.importlib.util, 'find_spec', return_value=None):
            record = first_run.environment()
        self.assertTrue(all(value == 'NOT_FOUND' for value in record['modules'].values()))
        self.assertEqual(record['render_execution'], 'NOT_RUN')

    def test_copy_failure_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output'
            with patch.object(first_run.shutil, 'copy2', side_effect=OSError('copy failure')):
                with self.assertRaises(OSError):
                    first_run.prepare(out)
            self.assertFalse(out.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
