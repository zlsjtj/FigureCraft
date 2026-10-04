"""Two contact-first design hypotheses, from the locked synthetic geometry.

The assembly renderer is the preserved, verified-occlusion original.  Its
world geometry and painter order are unchanged; only a uniform page transform
is applied. Side diagrams are true x/z projections of the same record.
"""
from pathlib import Path
import argparse, csv, copy, hashlib, json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageOps
from pypdf import PdfReader
import native_geometry as g

C=g.C

def assembly(sc,scale,dx,dy):
    src=g.Scene(); g.main_base(src)
    th=math.acos((60**2+75**2-70**2)/(2*60*75))
    px,pz=g.panel(src,th); g.stay(src,px,pz,75,'final')
    for it in src.items:
        q=copy.deepcopy(it);q['id']='assembly-'+q['id'];q['role']='assembly-'+q['role']
        if 'pts' in q:q['pts']=[(x*scale+dx,y*scale+dy) for x,y in q['pts']]
        if 'x' in q:q['x']=q['x']*scale+dx;q['y']=q['y']*scale+dy
        if 'r' in q:q['r']*=scale
        q['width']*=scale
        sc.items.append(q)
    return lambda x,y,z:(g.project(x,y,z)[0]*scale+dx,g.project(x,y,z)[1]*scale+dy)

def base2(sc,p,lo=-10,hi=130,grooves=(50,75,100),role='side-base'):
    pts=[p(lo,0)]
    for d in grooves:
        pts += [p(d+2*math.cos(t),2*math.sin(t)) for t in np.linspace(math.pi,2*math.pi,33)]
    pts += [p(hi,0),p(hi,-8),p(lo,-8)]
    sc.poly(pts,C['base_front'],C['quiet'],.18,role)

def rod(sc,p,px,pz,qx,qz,width=2,fill=None,role='side-stay'):
    nx,nz=-(qz-pz)/70,(qx-px)/70
    off=width/2
    sc.poly([p(px-nx*off,pz-nz*off),p(qx-nx*off,qz-nz*off),p(qx+nx*off,qz+nz*off),p(px+nx*off,pz+nz*off)],fill or C['stay'],C['stay_side'],.16,role)

def projection(sc,row,p,k,withbase=True,ghost=False):
    if withbase:base2(sc,p)
    ident=row['case_id'];px,pz=float(row['P_x_mm']),float(row['P_z_mm']);qx,qz=float(row['Q_x_mm']),float(row['Q_z_mm']);tx,tz=float(row['T_x_mm']),float(row['T_z_mm'])
    th=math.radians(float(row['panel_angle_deg']));nx,nz=-math.sin(th),math.cos(th)
    fill='#DFEBE9' if ghost else C['panel']
    sc.poly([p(-1.5*nx,-1.5*nz),p(tx-1.5*nx,tz-1.5*nz),p(tx+1.5*nx,tz+1.5*nz),p(1.5*nx,1.5*nz)],fill,C['panel_edge'],.19,ident+'-panel')
    rod(sc,p,px,pz,qx,qz,fill='#E4C49E' if ghost else C['stay'],role=ident+'-stay')
    sc.circle(*p(qx,qz),2*k,C['stay'],C['stay_side'],.18,ident+'-foot')
    for x,z in [(0,0),(px,pz)]:sc.circle(*p(x,z),max(.48,.9*k),'#FFFFFF',C['ink'],.18,ident+'-permanent-joint')

def detail(sc,refined=False):
    # Genuine section in the stay centre plane y=-36, not a transparent shell.
    # Bounds x=60..90, z=-8..14 are explicit in the source/caption.
    k=1.10;p=lambda x,z:(123+k*(x-75),25-k*z)
    base2(sc,p,60,90,(75,),'detail-base-section')
    # Clip to the section's top z=14, with the real S2 stay direction.
    px,pz=28.8333333333333,52.617857211205
    x=75+(px-75)*14/pz
    # Width normal uses the full source length; clipped segment is not a new rod.
    nx,nz=pz/70,(75-px)/70
    pts=[p(x-nx,14-nz),p(75-nx,-nz),p(75+nx,nz),p(x+nx,14+nz)]
    sc.poly(pts,'#EDBD83',C['stay_side'],.22,'detail-stay-section')
    sc.circle(*p(75,0),2*k,C['stay'],C['stay_side'],.22,'detail-integral-foot-section')
    # Section hatch marks belong only to the base material.
    for x in np.arange(61,90,4):
        sc.line([p(x,-7),p(min(x+2,90),-5)],'#91A2AB',.14,'detail-base-section-hatch')
    if refined:
        # Upward release is explicitly specified. This is only the local
        # disengagement direction, never a complete path to the shown R pose.
        sc.line([(128.5,24),(128.5,12)],C['stay_side'],.33,'upward-release-direction')
        sc.poly([(128.5,10),(127.45,12.9),(129.55,12.9)],C['stay_side'],'none',0,'upward-release-arrow')
    else:
        sc.text(146,26,'Q',9.5,True,anchor='middle')
        sc.line([(142,24.9),(126,25)],C['quiet'],.18,'detail-Q-leader')

def candidate_a(rows,refined=False):
    sc=g.Scene();sc.text(4,6,'S2 · seated',10.5,True)
    p=assembly(sc,.87,1.5,4)
    sc.text(4,18,'Panel',10)
    sc.line([(16,19.5),(27,30),p(77,0,77*math.tan(math.radians(61.278307)))],C['quiet'],.19,'panel-leader')
    # Target is inside the visible plate; it is not a new physical point.
    sc.items[-1]['pts']=[(16,19.5),(26,28),p(35,0,65)]
    sc.text(60,53,'Stay',10)
    sc.line([(62,55),(55,65),p(62,-36,14)],C['quiet'],.19,'stay-leader')
    sc.text(70,94,'Base',10)
    sc.line([(72,90.5),p(120,-28,0) if refined else p(110,-6,0)],C['quiet'],.19,'base-leader')
    hx,hy=p(0,-32,0);sc.text(hx-5,hy-1.3,'H',9.5,True)
    px,py=p(28.833333,-39,52.617857);sc.text(px-5.7,py-1.6,'P',9.5,True)
    for n,d in enumerate((50,75,100),1):
        x,y=p(d,-40,0);sc.text(x,y+5.4,'S'+str(n),8.5,anchor='middle')
    qx,qy=p(75,-36,0)
    # Source ring and no-arrow leader identify one section of the same foot.
    sc.circle(qx,qy,2.5,'none',C['quiet'],.18,'Q-detail-source')
    sc.line([(qx+2.5,qy),(87,79),(95,37),(106.5 if refined else 105,31)],C['quiet'],.15 if refined else .18,'Q-section-correspondence',dash='1.1 1.2' if refined else None)
    sc.text(105,6,'Lift-out contact' if refined else 'Foot at S2',10.5,True)
    detail(sc,refined)
    sc.text(102,44,'R · externally held',10,True)
    k=.39;p2=lambda x,z:(106+k*x,94-k*z)
    projection(sc,rows[-1],p2,k)
    sc.text(101,73,'P',9,True)
    sc.text(101,93,'H',9,True)
    qx,qz=float(rows[-1]['Q_x_mm']),25
    # Open gap is geometry; datum is a dimension, not a trajectory.
    x=142
    sc.line([(x,94),(x,94-k*23)],C['quiet'],.18,'clearance-dimension')
    sc.line([(140.7,94),(143.3,94)],C['quiet'],.18,'clearance-cap')
    sc.line([(140.7,94-k*23),(143.3,94-k*23)],C['quiet'],.18,'clearance-cap')
    if refined:
        foot_bottom=p2(qx,23)
        sc.line([foot_bottom,(140.1,foot_bottom[1])],C['quiet'],.15,'clearance-witness',dash='.55 .65')
    sc.text(144,89.8,'23 mm',8.5,role='clearance-value')
    sc.text(4,98,'Synthetic geometry · DEMO',8.3,fill=C['quiet'])
    return sc

def candidate_b(rows):
    sc=g.Scene();sc.text(4,6,'One support · four alternative poses',10.5,True)
    k=.59;p=lambda x,z:(18+k*x,88.5-k*z)
    base2(sc,p)
    # Discrete alternatives share the same datum. No motion interpolation.
    for idx in (0,2,1,3):projection(sc,rows[idx],p,k,False,idx in(0,2))
    sc.text(3,15,'R · held',9.5,True)
    sc.text(34,17,'S1',9.5,True)
    sc.text(54,26,'S2',9.5,True)
    sc.text(72,39,'S3',9.5,True)
    for n,d in enumerate((50,75,100),1):
        sc.text(*p(d,-16),'S'+str(n),8.5,anchor='middle')
    sc.text(10,88,'H',9.5,True)
    # Clearance must not be inferred only from a number.
    sc.line([(57.5,88.5),(57.5,88.5-23*k)],C['quiet'],.18,'clearance-dimension')
    for y in (88.5,88.5-23*k):sc.line([(56.2,y),(58.8,y)],C['quiet'],.18,'clearance-cap')
    sc.text(59,78.5,'23 mm',8.5)
    sc.text(103,19,'Assembly · S2',10,True)
    ap=assembly(sc,.59,103,18)
    sc.text(130,80,'Stay beside panel',9,anchor='middle')
    sc.line([(133,76),ap(62,-36,14)],C['quiet'],.18,'beside-panel-leader')
    sc.text(4,98,'Synthetic geometry · DEMO',8.3,fill=C['quiet'])
    return sc

def export(sc,out,a):
    out.mkdir(parents=True,exist_ok=False)
    # SVG supports transparent source circles; reportlab's old exporter does
    # not, so transparently outlined rings are handled in a local export shim.
    labels=export_native(sc,out,a.font,a.bold_font)
    proc=subprocess.run([str(a.pdftoppm),'-png','-singlefile','-r','300',str(out/'figure.pdf'),str(out/'figure')],capture_output=True,text=True,check=True)
    im=Image.open(out/'figure.png').convert('RGB');ImageOps.grayscale(im).save(out/'figure-grayscale.png')
    arr=np.asarray(im)/255;mat=np.array([[.367,.861,-.228],[.280,.673,.047],[-.012,.043,.969]])
    Image.fromarray(np.uint8(np.clip(arr@mat.T,0,1)*255+.5)).save(out/'figure-deuteranopia.png')
    im.resize((605,374),Image.Resampling.LANCZOS).save(out/'figure-96dpi-preview.png')
    pg=PdfReader(out/'figure.pdf').pages[0]
    checks={'physical_mm':[float(pg.mediabox.width)/g.MM,float(pg.mediabox.height)/g.MM],'png_px':im.size,'minimum_font_pt':min(z['pt'] for z in labels),'labels':labels,'text_out_of_bounds':[z for z in labels if z['bounds'][0]<0 or z['bounds'][1]<0 or z['bounds'][2]>160 or z['bounds'][3]>99],'render_returncode':proc.returncode,'text':pg.extract_text(),'bitmap_in_svg':False,'limitations':['Agent visual review only; author acceptance pending','Approximate single deuteranopia matrix; no general CVD certification','96 dpi preview has nominal physical size; display is not calibrated']}
    (out/'technical-checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    (out/'scene.json').write_text(json.dumps(sc.items,indent=2),encoding='utf-8')
    return checks

def export_native(sc,out,font,bold):
    # Draw outline ring as a polygonal closed circle, preserving editable vectors.
    sc=copy.deepcopy(sc)
    for it in sc.items:
        if it['kind']=='circle' and it['fill']=='none':
            it['kind']='polyline';it['pts']=[(it['x']+it['r']*math.cos(t),it['y']+it['r']*math.sin(t)) for t in np.linspace(0,2*math.pi,81)]
    return g.export(sc,out,font,bold)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True);ap.add_argument('--refined',action='store_true');ap.add_argument('--input',type=Path,default=Path(__file__).parent/'source-input'/'finite-record.csv');a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refusing overwrite: '+str(a.out))
    a.out.mkdir(parents=True)
    rows=list(csv.DictReader(a.input.open(encoding='utf-8')))
    variants=[('candidate-A-refined',lambda r:candidate_a(r,True))] if a.refined else [('candidate-A',candidate_a),('candidate-B',candidate_b)]
    checks={name:export(fn(rows),a.out/name,a) for name,fn in variants}
    receipt={'command':sys.argv,'python':sys.version,'source_sha256':{p.name:g.sha(p) for p in (Path(__file__),Path(__file__).with_name('native_geometry.py'),a.input)},'checks':{n:{k:v for k,v in c.items() if k in ('physical_mm','minimum_font_pt','text_out_of_bounds')} for n,c in checks.items()}}
    (a.out/'rebuild-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt['checks']))
if __name__=='__main__':main()
