"""Direction, label binding and input failure behavior of non-bus relations."""
from pathlib import Path
import sys,unittest,copy,importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from relation_components import relation_path,add_component
from make_examples import Scene
from semantic_audit import audit_semantics

class RelationPath(unittest.TestCase):
    def path(self,**extra):
        args=dict(semantics='data_flow',points=[[50,10],[50,50],[10,50]],
                  source_entity='a',target_entity='b',meaning='Declared fixture transfer')
        args.update(extra);return relation_path('transfer',**args)
    def test_reversed_horizontal_vertical_and_diagonal_heads_follow_final_segment(self):
        for points in ([[50,10],[50,50],[10,50]],[[10,50],[50,50],[50,10]],[[10,10],[20,10],[50,50]]):
            s=Scene('fixture','Arbitrary relation direction fixture')
            s.entity('a','input','source');s.entity('b','input','target')
            add_component(s,self.path(points=points))
            self.assertEqual(audit_semantics(s.s)['status'],'PASS')
    def test_common_reference_is_undirected_and_preserves_endpoint_order(self):
        p=self.path(semantics='common_reference',dash=[4,3])
        self.assertEqual(p['relations'][0]['kind'],'reference')
        self.assertFalse(any(x['type']=='polygon' for x in p['items']))
        self.assertEqual(p['anchors'],{'source':[50,10],'target':[10,50]})
    def test_mapping_and_motion_are_not_merged_into_flow(self):
        for semantic,kind in [('value_mapping','mapping'),('motion','motion')]:
            self.assertEqual(self.path(semantics=semantic)['relations'][0]['kind'],kind)
    def test_label_follows_bound_segment_after_reroute(self):
        label={'text':'Write','segment':1,'fraction':.25,'offset':[0,-8],'size':18}
        before=copy.deepcopy(label)
        a=self.path(label=label);b=self.path(points=[[80,10],[80,80],[40,80]],label=label)
        ta,tb=a['items'][-1],b['items'][-1]
        self.assertEqual((ta['x'],ta['y']),(40,42));self.assertEqual((tb['x'],tb['y']),(70,72))
        self.assertEqual(ta['relation'],'transfer');self.assertEqual(label,before)
    def test_missing_or_unknown_semantics_is_rejected(self):
        with self.assertRaises(TypeError):relation_path('x',points=[])
        for semantic in (None,'reference','unknown'):
            with self.assertRaises(ValueError):self.path(semantics=semantic)
    def test_invalid_paths_fail_without_silent_repair(self):
        for points in ([],[[0,0]],[[0,0],[0,0]],[[0,0],[float('nan'),2]],[[0,0],[True,2]],[[0,0],[1,1]]):
            with self.subTest(points=points),self.assertRaises(ValueError):self.path(points=points)
    def test_bad_label_bindings_and_styles_fail(self):
        for label in ({'text':'x','segment':2},{'text':'x','fraction':1.1},{'text':'x','offset':[1]},
                      {'text':'x','offset':[True,2]},{'text':''},{'text':'x','size':0},
                      {'text':'x','leading':-1},{'text':'x','align':'diagonal'},{'text':'x','typo':1}):
            with self.subTest(label=label),self.assertRaises(ValueError):self.path(label=label)
        for options in ({'width':0},{'head':-1},{'dash':[]},{'dash':[1,0]},{'meaning':' '}):
            with self.subTest(options=options),self.assertRaises(ValueError):self.path(**options)
    def test_development_builder_uses_bound_relations_in_both_layouts(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('camera_dev',root/'examples/common-reference-demo/dev/build.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for variant in ('rows','columns'):
            scene=module.make_scene(root,root/'examples/common-reference-demo/input/figure-task.md',variant).s
            self.assertEqual(len(scene['relation_components']),4)
            self.assertEqual({c['kind'] for c in scene['relation_components']},{'relation_path'})
            self.assertEqual(sum(x['type']=='text' and 'relation_label_binding' in x for x in scene['items']),4)
            self.assertEqual(audit_semantics(scene)['status'],'PASS')

if __name__=='__main__':unittest.main()
