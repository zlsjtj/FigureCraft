"""Six particles, two support layers, one repeated P6; original structural DEMO.

Cap geometry is illustrative analytic projection, not a measured 3D model.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys

def build(skill,out,baseline=None):
    sys.path.insert(0,str(skill/'scripts'))
    from make_examples import Scene
    from scene_components import (rounded_coated_particle,sliced_coated_particle,opened_coating_particle,
        layered_slab,detail_link,declare_count,declare_occlusion)
    def base(name):
        s=Scene(name,'Six coated particles on two support layers; the cut repeats the front-right P6.',390)
        s.s['output'].update(width_mm=160,placement_width_mm=160)
        s.s['reference_palette']='yellow_blue_sage'
        s.s['role_map']={'core':{'swatch':'yellow'},'coating':{'swatch':'blue'},
                         'upper':{'swatch':'lilac'},'lower':{'swatch':'sage'}}
        s.entity('particles','coating','Six intact coated particles P1 to P6; the repeated cut is the same P6.')
        s.entity('layers','lower','Two contiguous support layers.')
        s.s['locked_values']={'particles':6,'supporting_layers':2,'repeated_detail':1,'detail_source':'P6'}
        s.s['object_model']={f'P{i}':{'core':f'P{i}.core','coating':f'P{i}.coating','overview_state':'intact','core_visible_in_overview':False} for i in range(1,7)}
        s.s['evidence_status']='User-stipulated structural DEMO; no measured dimensions, transport or performance.'
        s.s['source_refs']=[{'kind':'stipulated_demo','description':'Six coated particles; two contiguous layers; one repeated P6 view.'}]
        if baseline:
            for name in ('A','B'):
                src=baseline/name/'figure_spec.json'
                s.s['source_refs'].append({'kind':'prior_demo','path':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
        s.s['forbidden_implications']=['A seventh particle','Measured dimensions','Physical 3D simulation','Transport or performance']
        s.s['depth']={'mode':'D1_analytic_vector_projection','affects_quantitative_encoding':False,'light_direction':'upper_left'}
        s.text('demo','DEMO · Not to scale',26,379,18)
        declare_count(s,'six_particles','particles',[f'P{i}' for i in range(1,7)])
        declare_count(s,'two_layers','layers',['lower-layer','upper-layer'])
        return s
    def layer(s,x,y,w,dx,dy):
        for name,yy,t,role in [('lower-layer',y+13,22,'lower'),('upper-layer',y,13,'upper')]:
            layered_slab(s,name,x=x,y=yy,width=w,depth_x=dx,depth_y=dy,thickness=t,entity='layers',role=role)
            items={p['id']:p for p in s.s['items']}
            for face in ('front','side','top'):items[name+'-'+face]['stroke_width']=.75
            items[name+'-front']['fill']='@'+role+('.fill' if role=='upper' else '.base');items[name+'-side']['fill']='@'+role+'.shadow'
        declare_occlusion(s,'lower-layer-top','upper-layer-top')
    def particles(s,pts,r):
        for i,(x,y) in enumerate(pts,1):
            s.add(f'P{i}-contact','ellipse',x=x+2,y=y+r-1,rx=r*.69,ry=r*.115,fill='#3D4955',opacity=.19,
                  entity='particles',logical_id=f'P{i}',object_part='decoration',decorative_depth=True)
            rounded_coated_particle(s,f'P{i}',x=x,y=y,radius=r,core_radius=r*.65,entity='particles',shell_role='coating',core_role='core')
            declare_occlusion(s,'upper-layer-top',f'P{i}-shell')
        x,y=pts[-1]
        s.text('P6-label','P6',x,y+6.7,19,align='center',background='@coating.fill',entity='particles',logical_id='P6',object_part='decoration')
    def label(s,ident,txt,x,y,points,align='left'):
        s.line(ident+'-leader',points,'#5F7180',1)
        s.text(ident,txt,x,y,19,align)
    a=base('material_v17_A_overview_and_section')
    a.s['layout']={'archetype':'overview_and_adjacent_oblique_section','reading_order':'six particles, selected P6, core within coating'}
    a.text('title','Six coated particles on two support layers',26,32,23)
    layer(a,39,284,330,94,-98)
    particles(a,[(138,161),(235,161),(332,161),(91,230),(191,230),(291,230)],41)
    sliced_coated_particle(a,'P6-detail',x=681,y=196,radius=108,core_radius=70.2,entity='particles',shell_role='coating',core_role='core',detail_of='P6',cut_offset=0,normal_angle_deg=48)
    detail_link(a,'same-P6','P6','P6-detail',[[332,230],[500,230],[575.4,218.5]],'#6A7C8B')
    a.text('detail-name','P6 · oblique section',681,65,21,align='center')
    label(a,'core-name','Core',799,195,[[721,190],[786,188]])
    label(a,'coating-name','Coating',799,256,[[743,249],[787,249]])
    label(a,'upper-name','Upper layer',324,347,[[325,291],[325,324]],'center')
    label(a,'lower-name','Lower layer',104,347,[[103,308],[103,324]],'center')
    a.text('identity','Same P6, shown in section',681,341,19,align='center')
    a.s['caption']='Structural DEMO, not to scale. Six intact coated particles rest on two contiguous support layers. The dashed, undirected line identifies the front-right P6 in a repeated oblique central section, not a seventh particle. The curved coating and flat cut face use editable 2.5D vectors. Core and coating dimensions are illustrative; the cut is not an observed fracture. No transport or performance is represented.'
    a.finish(out/'scene_A.json')
    b=base('material_v17_B_cap_section_and_context')
    b.s['layout']={'archetype':'large_cap_section_with_compact_context','reading_order':'curved coating, flat cut face, same P6 in context'}
    b.text('title','A coating opening reveals the intact core',26,32,23)
    layer(b,43,278,257,67,-75)
    particles(b,[(109,186),(182,186),(255,186),(90,240),(177,240),(264,240)],29)
    opened_coating_particle(b,'P6-detail',x=650,y=201,radius=128,core_radius=83.2,entity='particles',shell_role='coating',core_role='core',detail_of='P6',cut_offset=.15,normal_angle_deg=65)
    detail_link(b,'same-P6','P6','P6-detail',[[293,240],[479,240],[525.4,230.1]],'#6A7C8B')
    b.text('context-name','Six particles · same P6',210,107,21,align='center')
    b.text('detail-name','P6 · local cutaway',650,58,21,align='center')
    label(b,'core-name','Core',810,190,[[723,190],[797,183]])
    rim=next(i for i in b.s['items'] if i['id']=='P6-detail-cut-face')
    rim_tip=[rim['x']+rim['rx']*math.cos(math.radians(50)),rim['y']+rim['ry']*math.sin(math.radians(50))]
    label(b,'coating-name','Coating',802,290,[rim_tip,[789,283]])
    label(b,'upper-name','Upper layer',294,341,[[290,285],[290,319]],'center')
    label(b,'lower-name','Lower layer',101,341,[[101,302],[101,319]],'center')
    b.s['caption']='Structural DEMO, not to scale. The large view repeats the front-right P6 from the six-particle overview. Only an illustrative cap of the coating is removed, exposing part of the intact curved core. The flat annular coating rim and the exposed core share the same oblique plane intersection; the core remains uncut and projects in front of that rim. This is editable analytic 2.5D geometry, not physical 3D, a measured fracture or a material-performance claim. The overview retains six intact particles and two contiguous supporting layers.'
    b.finish(out/'scene_B.json')
    (out/'captions.json').write_text(json.dumps({s.s['figure_id']:{'caption':s.s['caption'],'alt_text':s.s['alt_text']} for s in (a,b)},indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--skill','--skill-dir',dest='skill',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);build(a.skill,a.out,a.baseline)
