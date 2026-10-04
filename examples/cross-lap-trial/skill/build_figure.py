"""Rebuild the original cross-lap figure from explicit, dimensioned geometry.
Requires reportlab, Pillow, numpy, pypdf, an Arial-compatible TTF and pdftoppm.
All paths are CLI parameters. Refuses to replace an existing figure file.
"""
from pathlib import Path
import argparse, json, hashlib, math, subprocess, shutil
from collections import Counter
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

P=argparse.ArgumentParser()
P.add_argument('--source',type=Path,required=True)
P.add_argument('--out',type=Path,required=True)
P.add_argument('--font',type=Path,required=True)
P.add_argument('--bold-font',type=Path)
P.add_argument('--pdftoppm',type=Path,required=True)
P.add_argument('--revision',choices=['first','final'],default='first')
a=P.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
if (a.out/'figure.svg').exists() or (a.out/'figure.pdf').exists():
    raise SystemExit('Refusing to overwrite an existing figure')
source_text=a.source.read_text(encoding='utf-8-sig')
assert 'z = [0,8]' in source_text and 'z = [8,16]' in source_text
pdfmetrics.registerFont(TTFont('FigureArial',str(a.font)))
pdfmetrics.registerFont(TTFont('FigureArialBold',str(a.bold_font or a.font)))
MM=72/25.4
W,H=160,100
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
svg=ET.Element('{'+NS+'}svg',{'width':'160mm','height':'100mm','viewBox':'0 0 160 100','version':'1.1'})
title=ET.SubElement(svg,'{'+NS+'}title');title.text='Complementary cross-lap notches and flush assembly'
desc=ET.SubElement(svg,'{'+NS+'}desc');desc.text='Constructed geometry demonstration. Three views of the same two members: separated, assembled, and the central contact section.'
c=Canvas(str(a.out/'figure.pdf'),pagesize=(W*MM,H*MM),pageCompression=1,invariant=1)
c.setTitle('Complementary cross-lap notches and flush assembly — constructed DEMO')
c.setAuthor('Original geometry illustration')
shapes=[]; text_records=[]
ink='#253747'; muted='#526675'; A='#5F98B5'; B='#E5AF62'
pal={'A':{'top':'#9BC3D6','side':'#5F98B5','end':'#397695'},'B':{'top':'#F0CD91','side':'#DEA450','end':'#BF813A'}}

def attrs(id,entity=None,view=None,part=None,relation=None):
    d={'id':id}
    for k,v in [('entity',entity),('view',view),('object-part',part),('relation',relation)]:
        if v is not None:d['data-'+k]=v
    return d

def poly(points,fill,stroke=ink,width=.28,id='poly',**meta):
    d=attrs(id,**meta);d.update({'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in points),'fill':fill or 'none','stroke':stroke or 'none','stroke-width':str(width),'stroke-linejoin':'round'})
    ET.SubElement(svg,'{'+NS+'}polygon',d)
    p=c.beginPath();p.moveTo(points[0][0]*MM,(H-points[0][1])*MM)
    for x,y in points[1:]:p.lineTo(x*MM,(H-y)*MM)
    p.close()
    if fill:c.setFillColor(HexColor(fill))
    if stroke:c.setStrokeColor(HexColor(stroke));c.setLineWidth(width*MM)
    c.setLineJoin(1);c.drawPath(p,fill=bool(fill),stroke=bool(stroke))
    shapes.append({'id':id,'points':points,**meta})

def line(points,color=ink,width=.28,dash=None,id='line',**meta):
    d=attrs(id,**meta);d.update({'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in points),'fill':'none','stroke':color,'stroke-width':str(width),'stroke-linejoin':'round','stroke-linecap':'round'})
    if dash:d['stroke-dasharray']=' '.join(map(str,dash))
    ET.SubElement(svg,'{'+NS+'}polyline',d)
    c.setStrokeColor(HexColor(color));c.setLineWidth(width*MM);c.setLineCap(1);c.setLineJoin(1)
    c.setDash([d*MM for d in dash] if dash else [])
    p=c.beginPath();p.moveTo(points[0][0]*MM,(H-points[0][1])*MM)
    for x,y in points[1:]:p.lineTo(x*MM,(H-y)*MM)
    c.drawPath(p,stroke=1,fill=0);c.setDash([])
    shapes.append({'id':id,'points':points,**meta})

def text(x,y,s,pt=10,bold=False,color=ink,anchor='start',id=None):
    id=id or 'text-'+str(len(text_records))
    size=pt/MM
    d={'id':id,'x':str(x),'y':str(y),'font-family':'Arial','font-size':str(size),'font-weight':'bold' if bold else 'normal','fill':color,'text-anchor':anchor}
    t=ET.SubElement(svg,'{'+NS+'}text',d);t.text=s
    font='FigureArialBold' if bold else 'FigureArial'
    c.setFillColor(HexColor(color));c.setFont(font,pt)
    width=pdfmetrics.stringWidth(s,font,pt)/MM
    left=x-(width/2 if anchor=='middle' else width if anchor=='end' else 0)
    c.drawString(left*MM,(H-y)*MM,s)
    text_records.append({'id':id,'text':s,'pt':pt,'bounds':[left,y-size*.82,left+width,y+size*.22]})

EYE=np.array([.4242640687,-.5656854249,.7071067812])
SX=np.array([.8,.6,0.]);SY=np.array([.4242640687,-.5656854249,-.7071067812])
def project(p,origin,scale):return (origin[0]+float(np.dot(p,SX))*scale,origin[1]+float(np.dot(p,SY))*scale)

def member_faces(member,lift=0):
    # Concave extrusion profiles; every coordinate comes from the geometry fixture.
    if member=='A':
        profile=[(-50,0),(50,0),(50,16),(10,16),(10,8),(-10,8),(-10,16),(-50,16)]
        convert=lambda u,z,w:(u,w,z+lift)
        lo,hi=-10,10
        normal_lo=(0,-1,0);normal_hi=(0,1,0)
    else:
        profile=[(-40,0),(-10,0),(-10,8),(10,8),(10,0),(40,0),(40,16),(-40,16)]
        convert=lambda u,z,w:(w,u,z+lift)
        lo,hi=-10,10
        normal_lo=(-1,0,0);normal_hi=(1,0,0)
    faces=[([convert(u,z,lo) for u,z in profile],normal_lo,'side'),([convert(u,z,hi) for u,z in profile],normal_hi,'side')]
    for i,(u,z) in enumerate(profile):
        u2,z2=profile[(i+1)%len(profile)]
        du,dz=u2-u,z2-z
        n=(dz,0,-du) if member=='A' else (0,dz,-du)
        kind='top' if n[2]>0 else 'end'
        faces.append(([convert(u,z,lo),convert(u2,z2,lo),convert(u2,z2,hi),convert(u,z,hi)],n,kind))
    return [(p,n,k) for p,n,k in faces if np.dot(n,EYE)>0]

def draw_exploded(origin=(47,70),scale=.82,lift_b=30):
    for m,lift in [('A',0),('B',lift_b)]:
        faces=member_faces(m,lift)
        faces.sort(key=lambda f:float(np.dot(np.mean(f[0],axis=0),EYE)))
        for j,(p,n,k) in enumerate(faces):
            poly([project(v,origin,scale) for v in p],pal[m][k],id=f'exploded-{m}-face-{j}',entity=m,view='exploded',part='primary' if j==0 else 'surface')
    return lambda p:project(p,origin,scale)

def draw_assembled(origin=(125,34),scale=.54):
    xs=[-50,-10,10,50];ys=[-40,-10,10,40];zs=[0,8,16]
    occupancy={}
    for i in range(3):
        for j in range(3):
            for k in range(2):
                if j==1 and (i!=1 or k==0):occupancy[i,j,k]='A'
                if i==1 and (j!=1 or k==1):occupancy[i,j,k]='B'
    faces=[]
    for (i,j,k),m in occupancy.items():
        x0,x1=xs[i:i+2];y0,y1=ys[j:j+2];z0,z1=zs[k:k+2]
        for n,adj,pts,kind in [
            ((1,0,0),(i+1,j,k),[(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],'end'),
            ((0,-1,0),(i,j-1,k),[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],'side'),
            ((0,0,1),(i,j,k+1),[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],'top')]:
            if adj in occupancy:continue
            faces.append({'p':pts,'n':n,'m':m,'k':kind})
    # Coplanar edges shared by the same member are construction seams, not outlines.
    edges=Counter()
    for f in faces:
        for u,v in zip(f['p'],f['p'][1:]+f['p'][:1]):edges[(f['m'],f['n'],tuple(sorted((u,v))))]+=1
    faces.sort(key=lambda f:float(np.dot(np.mean(f['p'],axis=0),EYE)))
    for j,f in enumerate(faces):
        m=f['m'];p=f['p']
        poly([project(v,origin,scale) for v in p],pal[m][f['k']],stroke=None,id=f'assembled-{m}-face-{j}',entity=m,view='assembled',part='detail')
        for e,(u,v) in enumerate(zip(p,p[1:]+p[:1])):
            if edges[(m,f['n'],tuple(sorted((u,v))))]==1:
                line([project(u,origin,scale),project(v,origin,scale)],id=f'assembled-edge-{j}-{e}',entity=m,view='assembled',part='detail')
    return lambda p:project(p,origin,scale)

poly([(0,0),(160,0),(160,100),(0,100)],'#FFFFFF',stroke=None,id='page-background')
text(6,8,'a  Complementary notches',11,bold=True)
text(100,8,'b  Assembled',11,bold=True)
pe=draw_exploded(origin=(47,72),scale=.74,lift_b=44) if a.revision=='final' else draw_exploded()
pa=draw_assembled(origin=(125,32)) if a.revision=='final' else draw_assembled()

# Labels bind to the visible faces, not to detached verbal rules.
if a.revision=='final':
    text(10,75,'A',11,bold=True,color='#214F68')
    line([(15,72),pe((-35,-10,8))],color='#214F68',id='A-identity',entity='A',view='exploded')
    text(78,27,'B',11,bold=True,color='#80531D')
    line([(76,28),pe((10,28,56))],color='#80531D',id='B-identity',entity='B',view='exploded')
    text(6,86,'Upper notch',10,bold=True)
    line([(31,83),(38,76),pe((0,-4,8))],width=.24,id='upper-notch-leader',entity='A',view='exploded',relation='identifies-upper-notch')
    text(64,46,'Lower notch',10,bold=True)
    line([(62,47),pe((10,0,52))],width=.24,id='lower-notch-leader',entity='B',view='exploded',relation='identifies-lower-notch')
    line([(49,54),(49,62)],width=.45,id='lower-B-motion',entity='B',view='exploded',relation='assembly-motion')
    poly([(49,63),(47.9,60.8),(50.1,60.8)],ink,stroke=None,id='lower-B-motion-head',entity='B',view='exploded',relation='assembly-motion')
    text(53,59,'Lower B',9.5)
else:
    text(10,86,'A',11,bold=True,color='#214F68')
    line([(15,83),pe((-35,-10,8))],color='#214F68',id='A-identity',entity='A',view='exploded')
    text(71,28,'B',11,bold=True,color='#80531D')
    line([(70,30),pe((10,28,42))],color='#80531D',id='B-identity',entity='B',view='exploded')
    text(5,42,'Upper notch',10,bold=True)
    line([(6,44),(6,51),pe((-7,-8,8))],width=.24,id='upper-notch-leader',entity='A',view='exploded',relation='identifies-upper-notch')
    text(52,17,'Lower notch',10,bold=True)
    line([(67,19),(77,37),pe((10,0,38))],width=.24,id='lower-notch-leader',entity='B',view='exploded',relation='identifies-lower-notch')
    line([(47,53),(47,60)],width=.45,id='lower-B-motion',entity='B',view='exploded',relation='assembly-motion')
    poly([(47,61),(45.9,58.8),(48.1,58.8)],ink,stroke=None,id='lower-B-motion-head',entity='B',view='exploded',relation='assembly-motion')
    text(51,57,'Lower B',9.5)
text(5,93,'Each notch crosses the full width',9.4)

text(124.5,50,'Flush top and base',10,bold=True,anchor='middle')
# A dashed section trace at the crossing refers to the same assembled pair.
line([pa((-10,0,16)),pa((10,0,16))],color=ink,width=.35,dash=[1.1,.8],id='section-trace',view='assembled',relation='section-location')
text(146,24,'c',10,bold=True)
line([(143.7,24),pa((10,0,16))],width=.23,id='section-trace-label',view='assembled',relation='section-location')

text(100,60,'c  Crossing section',11,bold=True)
text(100,65,'Same A and B, at y = 0',9.3)
left,right,top,mid,base=107,135,69,80.2,91.4
poly([(left,top),(right,top),(right,mid),(left,mid)],pal['B']['top'],id='section-B',entity='B',view='section',part='detail')
poly([(left,mid),(right,mid),(right,base),(left,base)],pal['A']['top'],id='section-A',entity='A',view='section',part='detail')
line([(left,mid),(right,mid)],width=.55,id='contact-z8',view='section',relation='contact')
text(121,76,'B',10.5,bold=True,anchor='middle')
text(121,87.2,'A',10.5,bold=True,anchor='middle')
for y,label in [(top,'16'),(mid,'8'),(base,'0')]:
    line([(right,y),(139,y)],width=.22,id='z-tick-'+label,view='section')
    text(141,y+1.15,label,9.5)
text(141,66 if a.revision=='final' else 67,'z (mm)',8.7)
text(104,81.3,'contact',9,anchor='end')
line([(104.5,mid),(left,mid)],width=.28,id='contact-label',view='section',relation='contact')
text(6,98,'Two members, three views',9,color=muted)
text(154,98,'DEMO',9,bold=True,color=muted,anchor='end')

c.showPage();c.save()
ET.indent(svg)
ET.ElementTree(svg).write(a.out/'figure.svg',encoding='utf-8',xml_declaration=True)
subprocess.run([str(a.pdftoppm),'-png','-singlefile','-r','300',str(a.out/'figure.pdf'),str(a.out/'figure')],check=True,capture_output=True)
im=Image.open(a.out/'figure.png').convert('RGB')
im.convert('L').save(a.out/'figure_grayscale.png')
# Machado et al. matrix at full deuteranomaly severity, applied in linear RGB.
# This is one selected simulation, not an accessibility certification.
rgb=np.asarray(im).astype(float)/255
lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
sim=np.clip(lin@mat.T,0,1)
srgb=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
Image.fromarray(np.uint8(np.clip(srgb,0,1)*255)).save(a.out/'figure_deuteranopia.png')
caption=('Constructed geometry demonstration of a perpendicular cross-lap joint. (a) Member A (blue; 100 × 20 × 16 mm along x, y and z) has a central upper-half notch; member B (ochre; 20 × 80 × 16 mm) has the complementary lower-half notch. Each notch spans the full 20 mm width and is 8 mm deep. B is shown raised vertically for explanation; the downward arrow indicates visual assembly motion. (b) The same two members assembled, with both top surfaces at z = 16 mm and both lower surfaces at z = 0. The dashed line locates the central section. (c) The crossing alone, sectioned at y = 0: A occupies z = 0–8 mm and B occupies z = 8–16 mm, meeting at z = 8 with no volume overlap. Views use different display scales. Contact is ideal with zero clearance; manufacturing tolerances are unspecified. This is a geometry fixture, not a tested joint or a strength result.')
(a.out/'caption.txt').write_text(caption+'\n',encoding='utf-8')
(a.out/'alt_text.txt').write_text('Blue member A has an open notch across its upper half. Ochre member B has a corresponding notch across its lower half and is raised above A. Lowering B fills the upper half of the crossing while A fills the lower half. The assembled cross has flush top and bottom surfaces. A central section of the same two members shows the shared z = 8 mm contact, with A below and B above.\n',encoding='utf-8')
spec={'identity':'DEMO','source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'output_mm':[160,100],'projection':{'type':'orthographic affine','screen_x':SX.tolist(),'screen_y':SY.tolist(),'eye':EYE.tolist()},'entities':{'A':{'bounds':[[-50,50],[-10,10],[0,16]],'removed':[[-10,10],[-10,10],[8,16]],'color_role':'blue'},'B':{'bounds':[[-10,10],[-40,40],[0,16]],'removed':[[-10,10],[-10,10],[0,8]],'color_role':'ochre'}},'views':{'exploded':'primary representations of A and B; B translated +30 mm along z for display','assembled':'same A and B, zero display translation','section':'same A and B, crossing only at y=0'},'relations':{'assembly-motion':'B lowered along negative z, conceptual assembly only','contact':'A upper central surface and B lower central surface share z=8','section-location':'dashed trace at y=0 of crossing'},'locked_values':{'A_length_mm':100,'B_length_mm':80,'width_mm':20,'total_height_mm':16,'notch_depth_mm':8,'contact_z_mm':8,'physical_members':2},'editable':'All original SVG polygons, polylines and text are vector objects. PDF embeds a subset font. SVG relies on local Arial. No raster is embedded.','role_palette':pal,'design_choice':'Exploded geometry exposes the complementary open notches, assembly establishes flush outer surfaces, and a named section reveals contact hidden inside the assembled cross. The section is a repeat view, not a third member.'}
if a.revision=='final':spec['views']['exploded']='primary representations of A and B; B translated +44 mm along z for display'
(a.out/'figure_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pdf=PdfReader(a.out/'figure.pdf');box=pdf.pages[0].mediabox
table=[]
for x in [-49,-11,-9,0,9,11,49]:
    for y in [-39,-11,-9,0,9,11,39]:
        for z in [1,7,9,15]:
            ina=(-50<x<50 and -10<y<10 and 0<z<16 and not(-10<x<10 and 8<z<16))
            inb=(-10<x<10 and -40<y<40 and 0<z<16 and not(-10<y<10 and 0<z<8))
            assert not(ina and inb),'Overlapping material'
            table.append([x,y,z,int(ina),int(inb)])
bounds_issues=[t for t in text_records if t['bounds'][0]<0 or t['bounds'][2]>160 or t['bounds'][1]<0 or t['bounds'][3]>100]
overlaps=[]
for i,t in enumerate(text_records):
    for u in text_records[i+1:]:
        x1,y1,x2,y2=t['bounds'];x3,y3,x4,y4=u['bounds']
        if min(x2,x4)>max(x1,x3) and min(y2,y4)>max(y1,y3):overlaps.append([t['text'],u['text']])
checks={'source_sha256':spec['source_sha256'],'revision':a.revision,'svg_width_mm':160,'svg_height_mm':100,'pdf_pages':len(pdf.pages),'pdf_size_mm':[float(box.width)/MM,float(box.height)/MM],'png_pixels':im.size,'minimum_font_pt':min(t['pt'] for t in text_records),'text_bounds_issues':bounds_issues,'text_pair_bounds_overlaps':overlaps,'geometry_overlap_sample_count':len(table),'geometry_overlap_sample_failures':0,'exact_box_intersection':'A and B intersect only at their common z=8 boundary inside crossing; central occupied intervals [0,8] and [8,16] share no volume.','svg_image_count':len(svg.findall('.//{'+NS+'}image')),'pdf_text':pdf.pages[0].extract_text(),'technical_status':'PASS' if not bounds_issues and not overlaps else 'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED','scientific_review_status':'REVIEW_REQUIRED','author_acceptance':'NOT_RUN','limits':['Text bounding boxes are a basic screen; arbitrary line/face overlap requires viewing the image.','Projection visibility and exact visual contact are reviewed manually, not certified by sample-point occupancy.','Physical printing and editor interoperability are not tested.']}
(a.out/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(a.out/'text_inventory.json').write_text(json.dumps(text_records,indent=2)+'\n',encoding='utf-8')
shutil.copy2(__file__,a.out/'build_figure.py')
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.out.iterdir() if f.is_file() and f.suffix in ['.svg','.pdf','.png','.txt','.py','.json']}
(a.out/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'out':str(a.out),'technical_status':checks['technical_status'],'text_overlaps':overlaps,'pdf_mm':checks['pdf_size_mm']},ensure_ascii=True))
