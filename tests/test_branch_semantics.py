from pathlib import Path
import sys,unittest,warnings
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from relation_components import branch_bus,relation_branch,add_component
from make_examples import Scene
from figure_core import validate_spec

class BranchSemantics(unittest.TestCase):
    def branch(self,**extra):return branch_bus('b',source=[10,50],targets=[[90,20],[90,80]],junction_x=40,source_entity='s',target_entities=['a','b'],meaning='Fixture declared relation',**extra)
    def test_shared_reference_has_no_direction_cue(self):
        b=self.branch(semantics='common_reference');self.assertFalse(any(i['type']=='polygon' for i in b['items']));self.assertEqual({r['kind'] for r in b['relations']},{'reference'})
    def test_mapping_flow_motion_keep_distinct_types_and_arrows(self):
        for semantic,kind in [('value_mapping','mapping'),('data_flow','flow'),('motion','motion')]:
            b=self.branch(semantics=semantic);self.assertEqual(sum(i['type']=='polygon' for i in b['items']),2);self.assertEqual({r['kind'] for r in b['relations']},{kind})
            s=Scene('fixture','Declared relation fixture')
            for n in ['s','a','b']:s.entity(n,'structure',n)
            add_component(s,b);self.assertTrue(validate_spec(s.s))
    def test_conflicting_override_is_rejected(self):
        with self.assertRaises(ValueError):self.branch(semantics='common_reference',arrowheads=True)
        with self.assertRaises(ValueError):self.branch(semantics='motion',arrowheads=False)
    def test_legacy_keeps_geometry_with_visible_migration_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always');b=self.branch()
        self.assertEqual(sum(i['type']=='polygon' for i in b['items']),2);self.assertEqual(b['relations'][0]['kind'],'reuse');self.assertTrue(any(issubclass(x.category,DeprecationWarning) for x in w))
    def test_unknown_semantics_is_not_silently_reuse(self):
        with self.assertRaises(ValueError):self.branch(semantics='whatever')
    def test_new_call_entry_requires_semantics(self):
        with self.assertRaises(TypeError):relation_branch('new')
        with self.assertRaises(ValueError):relation_branch('new',semantics=None)
        b=relation_branch('new',semantics='common_reference',source=[10,50],targets=[[90,20],[90,80]],junction_x=40,source_entity='s',target_entities=['a','b'],meaning='One shared reference')
        self.assertFalse(any(x['type']=='polygon' for x in b['items']))
if __name__=='__main__':unittest.main()
