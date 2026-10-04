"""Deterministic vector reconstruction of a synthetic, three-body geometry DEMO.
Requires reportlab, pypdf, Pillow, numpy and an explicit Poppler pdftoppm.
No measured data, simulation, external images or hidden input is used.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, subprocess, sys, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageOps
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

MM = 72 / 25.4
W, H = 160., 99.
C = dict(ink='#243B46', quiet='#667984', panel='#B8DFDA', panel_side='#74A9A5',
         panel_edge='#437D7C', stay='#DB9E56', stay_side='#AE7137', base='#E6EDF1',
         base_front='#BECCD5', base_side='#CFDBE1', groove='#849BA9', paper='#FFFFFF')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb(h): return tuple(int(h[i:i+2], 16)/255 for i in (1,3,5))
def mix(a,b,t): return '#'+''.join(f'{round((1-t)*x+t*y):02x}' for x,y in zip([int(a[i:i+2],16) for i in (1,3,5)],[int(b[i:i+2],16) for i in (1,3,5)]))

class Scene:
    def __init__(self): self.items=[]; self.serial=0
    def add(self, kind, role, **kw):
        self.serial += 1
        self.items.append(dict(kind=kind, id=f'{role}-{self.serial}', role=role, **kw))
    def poly(self, pts, fill, stroke=C['ink'], width=.18, role='shape'):
        self.add('polygon',role,pts=pts,fill=fill,stroke=stroke,width=width)
    def line(self, pts, stroke=C['quiet'], width=.22, role='leader', dash=None):
        self.add('polyline',role,pts=pts,fill='none',stroke=stroke,width=width,dash=dash)
    def circle(self,x,y,r,fill,stroke=C['ink'],width=.18,role='joint'):
        self.add('circle',role,x=x,y=y,r=r,fill=fill,stroke=stroke,width=width)
    def text(self,x,y,s,size=10,bold=False,fill=C['ink'],anchor='start',role='label'):
        self.add('text',role,x=x,y=y,s=s,size=size,bold=bold,fill=fill,anchor=anchor)

def project(x,y,z):
    return (22+.55*(.75*x+.75*y), 72+.55*(.18*x-.35*y-.95*z))
def poly3(sc,pts,fill,role,stroke=C['ink'],width=.18):
    sc.poly([project(*p) for p in pts],fill,stroke,width,role)

def main_base(sc):
    # Single base, not three blocks. Front boundary contains three semicircular cuts.
    poly3(sc,[(130,-40,0),(130,40,0),(130,40,-8),(130,-40,-8)],C['base_side'],'base-right')
    edge=[(-10,-40,0)]
    for d in (50,75,100):
        edge.append((d-2,-40,0))
        edge += [(d+2*math.cos(t),-40,2*math.sin(t)) for t in np.linspace(math.pi,2*math.pi,25)]
    edge += [(130,-40,0),(130,-40,-8),(-10,-40,-8)]
    poly3(sc,edge,C['base_front'],'base-front')
    top=[(-10,-40,0)]
    for d in (50,75,100):
        top += [(d-2,-40,0),(d-2,-32,0),(d+2,-32,0),(d+2,-40,0)]
    top += [(130,-40,0),(130,40,0),(-10,40,0)]
    poly3(sc,top,C['base'],'base-top')
    for n,d in enumerate((50,75,100),1):
        ts=np.linspace(math.pi,2*math.pi,21)
        for a,b in zip(ts[:-1],ts[1:]):
            shade=mix(C['groove'],C['base'],.18+.52*abs(math.cos((a+b)/2)))
            poly3(sc,[(d+2*math.cos(a),-40,2*math.sin(a)),(d+2*math.cos(a),-32,2*math.sin(a)),
                      (d+2*math.cos(b),-32,2*math.sin(b)),(d+2*math.cos(b),-40,2*math.sin(b))],shade,f'groove-S{n}',stroke='none')
        for yy in (-40,-32):
            sc.line([project(d+2*math.cos(t),yy,2*math.sin(t)) for t in ts],C['groove'],.16,f'groove-S{n}-rim')

def panel(sc,theta):
    co,si=math.cos(theta),math.sin(theta)
    # Thickness runs normal to the panel length in the side projection.
    def p(t,y,n): return (t*co-n*si,y,t*si+n*co)
    poly3(sc,[p(0,-32,-1.5),p(120,-32,-1.5),p(120,32,-1.5),p(0,32,-1.5)],C['panel'],'panel-face')
    poly3(sc,[p(0,-32,-1.5),p(0,-32,1.5),p(120,-32,1.5),p(120,-32,-1.5)],C['panel_side'],'panel-near-edge')
    poly3(sc,[p(120,-32,-1.5),p(120,-32,1.5),p(120,32,1.5),p(120,32,-1.5)],'#D9EFEB','panel-top')
    # No markings or screen are added to the display panel.
    return 60*co,60*si

def foot(sc,d,revision):
    ts=np.linspace(0,2*math.pi,65)
    # Cylindrical foot is integral with the one stay, not a base pin.
    if revision=='final':
        # The exact affine silhouette of the specified cylinder is the convex
        # hull of the two projected end circles. No facets or extra mechanism.
        pts=sorted(set(project(d+2*math.cos(t),yy,2*math.sin(t)) for t in ts for yy in (-39,-33)))
        def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
        lo=[];up=[]
        for p in pts:
            while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
            lo.append(p)
        for p in reversed(pts):
            while len(up)>=2 and cross(up[-2],up[-1],p)<=0:up.pop()
            up.append(p)
        sc.poly(lo[:-1]+up[:-1],C['stay'],C['stay_side'],.16,'integral-foot-surface')
        poly3(sc,[(d+2*math.cos(t),-39,2*math.sin(t)) for t in ts],C['stay'],'integral-foot-end',width=.16)
        return
    for a,b in zip(ts[:-1],ts[1:]):
        poly3(sc,[(d+2*math.cos(a),-39,2*math.sin(a)),(d+2*math.cos(a),-33,2*math.sin(a)),
                  (d+2*math.cos(b),-33,2*math.sin(b)),(d+2*math.cos(b),-39,2*math.sin(b))],
              mix(C['stay_side'],C['stay'],.45+.35*math.sin((a+b)/2)), 'integral-foot-surface',stroke='none')
    poly3(sc,[(d+2*math.cos(t),-39,2*math.sin(t)) for t in ts],C['stay'],'integral-foot-end',width=.16)

def stay(sc,px,pz,d,revision):
    dx,dz=d-px,-pz
    nx,nz=-dz/70,dx/70
    def p(x,z,y,off): return(x+nx*off,y,z+nz*off)
    poly3(sc,[p(px,pz,-33,-1),p(d,0,-33,-1),p(d,0,-39,-1),p(px,pz,-39,-1)],'#EDBD83','stay-wide-face')
    poly3(sc,[p(px,pz,-39,-1),p(d,0,-39,-1),p(d,0,-39,1),p(px,pz,-39,1)],C['stay_side'],'stay-near-edge')
    foot(sc,d,revision)
    # Short exposed axle stub connects the panel edge to the beside-panel stay.
    sc.line([project(px,-32,pz),project(px,-39.6,pz)],C['ink'],.58,'pivot-P-axle')
    x,y=project(px,-39,pz)
    sc.circle(x,y,.77,'#EDF2F3',C['ink'],.22,'permanent-pivot-P')
    x,y=project(0,-35,0)
    if revision=='final':
        sc.line([project(0,-32,0),project(0,-35,0)],C['ink'],.58,'hinge-H-axle')
    sc.circle(x,y,.87,'#EDF2F3',C['ink'],.23,'permanent-hinge-H')

def profile(sc,row,ox,oy):
    k=.178
    def p(x,z): return (ox+k*x,oy-k*z)
    ident=row['case_id']; px,pz=float(row['P_x_mm']),float(row['P_z_mm'])
    qx,qz=float(row['Q_x_mm']),float(row['Q_z_mm'])
    tx,tz=float(row['T_x_mm']),float(row['T_z_mm'])
    edge=[p(-10,0)]
    for d in (50,75,100):
        edge.extend(p(d+2*math.cos(t),2*math.sin(t)) for t in np.linspace(math.pi,2*math.pi,13))
    edge += [p(130,0),p(130,-8),p(-10,-8)]
    sc.poly(edge,C['base_front'],C['quiet'],.14,ident+'-base')
    sc.line([p(0,0),p(tx,tz)],C['panel_edge'],.55,ident+'-panel')
    sc.line([p(px,pz),p(qx,qz)],C['stay_side'],.36,ident+'-stay')
    q=p(qx,qz); sc.circle(*q,2*k,C['stay'],C['stay_side'],.14,ident+'-foot')
    for x,z in ((0,0),(px,pz)):
        sc.circle(*p(x,z),.37,'#FFFFFF',C['ink'],.16,ident+'-permanent-pivot')
    if ident=='R':
        # A dashed datum emphasizes the actual clear gap without drawing a trajectory.
        sc.line([p(qx,0),p(qx,23)],C['quiet'],.16,ident+'-clearance',dash='0.5 0.6')

def design(rows,revision):
    sc=Scene()
    sc.text(4,6,'Assembly · S2',10.5,True)
    sc.text(102,6,'Side profiles',10.5,True)
    main_base(sc)
    theta=math.acos((60**2+75**2-70**2)/(2*60*75))
    px,pz=panel(sc,theta); stay(sc,px,pz,75,revision)
    sc.text(4,26,'Panel',10.5)
    sc.line([(15,28),(24,35),(33,38)],C['quiet'],.2,'panel-label-leader')
    sc.text(57,54,'Stay',10.5)
    sc.line([(58,56),(49,60),(29,69)],C['quiet'],.2,'stay-label-leader')
    sc.text(72,89,'Base',10.5)
    sc.line([(75,85),(72,79)],C['quiet'],.2,'base-label-leader')
    sc.text(3.8,76,'H',9.5,True)
    sc.text(12,52.5,'P',9.5,True)
    # Groove identity belongs beside its own recessed seat.
    for n,d in enumerate((50,75,100),1):
        x,y=project(d,-40,0)
        sc.text(x+.8,y+5.5,f'S{n}',8.2,False,anchor='middle',role='groove-label')
    sc.text(5,12,'θ = 61.28°',9.5)
    for row,ox,oy,labx,laby in zip(rows,[104,134,104,134],[47,47,88,88],[102,132,102,132],[15,15,56,56]):
        sc.text(labx,laby,('R · held' if row['case_id']=='R' else row['case_id']),9.5,True,role='state-label')
        sc.text(labx,laby+5,f"{float(row['panel_angle_deg']):.2f}°",9,role='angle-label')
        profile(sc,row,ox,oy)
    sc.text(101,97,'Synthetic geometry · DEMO',8.2,fill=C['quiet'],role='provenance-label')
    return sc

def export(sc,out,font,bold):
    pdfmetrics.registerFont(TTFont('FigureRegular',str(font)))
    pdfmetrics.registerFont(TTFont('FigureBold',str(bold)))
    root=ET.Element(f'{{{NS}}}svg',dict(width='160mm',height='99mm',viewBox='0 0 160 99'))
    desc=ET.SubElement(root,f'{{{NS}}}desc');desc.text='Synthetic geometry; exactly three bodies. Repeated views show one device in four configurations.'
    cv=canvas.Canvas(str(out/'figure.pdf'),pagesize=(W*MM,H*MM),pageCompression=1,invariant=1)
    cv.setTitle('Three-body display support — synthetic geometry DEMO')
    labels=[]
    for it in sc.items:
        kind=it['kind']; a={'id':it['id'],'data-role':it['role']}
        if kind in ('polygon','polyline'):
            a.update(points=' '.join(f'{x:.5f},{y:.5f}' for x,y in it['pts']),fill=it['fill'],stroke=it['stroke'])
            a['stroke-width']=str(it['width']);a['stroke-linejoin']='round'
            if it.get('dash'):a['stroke-dasharray']=it['dash']
            path=cv.beginPath();path.moveTo(it['pts'][0][0]*MM,(H-it['pts'][0][1])*MM)
            for x,y in it['pts'][1:]: path.lineTo(x*MM,(H-y)*MM)
            if kind=='polygon':path.close()
            cv.setLineWidth(it['width']*MM);cv.setLineJoin(1)
            if it.get('dash'):cv.setDash([float(v)*MM for v in it['dash'].split()])
            else:cv.setDash([])
            if it['fill']!='none':cv.setFillColorRGB(*rgb(it['fill']))
            if it['stroke']!='none':cv.setStrokeColorRGB(*rgb(it['stroke']))
            cv.drawPath(path,stroke=int(it['stroke']!='none'),fill=int(it['fill']!='none'))
        elif kind=='circle':
            a.update(cx=str(it['x']),cy=str(it['y']),r=str(it['r']),fill=it['fill'],stroke=it['stroke']);a['stroke-width']=str(it['width'])
            cv.setDash([]);cv.setFillColorRGB(*rgb(it['fill']));cv.setStrokeColorRGB(*rgb(it['stroke']));cv.setLineWidth(it['width']*MM)
            cv.circle(it['x']*MM,(H-it['y'])*MM,it['r']*MM,stroke=1,fill=1)
        else:
            a.update(x=str(it['x']),y=str(it['y']),fill=it['fill']);a['font-family']='Arial';a['font-size']=str(it['size']/MM);a['font-weight']='bold' if it['bold'] else 'normal';a['text-anchor']=it['anchor']
            f='FigureBold' if it['bold'] else 'FigureRegular';cv.setFont(f,it['size']);cv.setFillColorRGB(*rgb(it['fill']))
            tw=pdfmetrics.stringWidth(it['s'],f,it['size'])/MM
            x=it['x']-({'start':0,'middle':.5,'end':1}[it['anchor']])*tw
            cv.drawString(x*MM,(H-it['y'])*MM,it['s'])
            labels.append(dict(id=it['id'],text=it['s'],pt=it['size'],bounds=[x,it['y']-it['size']/MM,x+tw,it['y']+.2]))
        el=ET.SubElement(root,f'{{{NS}}}{kind}',a)
        if kind=='text':el.text=it['s']
    cv.showPage();cv.save()
    ET.ElementTree(root).write(out/'figure.svg',encoding='utf-8',xml_declaration=True)
    return labels

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True);ap.add_argument('--input',type=Path,default=Path(__file__).parent/'source-input'/'finite-record.csv');ap.add_argument('--revision',choices=['first','final'],default='first');a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refusing to overwrite an existing output directory')
    a.out.mkdir(parents=True)
    rows=list(csv.DictReader(a.input.open(encoding='utf-8')))
    sc=design(rows,a.revision);labels=export(sc,a.out,a.font,a.bold_font)
    proc=subprocess.run([str(a.pdftoppm),'-png','-singlefile','-r','300',str(a.out/'figure.pdf'),str(a.out/'figure')],capture_output=True,text=True)
    if proc.returncode:raise RuntimeError(proc.stderr)
    im=Image.open(a.out/'figure.png').convert('RGB')
    ImageOps.grayscale(im).save(a.out/'figure-grayscale.png')
    # Explicit, approximate single deuteranopia matrix; not all CVD conditions.
    arr=np.asarray(im)/255.;mat=np.array([[.367,.861,-.228],[.280,.673,.047],[-.012,.043,.969]])
    Image.fromarray(np.uint8(np.clip(arr@mat.T,0,1)*255+.5)).save(a.out/'figure-deuteranopia.png')
    pg=PdfReader(a.out/'figure.pdf').pages[0]
    checks={'svg_xml':'parsed','svg_images':len(ET.parse(a.out/'figure.svg').findall('.//{'+NS+'}image')),'pdf_pages':1,'pdf_mm':[float(pg.mediabox.width)/MM,float(pg.mediabox.height)/MM],'png_pixels':im.size,'min_font_pt':min(x['pt'] for x in labels),'text_out_of_bounds':[x for x in labels if x['bounds'][0]<0 or x['bounds'][1]<0 or x['bounds'][2]>W or x['bounds'][3]>H],'pdf_text':pg.extract_text(),'labels':labels,'render_returncode':proc.returncode,'limitations':['No automatic complex-surface occlusion or scientific mechanism validator','No actual-size Word integration in this subtask','CVD output is an approximate single-condition screen preview']}
    (a.out/'technical-checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    (a.out/'scene.json').write_text(json.dumps(sc.items,indent=2),encoding='utf-8')
    receipt={'kind':'fixed_source_reconstruction','revision':a.revision,'command':sys.argv,'python':sys.version,'inputs':{str(a.input):sha(a.input),str(a.font):sha(a.font),str(a.bold_font):sha(a.bold_font)},'artifacts':{p.name:sha(p) for p in sorted(a.out.iterdir()) if p.is_file()}}
    (a.out/'rebuild-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(a.out),'minimum_font_pt':checks['min_font_pt'],'text_out_of_bounds':len(checks['text_out_of_bounds']),'files':len(receipt['artifacts'])}))

if __name__=='__main__':main()
