"""Rebuild a fictional plate schematic. All lengths below are illustration ratios.
Usage: python build_figure.py --out NEW_DIRECTORY --view plan|oblique --font FONT --bold-font FONT --pdftoppm TOOL
The output directory must not exist. No external image assets or font copies.
"""
import argparse, json, math, hashlib, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageOps
import numpy as np
from pypdf import PdfReader

MM=72/25.4
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arc(r,a,b,n=160): return [(r*math.cos(t),r*math.sin(t)) for t in np.linspace(a,b,n)]
def contours():
    outer=arc(1,0,2*math.pi,721)[:-1]
    holes=[]; r=.34; ri=.80; hw=.08
    for k in range(3):
        a=math.pi/2+k*2*math.pi/3; b=a+2*math.pi/3
        # Clockwise hole: inner arc CCW, straight bridge edge outward,
        # outer arc CW, opposite bridge edge inward.
        holes.append(arc(r,a+math.asin(hw/r),b-math.asin(hw/r))+
                     arc(ri,b-math.asin(hw/ri),a+math.asin(hw/ri)))
    return [outer]+holes

class Drawing:
    def __init__(self,out,font,bold):
        self.out=out; self.items=[]; self.labels=[]
        pdfmetrics.registerFont(TTFont('PlateArial',str(font)))
        pdfmetrics.registerFont(TTFont('PlateArialBold',str(bold)))
        self.pdf=canvas.Canvas(str(out/'figure.pdf'),pagesize=(160*MM,85*MM),pageCompression=1,invariant=1)
        self.pdf.setTitle('Fictional DEMO — one-piece plate')
        self.pdf.setAuthor('Model-generated illustration; not experimental evidence')
    def path(self,polys,fill,stroke='#294B55',width=.28,id='path',attrs=''):
        d=' '.join('M '+' L '.join(f'{x:.5f} {y:.5f}' for x,y in p)+' Z' for p in polys)
        self.items.append(f'<path id="{id}" d="{d}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" {attrs}/>')
        p=self.pdf.beginPath()
        for poly in polys:
            p.moveTo(poly[0][0]*MM,(85-poly[0][1])*MM)
            for x,y in poly[1:]: p.lineTo(x*MM,(85-y)*MM)
            p.close()
        from reportlab.lib.colors import HexColor
        self.pdf.setFillColor(HexColor(fill)); self.pdf.setStrokeColor(HexColor(stroke if stroke!='none' else fill)); self.pdf.setLineWidth(width*MM)
        self.pdf.drawPath(p,fill=1,stroke=int(stroke!='none'),fillMode=0)
    def line(self,pts,id):
        d='M '+' L '.join(f'{x:.5f} {y:.5f}' for x,y in pts)
        self.items.append(f'<path id="{id}" d="{d}" fill="none" stroke="#536776" stroke-width="0.20" stroke-linecap="round"/>')
        from reportlab.lib.colors import HexColor
        self.pdf.setStrokeColor(HexColor('#536776'));self.pdf.setLineWidth(.20*MM)
        p=self.pdf.beginPath();p.moveTo(pts[0][0]*MM,(85-pts[0][1])*MM)
        for x,y in pts[1:]:p.lineTo(x*MM,(85-y)*MM)
        self.pdf.drawPath(p,stroke=1,fill=0)
    def text(self,x,y,s,id,bold=False,size=9.5,color='#233B46'):
        from reportlab.lib.colors import HexColor
        self.items.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-size="{size/MM:.6f}" font-weight="{"bold" if bold else "normal"}" fill="{color}">{s}</text>')
        self.pdf.setFont('PlateArialBold' if bold else 'PlateArial',size);self.pdf.setFillColor(HexColor(color));self.pdf.drawString(x*MM,(85-y)*MM,s)
        self.labels.append({'id':id,'text':s,'font_pt':size,'x_mm':x,'baseline_y_mm':y})
    def finish(self):
        self.pdf.showPage();self.pdf.save()
        root='<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="85mm" viewBox="0 0 160 85">\n<title>Fictional DEMO: one-piece plate</title>\n<desc>A continuous outer ring and circular central platform joined by exactly three equal-width radial bridges. The three intervening regions are openings through a uniform-thickness plate.</desc>\n<rect id="background" x="0" y="0" width="160" height="85" fill="#FFFFFF"/>\n'
        (self.out/'figure.svg').write_text(root+'\n'.join(self.items)+'\n</svg>\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--view',choices=['plan','oblique'],required=True)
    ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():ap.error('Refusing to overwrite an existing output directory')
    a.out.mkdir(parents=True)
    R=30 if a.view=='plan' else 44; sy=1 if a.view=='plan' else .63; depth=0 if a.view=='plan' else 3.4
    def project(p,z=0):return (82+R*p[0],43-R*sy*p[1]+z)
    cs=contours();d=Drawing(a.out,a.font,a.bold_font)
    if a.view=='oblique':
        # Boundary winding gives the material's outward normal. Faces whose
        # outward normal points toward negative y are visible to the viewer.
        for ci,c in enumerate(cs):
            for i,p in enumerate(c):
                q=c[(i+1)%len(c)];dx=q[0]-p[0];dy=q[1]-p[1]
                if dx>1e-9:
                    nlen=math.hypot(dx,dy); lum=.82+.12*(dy/nlen)
                    rgb=tuple(int(v*lum) for v in (91,140,151)); fill='#' + ''.join(f'{v:02x}' for v in rgb)
                    d.path([[project(p),project(q),project(q,depth),project(p,depth)]],fill,stroke='none',width=0,id=f'wall-{ci}-{i}',attrs='data-entity="plate" data-role="side-face"')
        # Bottom edges of all visible wall runs; no seams across coplanar top.
        for ci,c in enumerate(cs):
            run=[];runs=[]
            for i,p in enumerate(c):
                q=c[(i+1)%len(c)]
                if q[0]-p[0]>1e-9:
                    if not run:run=[project(p,depth)]
                    run.append(project(q,depth))
                elif run:runs.append(run);run=[]
            if run:runs.append(run)
            for j,run in enumerate(runs):d.line(run,f'lower-boundary-{ci}-{j}')
    d.path([[project(p) for p in c] for c in cs],'#B5D1D4',id='plate-top',attrs='data-entity="plate" data-role="top-face" data-hole-count="3" data-bridge-count="3"')
    d.text(6,8,'FICTIONAL DEMO',id='demo-label',bold=True,size=9,color='#536776')
    d.text(119,8,'One-piece plate',id='title',bold=True,size=10)
    d.text(6,22,'Central platform',id='central-label')
    d.line([(35,23.5),(42,23.5),project((-.18,.03))],'central-leader')
    d.text(125,24,'Outer ring',id='ring-label')
    d.line([(125,26),(121,26),project((.68,.61))],'ring-leader')
    d.text(6,65,'Three equal-width',id='bridge-label-1')
    d.text(6,69.3,'radial bridges',id='bridge-label-2')
    d.line([(37,65),(45,65),project((-.51,-.29445))],'bridge-leader')
    d.text(121,61,'Through-open',id='opening-label-1')
    d.text(121,65.3,'regions',id='opening-label-2')
    d.line([(119,61),(111,61),project((.25,-.51))],'opening-leader')
    d.finish()
    command=[str(a.pdftoppm),'-png','-r','300','-singlefile',str(a.out/'figure.pdf'),str(a.out/'figure')]
    proc=subprocess.run(command,capture_output=True,text=True)
    if proc.returncode:raise RuntimeError(proc.stderr)
    im=Image.open(a.out/'figure.png').convert('RGB');ImageOps.grayscale(im).save(a.out/'figure_grayscale.png')
    # Fixed deuteranopia screening matrix (linear RGB approximation only).
    v=np.asarray(im)/255.; lin=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
    m=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    lin=np.clip(lin@m.T,0,1); sim=np.where(lin<=.0031308,12.92*lin,1.055*lin**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(sim*255,0,255))).save(a.out/'figure_deuteranopia.png')
    pdf=PdfReader(a.out/'figure.pdf');box=pdf.pages[0].mediabox
    facts={'fictional_demo':True,'view':a.view,'size_mm':[160,85],'model':{'outer_radius':1,'ring_inner_radius':.8,'platform_radius':.34,'bridge_width':.16,'bridge_angles_deg':[90,210,330],'thickness_projection_mm':depth,'units':'illustration ratios; no measured dimensions'},'entities':[{'id':'plate','actual_object_count':1,'regions':['outer ring','central platform','three radial bridges']}],'relations':{'bridges':'radial, equal width, evenly spaced, continuous with ring and platform','open_regions':3,'thickness':'uniform','directional_arrows':False},'labels':d.labels,'editable':'All shapes are vector paths; SVG text remains text; PDF uses embedded Arial subsets. Font files are external, not redistributed.'}
    (a.out/'figure_spec.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    text={'demo':True,'paragraph':'The fictional structure in Fig. 1 is a single plate of uniform thickness. A circular central platform is connected to a continuous outer ring by three straight radial bridges of equal width, spaced uniformly around the platform. The regions between adjacent bridges are open through the full plate thickness. The platform, bridges, and ring therefore form one continuous piece; the illustration describes geometry only and is not based on measured dimensions or experimental tests.','caption':'Figure 1. Fictional DEMO of a one-piece plate comprising a circular central platform, a continuous outer ring, and three equal-width radial bridges at uniform angular intervals. The three intervening regions are through-openings. '+('The oblique view exposes the uniform plate thickness; darker faces indicate surface orientation within the same piece. ' if a.view=='oblique' else 'The plan view shows the complete in-plane connectivity. ')+'Proportions are illustrative, with no measured dimensions or test results.','alt_text':'A single continuous plate has a complete circular outer ring around a circular central platform. Exactly three straight, equally wide bridges connect the two at evenly spaced angles. Three intervening apertures are empty through the plate. '+('An oblique view shows shallow side walls and consistent thickness.' if a.view=='oblique' else 'Viewed from above.')}
    (a.out/'text.json').write_text(json.dumps(text,indent=2),encoding='utf-8')
    check={'technical_status':'PASS','overall_status':'REVIEW_REQUIRED','scientific_review_status':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED','author_acceptance':'NOT_OBTAINED','journal_acceptance':'NOT_CLAIMED','svg_xml_parse':bool(ET.parse(a.out/'figure.svg')),'pdf_pages':len(pdf.pages),'pdf_size_mm':[float(box.width)/MM,float(box.height)/MM],'pdf_text':pdf.pages[0].extract_text(),'png_size_px':list(im.size),'minimum_label_pt':min(x['font_pt'] for x in d.labels),'vector_image_nodes':0,'export_command':command,'export_exit_code':proc.returncode,'fonts':[{'path':str(a.font),'sha256':sha(a.font)},{'path':str(a.bold_font),'sha256':sha(a.bold_font)}],'files':{p.name:sha(p) for p in a.out.iterdir() if p.is_file()},'limits':['No author or independent reviewer acceptance.','No scientific measurements or tests.','Cross-platform SVG font substitution is untested.','Color-vision view screens one simulated condition only.']}
    assert len(pdf.pages)==1 and all(abs(v-e)<.01 for v,e in zip(check['pdf_size_mm'],[160,85]))
    assert all(x['text'] in check['pdf_text'] for x in d.labels)
    (a.out/'export_checks.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(a.out),'view':a.view,'export':'PASS','png_size_px':list(im.size)}))
if __name__=='__main__':main()
