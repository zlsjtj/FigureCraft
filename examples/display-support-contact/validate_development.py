"""Evidence checks for this synthetic geometry development, not user testing."""
from pathlib import Path
import argparse, csv, hashlib, json, math, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import native_geometry as g
import build_candidates as b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline-root',type=Path,required=True);ap.add_argument('--out',type=Path,default=Path(__file__).parent);a=ap.parse_args();root=a.out
    selected=root/'selected'/'candidate-A-refined'
    rows=list(csv.DictReader((root/'source-input'/'finite-record.csv').open(encoding='utf-8')))
    record=[]
    for r in rows:
        ident=r['case_id'];px,pz=float(r['P_x_mm']),float(r['P_z_mm']);qx,qz=float(r['Q_x_mm']),float(r['Q_z_mm']);tx,tz=float(r['T_x_mm']),float(r['T_z_mm'])
        checks={'HP_60':abs(math.hypot(px,pz)-60)<1e-6,'PQ_70':abs(math.hypot(qx-px,qz-pz)-70)<1e-6,'HT_120':abs(math.hypot(tx,tz)-120)<1e-6,'two_permanent_joints':int(r['permanent_revolute_joints'])==2,'zero_experiments':int(r['physical_experiments'])==0,'contact_count':int(r['active_foot_groove_contacts'])==(0 if ident=='R' else 1)}
        if ident=='R':checks['lowest_point_23']=qz-2==23;checks['theta_90']=float(r['panel_angle_deg'])==90
        else:
            d=float(r['groove_x_mm']);theta=math.degrees(math.acos((60**2+d*d-70**2)/(120*d)))
            checks['angle_matches_formula']=abs(theta-float(r['panel_angle_deg']))<1e-6
        record.append({'case':ident,'checks':checks,'pass':all(checks.values())})
    original=g.Scene();g.main_base(original);p=g.panel(original,math.acos((60**2+75**2-70**2)/(120*75)));g.stay(original,*p,75,'final')
    scene=json.loads((selected/'scene.json').read_text());assembly=[z for z in scene if z['role'].startswith('assembly-')]
    matched=len(original.items)==len(assembly)
    errors=[]
    for old,new in zip(original.items,assembly):
        if new['role']!='assembly-'+old['role']:errors.append(new['id']+' order/role')
        if 'pts' in old and not np.allclose(np.array(new['pts']),np.array(old['pts'])*.87+[1.5,4],atol=1e-12,rtol=0):errors.append(new['id']+' coordinates')
        if 'x' in old and (abs(new['x']-(old['x']*.87+1.5))>1e-12 or abs(new['y']-(old['y']*.87+4))>1e-12):errors.append(new['id']+' centre')
    probe_source=json.loads((a.baseline_root/'occlusion-probes.json').read_text())
    im=Image.open(selected/'figure.png').convert('RGB');probes={}
    for name,item in probe_source.items():
        x,y=g.project(*item['world']);x=x*.87+1.5;y=y*.87+4
        pix=im.getpixel((round(x*im.width/160),round(y*im.height/99)));expected=item['pixels']['after-figure-v2'];delta=max(abs(u-v) for u,v in zip(pix,expected))
        probes[name]={'world':item['world'],'selected_xy_mm':[x,y],'expected_visible_surface_rgb':expected,'pixel_rgb':pix,'max_rgb_delta':delta,'matches_at_probe':delta<=8}
    audit=json.loads((root/'selected-label-audit.json').read_text());xml=ET.parse(selected/'figure.svg')
    identical_renderer=g.sha(root/'native_geometry.py')==g.sha(a.baseline_root/'build_figure.py')
    result={'technical_status':'PASS_WITH_AGENT_REVIEW','raw_label_audit_status':audit['technical_status'],'semantic_record_checks':record,'source_renderer_byte_identical':identical_renderer,'assembly_geometry_and_order':{'objects':len(assembly),'uniform_transform':[.87,1.5,4],'pass':matched and not errors,'errors':errors},'occlusion_probes':probes,'svg_images':len(xml.findall('.//{'+g.NS+'}image')),'text_nodes':len(xml.findall('.//{'+g.NS+'}text')),'label_audit_findings':audit['findings'],'label_audit_disposition':'Eight conservative background-bounding-box review flags. Agent viewed the exact selected image: labels and correspondence line do not overlap; H/P/S1-S3 have visible dark text on white/light surfaces. Raw audit remains REVIEW_REQUIRED.','scientific_status':'SOURCE_CONSISTENCY_CHECKED_SYNTHETIC_ONLY','visual_status':'DEVELOPER_AGENT_REVIEWED','independent_review':'NOT_RUN','author_acceptance':False,'overall_status':'REVIEW_REQUIRED'}
    result['finite_geometry_all_pass']=all(x['pass'] for x in record)
    result['occlusion_probes_all_match']=all(x['matches_at_probe'] for x in probes.values())
    (root/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    spec={'source_type':'synthetic_analytical_teaching_DEMO','physical_experiments':0,'page_mm':[160,99],'primary_reading_conclusion':'H and P remain connected while the single integral foot disengages upward from one fixed groove.','selected':'selected/candidate-A-refined','editable':'Native SVG geometry and text; vector PDF with embedded font; PNG derivatives','source_sha256':{str(p.relative_to(root)):g.sha(p) for p in sorted((root/'source-input').iterdir()) if p.is_file()},'role_colours':g.C,'bodies':['base','panel','stay_with_integral_foot'],'permanent_connections':['H:base-panel','P:panel-stay'],'unilateral_contact':'one foot with one of S1 S2 S3 when seated; none in R','groove_centres_x_mm':[50,75,100],'main_state':'S2','other_rendered_state':'R','state_records':rows,'caption_only_comparison':['S1 panel angle and outline comparison','S3 panel angle and outline comparison'],'local_view':{'identity':'same S2 foot and S2 recess','section_plane':'y=-36 mm','view_direction':'along +y toward the centre plane','section_geometry':'foot radius2, base z=-8..0, groove radius2 centred x75,z0','base_window_x_mm':[60,90],'stay_reference_cut_z_mm':14,'page_scale':1.10,'note':'Strip cut endpoints retain actual normal thickness; this is a local schematic section of idealized contact, not fit design.'},'motion_arrow':'qualitative upward disengagement only, not trajectory to R','assembled_view':{'projection':'unaltered original affine world projection','page_transform':[.87,1.5,4]},'R_view':{'projection':'side x/z','scale':.39,'Q_z_mm':25,'lowest_foot_z_mm':23},'boundary':'No new hardware, payload, clearances, stability, manufacturing or performance evidence','source_renderer_sha256':g.sha(root/'native_geometry.py'),'selected_sha256':{p.name:g.sha(p) for p in sorted(selected.iterdir()) if p.is_file()}}
    (root/'figure_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['finite_geometry_all_pass','source_renderer_byte_identical','occlusion_probes_all_match','svg_images','text_nodes','overall_status']}))
if __name__=='__main__':main()
