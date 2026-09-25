"""Focused vector-surface / section regression, not an aesthetic score."""
from pathlib import Path
import argparse,copy,json,sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from make_examples import Scene
from scene_components import rounded_coated_particle,declare_count,audit_components
from figure_core import validate_spec,geometry_payload,fonts,export_scene
from palette_tools import recolor,semantic_payload

def scene():
    s=Scene('surface_test','Constructed sphere and repeated oblique section.',300)
    s.entity('p','shell','One logical particle and its detail')
    s.s['role_map']={'shell':{'base':'#70A2E1'},'core':{'base':'#F0E36E'}}
    rounded_coated_particle(s,'p',x=100,y=100,radius=40,core_radius=26,entity='p',shell_role='shell',core_role='core')
    rounded_coated_particle(s,'d',x=300,y=110,radius=70,core_radius=45.5,entity='p',shell_role='shell',core_role='core',view='hemisphere',detail_of='p')
    declare_count(s,'one_particle','p',['p'])
    return s.s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    records=[]
    def check(name,okay,detail=None):records.append(dict(name=name,passed=bool(okay),detail=detail))
    def rejected(fn):
        try:fn();return False
        except (ValueError,KeyError):return True
    def it(s,id):return next(p for p in s['items'] if p['id']==id)
    s=scene();check('one_primary_and_repeated_section',validate_spec(s))
    t=copy.deepcopy(s);it(t,'d-core')['rx']+=1;check('cut_face_geometry_change_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(s);it(t,'d-cut-face')['fill_gradient']=it(t,'p-shell')['fill_gradient'];check('curved_shading_on_cut_face_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(s);it(t,'d-shell')['commands'][1][1]+=1;check('hemisphere_silhouette_change_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(s);it(t,'d-shell')['object_part']='primary';check('extra_primary_rejected',rejected(lambda:validate_spec(t)))
    check('ratio_change_rejected',rejected(lambda:rounded_coated_particle(s,'bad',x=500,y=100,radius=70,core_radius=35,entity='p',shell_role='shell',core_role='core',detail_of='p')))
    for label,change in [('unordered_stops',lambda g:g['stops'].__setitem__(1,[.8,'#FFFFFF'])),('nonfinite_stop',lambda g:g['stops'].__setitem__(1,[float('nan'),'#FFFFFF'])),('negative_radius',lambda g:g.update(r=-1)),('nonfinite_center',lambda g:g.update(cx=float('nan'))),('unknown_kind',lambda g:g.update(kind='conic'))]:
        t=copy.deepcopy(s);change(it(t,'p-shell')['fill_gradient']);check(label,rejected(lambda:validate_spec(t)))
    t=recolor(s,{'reference_palette':s['reference_palette'],'role_map':{'shell':{'base':'#46C1BE'},'core':{'base':'#F9B8B2'}}})
    check('recolor_keeps_semantics_and_surface_geometry',semantic_payload(s)==semantic_payload(t) and geometry_payload(s)==geometry_payload(t))
    t=copy.deepcopy(s);it(t,'p-shell')['fill_gradient']['cx']+=1;check('light_position_part_of_geometry',geometry_payload(s)!=geometry_payload(t))
    lib=json.loads((Path(__file__).resolve().parents[1]/'assets/reference_palettes.json').read_text(encoding='utf-8'))
    render=a.out/'rendered';render.mkdir();m=export_scene(s,render,fonts(a.font),lib)
    svg=ET.parse(render/'figure.svg').getroot();ns='{http://www.w3.org/2000/svg}'
    check('native_svg_gradients_and_no_raster',len(list(svg.iter(ns+'radialGradient')))==2 and not list(svg.iter(ns+'image')))
    from pypdf import PdfReader
    page=PdfReader(render/'figure.pdf').pages[0];resources=page['/Resources']
    check('native_pdf_shading_and_no_images',len(resources.get('/Shading',{}))==2 and not page.images)
    cut=scene();rounded_coated_particle(cut,'cut',x=600,y=130,radius=80,core_radius=52,entity='p',shell_role='shell',core_role='core',view='cutaway',detail_of='p')
    check('notched_cutaway_repeats_object',validate_spec(cut))
    t=copy.deepcopy(cut);it(t,'cut-lower-rim')['points'][0][0]+=2;check('cutaway_disconnected_rim_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(cut);it(t,'cut-core')['commands'][1][1]+=2;check('cutaway_wrong_core_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(cut);it(t,'cut-upper-rim')['fill_gradient']=it(t,'p-shell')['fill_gradient'];check('curved_shading_on_cut_rim_rejected',audit_components(t)['status']=='FAIL')
    out={'status':'PASS' if all(r['passed'] for r in records) else 'FAIL','count':len(records),'tests':records,'visual_quality':'NOT_TESTED','scientific_author_acceptance':False}
    (a.out/'results.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out));return int(out['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
