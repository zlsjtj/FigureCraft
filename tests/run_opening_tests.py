"""Coating-only opening geometry and corruption controls; no aesthetic score."""
from pathlib import Path
import argparse,copy,json,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from make_examples import Scene
from scene_components import opened_coating_particle,rounded_coated_particle,declare_count,audit_components
from figure_core import validate_spec,geometry_payload

def make():
    s=Scene('opening_test','One repeated coating opening leaves its core intact.',350)
    s.s['role_map']={'shell':{'base':'#70A2E1'},'core':{'base':'#F0E36E'}};s.entity('p','shell','One original coated particle')
    rounded_coated_particle(s,'p',x=100,y=110,radius=40,core_radius=26,entity='p',shell_role='shell',core_role='core')
    opened_coating_particle(s,'d',x=400,y=160,radius=100,core_radius=65,entity='p',shell_role='shell',core_role='core',detail_of='p')
    declare_count(s,'one','p',['p']);return s.s

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
    def check(name,ok,detail=None):rows.append(dict(name=name,passed=bool(ok),detail=detail))
    def item(s,id):return next(i for i in s['items'] if i['id']==id)
    s=make();check('intact_core_opening_preserves_one_primary',validate_spec(s))
    core=item(s,'d-core');rim=item(s,'d-cut-face');commands=core['commands'];r=65;th=math.radians(65);d=15
    # The core outline begins at the sphere/plane tangency on the sphere
    # silhouette, independently computed from x = d/sin(theta).
    sx,sy=commands[0][1:]
    check('core_cap_starts_at_shared_plane_sphere_intersection',abs(sx-400-d/math.sin(th))<1e-10 and abs((sx-400)**2+(sy-160)**2-r*r)<1e-9)
    endpoints=[c[-2:] for c in commands if c[0]=='C']
    check('curved_core_projects_in_front_of_rim',max(x for x,y in endpoints)>rim['x']+rim['rx']+5)
    check('coating_rim_flat_core_curved',not rim.get('fill_gradient') and core.get('fill_gradient',{}).get('kind')=='radial' and core['type']=='path')
    for name,mutation in [
        ('core_cut_state',lambda t:t['component_constraints'][-1].update(core_state='cut')),
        ('coating_intact_state',lambda t:t['component_constraints'][-1].update(coating_state='intact')),
        ('floating_core',lambda t:item(t,'d-core')['commands'][0].__setitem__(1,sx+5)),
        ('gradient_on_flat_rim',lambda t:item(t,'d-cut-face').update(fill_gradient=item(t,'d-core')['fill_gradient'])),
        ('core_replaced_by_flat_ellipse',lambda t:item(t,'d-core').update(type='ellipse',x=400,y=160,rx=35,ry=65)),
        ('opening_direction_changed_without_geometry',lambda t:t['component_constraints'][-1]['geometry'].update(face_direction='left'))]:
        t=copy.deepcopy(s);mutation(t);check(name+'_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(s);ix=t['items'].index(item(t,'d-core'));iy=t['items'].index(item(t,'d-cut-face'));t['items'][ix],t['items'][iy]=t['items'][iy],t['items'][ix]
    check('core_behind_rim_rejected',audit_components(t)['status']=='FAIL')
    result={'status':'PASS' if all(r['passed'] for r in rows) else 'FAIL','count':len(rows),'tests':rows,'visual_quality':'NOT_TESTED','author_acceptance':False}
    (a.out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return int(result['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
