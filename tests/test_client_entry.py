"""宿主入口、相对任务与包隔离回归；不冒充客户端生成。"""
import importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location('entry_'+name,ROOT/'scripts'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
class ClientEntry(unittest.TestCase):
    def test_plugin_points_to_single_canonical_skill(self):
        manifest=json.loads((ROOT/'.claude-plugin/plugin.json').read_text('utf-8'))
        market=json.loads((ROOT/'.claude-plugin/marketplace.json').read_text('utf-8'))
        self.assertEqual(manifest['skills'],['./'])
        self.assertEqual(manifest['name'],market['plugins'][0]['name'])
        self.assertEqual(market['plugins'][0]['source'],'./')
        self.assertNotIn('hooks',manifest)
        self.assertIn(manifest['version'],(ROOT/'SKILL.md').read_text('utf-8'))
    def test_plugin_task_invokes_namespaced_entry(self):
        first=load('first_run')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'新 任务'
            r=first.prepare(out,host='claude-code',installation='plugin')
            self.assertEqual(r['installation'],'plugin')
            self.assertIn('/figurecraft:scientific-figure-studio',(out/'TASK.md').read_text('utf-8'))
            self.assertEqual(r['generation'],'NOT_RUN')
    def test_workbuddy_portable_cli_materials(self):
        first=load('first_run')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'附件 任务';first.prepare(out,host='workbuddy',portable=True)
            task=(out/'TASK.md').read_text('utf-8')
            self.assertNotIn(str(ROOT),task);self.assertNotIn(str(out),task)
            self.assertEqual(json.loads((out/'environment.json').read_text('utf-8'))['status'],'NOT_PROBED')
    def test_plugin_option_rejects_wrong_host_without_writing(self):
        first=load('first_run')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'untouched'
            with self.assertRaises(ValueError):first.prepare(out,host='workbuddy',installation='plugin')
            self.assertFalse(out.exists())
    def test_plugin_metadata_only_in_claude_code_package(self):
        builder=load('build_package')
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'packages';builder.build(ROOT,out)
            for host in builder.HOSTS:
                with zipfile.ZipFile(out/f'scientific-figure-studio-{host}.zip') as z:
                    self.assertEqual('scientific-figure-studio/.claude-plugin/plugin.json' in z.namelist(),host=='claude-code')
                    self.assertIn('scientific-figure-studio/references/host-runtime.md',z.namelist())
if __name__=='__main__':unittest.main()
