"""安装不完整时仍能读帮助；不能创建伪成功的输出目录。"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RenderEntryTests(unittest.TestCase):
    def run_without_packages(self, *args):
        return subprocess.run([sys.executable, '-S', str(ROOT / 'scripts/render_figure.py'), *args],
                              capture_output=True, encoding='utf-8', errors='replace')

    def test_help_without_render_dependencies(self):
        result = self.run_without_packages('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--placement-width-mm', result.stdout)

    def test_missing_dependency_reports_interpreter_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / '中文 output'
            result = self.run_without_packages('scene.json', '--out', str(out), '--font', 'font.ttf')
            self.assertEqual(result.returncode, 2)
            self.assertIn('reportlab', result.stderr)
            self.assertIn('Python:', result.stderr)
            self.assertIn('requirements-core.txt', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
