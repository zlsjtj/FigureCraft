"""One directed post-review repair; preserves the prior candidates unchanged."""
from pathlib import Path
import argparse,csv,json,math,shutil,sys
import numpy as np
from PIL import Image
import build_candidates as b
import native_geometry as g

def hatch_polygon(sc,pts,spacing=1.8):
    # Clip parallel hatching against the exact integral rod/foot section union.
    vals=[y+x for x,y in pts]
    for c in np.arange(math.floor(min(vals)/spacing)*spacing,max(vals)+spacing,spacing):
        hits=[]
        for (x1,y1),(x2,y2) in zip(pts,pts[1:]+pts[:1]):
            v1=y1+x1-c;v2=y2+x2-c
            if (v1<=0<v2) or (v2<=0<v1):
                t=v1/(v1-v2);hits.append((x1+t*(x2-x1),y1+t*(y2-y1)))
        hits.sort()
        for p,q in zip(hits[::2],hits[1::2]):
            sc.line([p,q],g.C['stay_side'],.12,'final-integral-section-hatch')

def final_scene(rows):
    sc=b.candidate_a(rows,True)
    sc.items=[it for it in sc.items if not (it['role'].startswith('detail-') or it['role'] in ('Q-detail-source','Q-section-correspondence'))]
    for it in sc.items:
        if it.get('s')=='Lift-out contact':it['s']='A · S2 section'
        if it.get('s')=='S2':it['y']+=4.0
    # Same local x/z geometry in the y=-36 plane, viewed along +y.
    k=1.10;p=lambda x,z:(123+k*(x-75),25-k*z)
    b.base2(sc,p,60,90,(75,),'final-detail-base-section')
    for x in np.arange(61,90,4):
        sc.line([p(x,-7),p(min(x+2,90),-5)],'#91A2AB',.14,'final-base-section-hatch')
    px=173/6;pz=math.sqrt(60**2-px**2)
    nx,nz=pz/70,(75-px)/70;x=75+(px-75)*14/pz
    alpha=math.atan2(pz,px-75)
    # Boundary of the union of the radius-2 foot and the width-2 stay.
    # Suppress only the internal circular seam covered by the integral strip.
    arc=[p(75+2*math.cos(t),2*math.sin(t)) for t in np.linspace(alpha+math.pi/6,alpha+11*math.pi/6,181)]
    pts=arc+[p(x+nx,14+nz),p(x-nx,14-nz)]
    sc.poly(pts,'#EDBD83',g.C['stay_side'],.22,'final-integral-foot-stay-section')
    hatch_polygon(sc,pts)
    sc.text(146,13,'View +y',8.5,anchor='end',role='final-section-view-direction')
    # Short broken section trace. Its omitted central span leaves the foot and
    # groove lip unobscured. All trace points lie in y=-36,z=0.
    ap=lambda x,y,z:(g.project(x,y,z)[0]*.87+1.5,g.project(x,y,z)[1]*.87+4)
    for a,z in [(66,70),(80,84)]:
        sc.line([ap(a,-36,0),ap(z,-36,0)],g.C['quiet'],.19,'final-section-A-trace',dash='.8 .45')
    # Grey arrow is an observation arrow parallel to projected +y, not motion.
    a=np.array(ap(85,-48,0));tip=np.array(ap(85,-36,0));u=(tip-a)/np.linalg.norm(tip-a);v=np.array([-u[1],u[0]])
    sc.line([a.tolist(),(tip-1.15*u).tolist()],g.C['quiet'],.2,'final-section-A-view-arrow-shaft')
    sc.poly([tip.tolist(),(tip-1.6*u+.48*v).tolist(),(tip-1.6*u-.48*v).tolist()],g.C['quiet'],'none',0,'final-section-A-view-arrowhead')
    sc.text(39,76.5,'A +y',9,True,role='final-section-A-identity')
    # S2 is moved below its former crowded groove-lip region; the short leader
    # starts on the front face directly beneath the unchanged groove centre.
    start=ap(75,-40,-7.5)
    sc.line([start,(start[0],86.2)],g.C['quiet'],.16,'final-S2-label-leader')
    return sc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True);ap.add_argument('--baseline-root',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).parent;rows=list(csv.DictReader((root/'source-input'/'finite-record.csv').open(encoding='utf-8')))
    sc=final_scene(rows);checks=b.export(sc,a.out,a)
    prior=json.loads((root/'selected'/'candidate-A-refined'/'scene.json').read_text());old=[z for z in prior if z['role'].startswith('assembly-')];new=json.loads(json.dumps([z for z in sc.items if z['role'].startswith('assembly-')]))
    probes=json.loads((a.baseline_root/'occlusion-probes.json').read_text());im=Image.open(a.out/'figure.png').convert('RGB');pr={}
    for key,z in probes.items():
        x,y=g.project(*z['world']);x=x*.87+1.5;y=y*.87+4
        pix=im.getpixel((round(x*im.width/160),round(y*im.height/99)));expected=z['pixels']['after-figure-v2']
        pr[key]={'world':z['world'],'pixel_rgb':pix,'expected_rgb':expected,'pass':max(abs(c-d) for c,d in zip(pix,expected))<=8}
    semantic=[]
    for r in rows:
        p=np.array([float(r['P_x_mm']),float(r['P_z_mm'])]);q=np.array([float(r['Q_x_mm']),float(r['Q_z_mm'])]);t=np.array([float(r['T_x_mm']),float(r['T_z_mm'])]);vals=[np.linalg.norm(p),np.linalg.norm(q-p),np.linalg.norm(t)]
        semantic.append({'case':r['case_id'],'lengths':vals,'pass':max(abs(c-d) for c,d in zip(vals,[60,70,120]))<1e-6 and int(r['permanent_revolute_joints'])==2 and int(r['physical_experiments'])==0 and int(r['active_foot_groove_contacts'])==(0 if r['case_id']=='R' else 1)})
    spec=json.loads((root/'figure_spec.json').read_text());spec.update(selected='selected/candidate-A-final',revision_type='one_directed_post_independent_review_repair',parent_candidate='selected/candidate-A-refined')
    spec['local_view']['in_figure_identity']='A · S2 section; View +y; short section trace and observation arrow in main assembly'
    spec['local_view']['integral_section']='Exact union boundary of the same radius-2 circle and width-2 strip; one fill and consistent clipped hatch, no internal joint seam or new gap'
    spec.pop('selected_sha256',None)
    (a.out/'figure_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    shutil.copy2(root/'source-input'/'finite-record.csv',a.out/'finite-record.csv')
    receipt={'revision_type':'directed_post_review_repair','command':sys.argv,'source_sha256':{p.name:g.sha(p) for p in [Path(__file__),root/'build_candidates.py',root/'native_geometry.py',root/'source-input'/'finite-record.csv']},'main_assembly_byte_equal_scene':old==new,'occlusion_probes':pr,'all_five_probes_match':all(z['pass'] for z in pr.values()),'four_state_checks':semantic,'all_four_states_pass':all(z['pass'] for z in semantic),'physical_mm':checks['physical_mm'],'min_font_pt':checks['minimum_font_pt'],'text_out_of_bounds':checks['text_out_of_bounds'],'independent_review_of_this_revision':'NOT_RUN','author_acceptance':False}
    (a.out/'validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['main_assembly_byte_equal_scene','all_five_probes_match','all_four_states_pass','physical_mm','min_font_pt','text_out_of_bounds']}))
if __name__=='__main__':main()
