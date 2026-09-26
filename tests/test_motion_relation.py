"""Motion is a declared movement, not a dependency; test bounded geometry."""
from pathlib import Path
import copy, sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from make_examples import Scene
from figure_core import validate_spec
from semantic_audit import audit_semantics
from relation_components import branch_bus, add_component


def motion_scene():
    s=Scene('motion-demo','DEMO: the same drawer moves outward')
    s.s['items']=[]
    s.s['output'].update(width_mm=160,placement_width_mm=160,view_width=300,view_height=150)
    s.entity('closed','structure','Same drawer in original position')
    s.entity('open','structure','Same drawer after outward translation')
    s.text('title','DEMO: same drawer, new position',30,25,10)
    s.text('closed-label','Original position',65,112,7,align='center')
    s.text('open-label','New position',235,112,7,align='center')
    s.s['items'].extend([
        {'id':'before','type':'rect','x':30,'y':50,'w':70,'h':40,'entity':'closed','logical_id':'drawer','object_part':'primary','fill':'#FFFFFF','stroke':'#253B44','stroke_width':1},
        {'id':'after','type':'rect','x':200,'y':50,'w':70,'h':40,'entity':'open','logical_id':'drawer','object_part':'detail','fill':'#FFFFFF','stroke':'#253B44','stroke_width':1},
        {'id':'move-line','type':'line','points':[[105,70],[195,70]],'stroke':'#253B44','relation':'slide'},
        {'id':'move-tip','type':'polygon','points':[[195,70],[187,66],[187,74]],'fill':'#253B44','relation':'slide'}])
    s.s['relations']=[{'id':'slide','from':'closed','to':'open','kind':'motion','meaning':'Same drawer translated outward; arrow is not data flow',
        'geometry':{'item_id':'move-line','from':[105,70],'to':[195,70],'arrow':{'item_id':'move-tip','tip':[195,70],'base':[187,70]}}}]
    return s.s


class MotionRelations(unittest.TestCase):
    def test_correct_motion_is_renderable_and_geometry_passes(self):
        s=motion_scene();self.assertTrue(validate_spec(s));self.assertEqual(audit_semantics(s)['directed_relations'][0]['status'],'PASS')
    def test_reversed_actual_arrow_is_detected(self):
        s=motion_scene();s['items'][-1]['points']=[[179,70],[187,66],[187,74]]
        s['relations'][0]['geometry']['arrow']['tip']=[179,70]
        result=audit_semantics(s)
        self.assertEqual(result['directed_relations'][0]['status'],'FAIL')
        self.assertTrue(any(f['check']=='arrow_direction_or_geometry' for f in result['directed_relations'][0]['findings']))
        with self.assertRaises(ValueError):validate_spec(s)
    def test_missing_motion_geometry_does_not_become_pass(self):
        s=motion_scene();s['relations'][0].pop('geometry')
        self.assertEqual(audit_semantics(s)['directed_relations'][0]['status'],'REVIEW_REQUIRED')
    def test_shared_branch_integrates_with_existing_scene_validator(self):
        s=Scene('reuse-demo','Two readers share one calibration')
        for ident in ('source','a','b'):s.entity(ident,'structure',ident)
        add_component(s,branch_bus('read',source=[10,50],targets=[[80,20],[80,90]],junction_x=40,
            source_entity='source',target_entities=['a','b'],meaning='Read the same calibration'))
        self.assertTrue(validate_spec(s.s))
        self.assertTrue(all(r['status']=='PASS' for r in audit_semantics(s.s)['directed_relations']))
    def test_undirected_shared_association_integrates_without_requiring_arrow(self):
        s=Scene('association-demo','Two readers refer to one calibration')
        for ident in ('source','a','b'):s.entity(ident,'structure',ident)
        add_component(s,branch_bus('refer',source=[10,50],targets=[[80,20],[80,90]],junction_x=40,
            source_entity='source',target_entities=['a','b'],meaning='Both refer to the same calibration',arrowheads=False))
        self.assertTrue(validate_spec(s.s))
        self.assertTrue(all(r['status']=='PASS' for r in audit_semantics(s.s)['directed_relations']))

if __name__=='__main__':unittest.main()
