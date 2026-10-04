"""检查可搬移任务和实际 ZIP 内容；不把包检查当作客户端试用。"""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location('host_test_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HostPackages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.builder = load('build_package')
        cls.first = load('first_run')
        cls.out = Path(cls.temp.name) / '中文 安装包'
        cls.results = cls.builder.build(ROOT, cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_every_host_has_actual_files_and_matching_manifest(self):
        for host in self.builder.HOSTS:
            with self.subTest(host=host):
                name = self.first.DEMO['skill']
                with zipfile.ZipFile(self.out / f'{name}-{host}.zip') as z:
                    self.assertTrue(all(p.startswith(name + '/') and '..' not in p.split('/') for p in z.namelist()))
                    manifest = json.loads(z.read(name + '/package-manifest.json'))
                    for rel, hashes in manifest['files'].items():
                        self.assertEqual(self.builder.sha(z.read(name + '/' + rel)), hashes['package_sha256'])
                    self.assertIn(name + '/LICENSE', z.namelist())
                    for guide in ('README.md', 'docs/usage.md', 'docs/install.md', 'docs/first-use.md', 'docs/multihost-validation.md'):
                        self.assertIn(name + '/' + guide, z.namelist())
                    self.assertEqual(manifest['host_execution'], 'NOT_RUN_BY_PACKAGER')
                    self.assertNotIn('/.git/', '\n'.join(z.namelist()))

    def test_workbuddy_metadata_does_not_fork_body(self):
        name = self.first.DEMO['skill']
        with zipfile.ZipFile(self.out / f'{name}-claude.zip') as a, zipfile.ZipFile(self.out / f'{name}-workbuddy.zip') as b:
            baseline = a.read(name + '/SKILL.md').decode('utf-8')
            adapted = b.read(name + '/SKILL.md').decode('utf-8')
            self.assertEqual(baseline.split('---', 2)[2], adapted.split('---', 2)[2])
            self.assertIn('description_en:', adapted.split('---', 2)[1])

    def test_portable_trial_contains_only_inputs_and_no_local_machine_paths(self):
        name = self.first.DEMO['skill']
        with zipfile.ZipFile(self.out / f'{name}-first-use.zip') as z:
            prefix = name + '-try/'
            task = z.read(prefix + 'TASK.md').decode('utf-8')
            self.assertNotIn(str(ROOT), task)
            self.assertNotIn(str(self.out), task)
            self.assertNotIn('$' + name, task)
            actual = {p.split('/input/')[1] for p in z.namelist() if '/input/' in p}
            self.assertEqual(actual, set(self.first.DEMO['files']))
            self.assertEqual(json.loads(z.read(prefix + 'environment.json'))['status'], 'NOT_PROBED')

    def test_rebuild_is_identical(self):
        other = Path(self.temp.name) / 'again'
        result = self.builder.build(ROOT, other)
        self.assertEqual(self.results, result)

    def test_existing_package_directory_is_not_overwritten(self):
        before = {p.name: p.read_bytes() for p in self.out.iterdir()}
        with self.assertRaises(ValueError):
            self.builder.build(ROOT, self.out)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.iterdir()})

    def test_host_task_routes_and_old_default(self):
        for host in self.first.HOSTS:
            with self.subTest(host=host):
                out = Path(self.temp.name) / ('try-' + host)
                record = self.first.prepare(out, host=host)
                task = (out / 'TASK.md').read_text('utf-8')
                self.assertEqual(record['host'], host)
                self.assertEqual(record['generation'], 'NOT_RUN')
                if host == 'claude':
                    self.assertNotIn(str(out), task)
                elif host == 'claude-code':
                    self.assertIn('/' + self.first.DEMO['skill'], task)
                else:
                    self.assertIn(str(out / 'input'), task)
        with self.assertRaises(ValueError):
            self.first.prepare(Path(self.temp.name) / 'invalid', host='made-up')


if __name__ == '__main__':
    unittest.main()
