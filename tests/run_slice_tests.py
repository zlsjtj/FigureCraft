"""Analytic cut geometry and meaningful corruptions, not an aesthetic scorer."""
from pathlib import Path
import argparse,copy,json,math,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from make_examples import Scene
from scene_components import sliced_coated_particle,rounded_coated_particle,declare_count,audit_components,_slice_geometry
from figure_core import validate_spec,export_scene,fonts

def scene():
    s=Scene('slice_test','One original particle and its repeated cap section.',350)
    s.s['role_map']={'shell':{'base':'#70A2E1'},'core':{'base':'#F0E36E'}}
    s.entity('p','shell','One coated particle')
    rounded_coated_particle(s,'p',x=100,y=120,radius=40,core_radius=26,entity='p',shell_role='shell',core_role='core')
    sliced_coated_particle(s,'d',x=400,y=160,radius=90,core_radius=58.5,entity='p',shell_role='shell',core_role='core',detail_of='p',cut_offset=.36,normal_angle_deg=54)
    declare_count(s,'one_particle','p',['p'])
    return s.s

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--font',required=True,type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    records=[]
    def check(name,ok,detail=None):records.append(dict(name=name,passed=bool(ok),detail=detail))
    def item(s,id):return next(i for i in s['items'] if i['id']==id)
    def reject(fn):
        try:fn();return False
        except (ValueError,KeyError):return True
    s=scene();check('source_plus_detail_not_two_particles',validate_spec(s))
    # Independent 3D point construction checks the 2D projection; it does not
    # call the outline generator to compute the expected face coordinates.
    maximum_error=0;minimum_margin=1e9
    for angle in (20,37,54,70):
        for offset in (0,.18,.36,.6):
            r,cr=90,58.5;th=math.radians(angle);d=offset*r
            g=_slice_geometry(400,160,r,cr,offset,angle,'right')
            for rad,key in ((r,'cut_face'),(cr,'core_face')):
                rho=math.sqrt(rad*rad-d*d)
                for j in range(361):
                    t=math.radians(j)
                    px=d*math.sin(th)+rho*math.cos(th)*math.cos(t)
                    py=rho*math.sin(t)
                    pz=d*math.cos(th)-rho*math.sin(th)*math.cos(t)
                    face=g[key]
                    maximum_error=max(maximum_error,abs(px+400-(face['x']+face['rx']*math.cos(t))),abs(py+160-(face['y']+face['ry']*math.sin(t))),abs(px*px+py*py+pz*pz-rad*rad),abs(math.sin(th)*px+math.cos(th)*pz-d))
                    minimum_margin=min(minimum_margin,r*r-px*px-py*py)
    check('projected_faces_lie_on_sphere_and_same_cut_plane',maximum_error<1e-9,{'max_error':maximum_error,'angles_degrees':[20,37,54,70],'offset_fraction':[0,.18,.36,.6]})
    check('cut_faces_stay_inside_projected_original_sphere',minimum_margin>=-1e-9,minimum_margin)
    right=_slice_geometry(400,160,90,58.5,.36,54,'right');left=_slice_geometry(400,160,90,58.5,.36,54,'left')
    check('left_facing_projection_mirrors_right_face',abs(left['cut_face']['x']+right['cut_face']['x']-800)<1e-12 and left['cut_face']['rx']==right['cut_face']['rx'])
    check('off_center_core_cut_radius_is_recomputed',abs(right['core_face']['ry']-58.5)>1 and abs(right['core_face']['ry']-math.sqrt(58.5**2-(.36*90)**2))<1e-12)
    for name,change in [
        ('disconnected_outer_silhouette',lambda t:item(t,'d-shell')['commands'][0].__setitem__(1,item(t,'d-shell')['commands'][0][1]+2)),
        ('shifted_core_plane',lambda t:item(t,'d-core').update(x=item(t,'d-core')['x']+2)),
        ('copied_sphere_radius_into_cut_face',lambda t:item(t,'d-core').update(ry=58.5)),
        ('curved_highlight_on_flat_plane',lambda t:item(t,'d-cut-face').update(fill_gradient=item(t,'p-shell')['fill_gradient'])),
        ('duplicate_detail_counted_as_new_particle',lambda t:item(t,'d-shell').update(object_part='primary')),
        ('detached_part_identity',lambda t:item(t,'d-core').update(logical_id='seventh')),
        ('cut_geometry_declaration_changed_without_redrawing',lambda t:t['component_constraints'][-1]['geometry'].update(cut_offset=.2))]:
        t=copy.deepcopy(s);change(t);check(name+'_rejected',audit_components(t)['status']=='FAIL')
    t=copy.deepcopy(s);core=item(t,'d-core');t['items'].remove(core);t['items'].insert(t['items'].index(item(t,'d-cut-face')),core)
    check('core_occluded_by_cut_plane_order_rejected',audit_components(t)['status']=='FAIL')
    for label,args in [('offset_misses_core',(400,160,90,58.5,.7,54,'right')),('negative_offset',(400,160,90,58.5,-.2,54,'right')),('nonfinite_angle',(400,160,90,58.5,.36,float('nan'),'right')),('unsupported_direction',(400,160,90,58.5,.36,54,'up'))]:
        check(label+'_rejected',reject(lambda args=args:_slice_geometry(*args)))
    check('source_radius_ratio_change_rejected',reject(lambda:sliced_coated_particle(s,'bad',x=700,y=170,radius=90,core_radius=50,entity='p',shell_role='shell',core_role='core',detail_of='p')))
    render=a.out/'rendered';render.mkdir();library=json.loads((Path(__file__).resolve().parents[1]/'assets/reference_palettes.json').read_text(encoding='utf-8'))
    export_scene(s,render,fonts(a.font),library)
    from pypdf import PdfReader
    import xml.etree.ElementTree as ET
    svg=ET.parse(render/'figure.svg').getroot();ns='{http://www.w3.org/2000/svg}'
    cut_groups=[g for g in svg.iter(ns+'g') if g.get('id') in ('d-cut-face','d-core')]
    check('editable_svg_cut_faces_no_embedded_bitmap',len(cut_groups)==2 and all(len(list(g.iter(ns+'ellipse')))==1 for g in cut_groups) and not list(svg.iter(ns+'image')))
    check('vector_pdf_without_image_objects',not PdfReader(render/'figure.pdf').pages[0].images)
    result={'status':'PASS' if all(r['passed'] for r in records) else 'FAIL','count':len(records),'tests':records,'visual_quality':'NOT_TESTED','scientific_author_acceptance':False}
    (a.out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return int(result['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
