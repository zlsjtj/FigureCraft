"""Behavioral invariants for the reusable relation geometry (no rendering mocks)."""
from pathlib import Path
import sys, unittest, copy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from relation_components import sampled_pattern, branch_bus, add_component


class RelationComponents(unittest.TestCase):
    def pattern(self, values=(0,3,11,14), **kw):
        args=dict(x=20,y=50,units=4,entity='p',role='shared')
        args.update(kw)
        return sampled_pattern('p',values,**args)
    def test_nonuniform_distance_uses_values_not_index(self):
        self.assertEqual(self.pattern()['anchors'],[[20,50],[32,50],[64,50],[76,50]])
    def test_base_only_changes_results_not_geometry(self):
        a=self.pattern(labels=[2]);b=self.pattern(base=200,labels=[2],source_pattern='origin')
        self.assertEqual(a['anchors'],b['anchors'])
        self.assertEqual([p['text'] for p in b['items'] if p['type']=='text'],['211'])
        self.assertEqual(b['data']['source_pattern'],'origin')
    def test_negative_samples_and_origin_are_explicit(self):
        self.assertEqual(self.pattern((-3,0,2),base=-20)['anchors'],[[8,50],[20,50],[28,50]])
    def test_omitted_labels_do_not_omit_samples(self):
        p=self.pattern(labels=[])
        self.assertEqual(sum(i['object_part']=='primary' for i in p['items']),4)
        self.assertFalse(any(i['type']=='text' for i in p['items']))
    def test_rejects_false_scales_and_unordered_samples(self):
        for args in ({'units':0},{'units':float('nan')},{'marker':-1},{'base':float('inf')}):
            with self.subTest(args=args),self.assertRaises(ValueError): self.pattern(**args)
        for values in ([],[1,1],[1,0],[True,3]):
            with self.subTest(values=values),self.assertRaises(ValueError): self.pattern(values)
    def test_rejects_wrong_selected_indices(self):
        for labels in ([4],[-1],[1,1],[1.0]):
            with self.subTest(labels=labels),self.assertRaises(ValueError): self.pattern(labels=labels)
    def bus(self, **kw):
        args=dict(source=[10,50],targets=[[80,20],[80,90]],junction_x=40,
                  source_entity='source',target_entities=['a','b'],meaning='Read one calibration')
        args.update(kw);return branch_bus('links',**args)
    def test_one_trunk_and_both_direction_endpoints(self):
        b=self.bus()
        self.assertEqual(b['items'][1]['points'],[[40,20],[40,90]])
        heads=[i for i in b['items'] if i['type']=='polygon']
        self.assertEqual([h['points'][0] for h in heads],[[80,20],[80,90]])
        self.assertTrue(all(h['points'][1][0]<h['points'][0][0] for h in heads))
        self.assertEqual([r['from'] for r in b['relations']],['source','source'])
    def test_rejects_ambiguous_bus_geometry(self):
        for args in ({'junction_x':5},{'targets':[[41,20]]},
                     {'targets':[[80,20],[80,20]]},{'target_entities':['a']},{'meaning':''}):
            with self.subTest(args=args),self.assertRaises(ValueError): self.bus(**args)
    def test_association_has_no_hidden_arrow_and_keeps_all_endpoints(self):
        directed=self.bus();plain=self.bus(arrowheads=False)
        self.assertEqual(plain['anchors'],directed['anchors'])
        self.assertFalse(any(p['type']=='polygon' for p in plain['items']))
        self.assertEqual([p for p in directed['items'] if p['type']=='line'],plain['items'])
        for r in plain['relations']:
            self.assertFalse(r['geometry']['arrow_required'])
            self.assertNotIn('arrow',r['geometry'])
        self.assertEqual([r['to'] for r in plain['relations']],['a','b'])
    def test_rejects_ambiguous_arrow_style(self):
        for value in [None,0,1,'none']:
            with self.subTest(value=value),self.assertRaises(ValueError): self.bus(arrowheads=value)
    def test_addition_preserves_legacy_content_and_rejects_duplicates(self):
        old={'items':[{'id':'old','type':'rect','x':0}], 'relations':[], 'other':'preserve'}
        saved=copy.deepcopy(old);add_component(old,self.pattern())
        self.assertEqual(old['items'][0],saved['items'][0]);self.assertEqual(old['other'],'preserve')
        with self.assertRaises(ValueError):add_component(old,self.pattern())
    def test_components_render_as_existing_primitives(self):
        for c in (self.pattern(),self.bus()):
            self.assertTrue(all(p['type'] in ('line','rect','text','polygon') for p in c['items']))
            self.assertEqual(len({p['id'] for p in c['items']}),len(c['items']))

if __name__=='__main__':unittest.main()
