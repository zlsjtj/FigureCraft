"""Geometry/binding regressions, not aesthetics or materials physics tests."""
from pathlib import Path
import argparse,copy,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scene_components import *
from semantic_audit import audit_semantics

def base():
    s={'items':[],'relations':[]}
    layered_slab(s,'lower',x=0,y=150,width=200,depth_x=40,depth_y=-40,thickness=20,entity='layers',role='base')
    layered_slab(s,'upper',x=0,y=140,width=200,depth_x=40,depth_y=-40,thickness=10,entity='layers',role='support')
    coated_particle(s,'p0',x=70,y=90,radius=40,core_radius=25,entity='particles',shell_role='shell',core_role='core',view='cutaway')
    coated_particle(s,'p1',x=115,y=120,radius=40,core_radius=25,entity='particles',shell_role='shell',core_role='core')
    coated_particle(s,'detail',x=400,y=90,radius=80,core_radius=50,entity='particles',shell_role='shell',core_role='core',view='section',detail_of='p0')
    detail_link(s,'zoom','p0','detail',[[100,80],[320,80]])
    declare_count(s,'particles','particles',['p0','p1'])
    declare_count(s,'layers','layers',['lower','upper'])
    declare_occlusion(s,'p0-shell','p1-shell')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);records=[]
    def check(name,s,expected='FAIL'):
        r=audit_semantics(s);passed=r['status']==expected
        records.append({'name':name,'expected':expected,'actual':r['status'],'passed':passed,'findings':r['findings']})
    def mutate(name,fn):
        s=base();fn(s);check(name,s)
    def item(s,id):return next(p for p in s['items'] if p['id']==id)
    check('valid_components_and_repeat_section',base(),'PASS')
    mutate('duplicate_detail_primary',lambda s:item(s,'detail-shell').update(object_part='primary'))
    mutate('wrong_detail_binding',lambda s:item(s,'detail-core').update(logical_id='p1'))
    mutate('section_radius_changed',lambda s:item(s,'detail-core').update(r=55))
    mutate('section_center_changed',lambda s:item(s,'detail-core').update(x=410))
    mutate('cutaway_core_crosses_shell',lambda s:item(s,'p0-core')['points'].__setitem__(1,[200,0]))
    mutate('slab_edge_gap',lambda s:item(s,'upper-top')['points'].__setitem__(0,[0,135]))
    mutate('face_unbound',lambda s:item(s,'upper-side').update(logical_id='lower'))
    mutate('occlusion_order_reversed',lambda s:s['occlusion_constraints'][0].update(back='p1-shell',front='p0-shell'))
    mutate('occlusion_nonoverlap',lambda s:s['occlusion_constraints'][0].update(front='detail-shell'))
    mutate('core_drawn_behind_shell',lambda s:s['items'].insert(0,s['items'].pop(next(i for i,p in enumerate(s['items']) if p['id']=='p0-core'))))
    mutate('component_part_missing',lambda s:s['items'].remove(item(s,'upper-side')))
    s={'items':[],'relations':[]}
    array_grid(s,'source',['0','1'],x=0,y=0,columns=2,entity='a',role='cell',states=[True,False])
    array_grid(s,'target',['8','9'],x=0,y=100,columns=2,entity='b',role='cell')
    index_correspondence(s,'index0','source-0','target-0',meaning='same index')
    check('array_state_and_correspondence',s,'PASS')
    t=copy.deepcopy(s);item(t,'source-1').update(fill='@cell.fill');check('array_visual_state_mismatch',t)
    t=copy.deepcopy(s);item(t,'index0')['points'].reverse();check('array_correspondence_reversed',t)
    try:
        t=base();coated_particle(t,'bad',x=500,y=90,radius=80,core_radius=40,entity='particles',shell_role='shell',core_role='core',view='section',detail_of='p0')
    except ValueError:rejected=True
    else:rejected=False
    records.append({'name':'builder_rejects_changed_detail_ratio','passed':rejected})
    result={'status':'PASS' if all(r['passed'] for r in records) else 'FAIL','count':len(records),'tests':records,
            'limits':['No automatic judgment of scientific truth, physical visibility, aesthetic quality or reader comprehension.','Placement-size negative tests remain in the existing semantic suite.']}
    (a.out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'count':len(records)}))
    if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
