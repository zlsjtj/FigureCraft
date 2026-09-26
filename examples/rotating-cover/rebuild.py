"""Original DEMO figure. Rebuild from source_facts.json; no network or skill engine.
Requires reportlab, pypdf, Pillow, numpy, Arial regular/bold fonts and pdftoppm.
All paths are explicit arguments; output must not already exist.
"""
from pathlib import Path
import argparse, json, math, hashlib, subprocess, sys, re
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

W,H=720,440
WIDTH_MM=160
SCALE=WIDTH_MM*72/25.4/W
COLORS={'ink':'#22333F','muted':'#52626C','disk':'#E6EBED','disk_edge':'#9CAAB1','shaft':'#CDD6DB','cover':'#315569','cover_side':'#233E4D','contact':'#EDBD67','contact_edge':'#866333','white':'#FFFFFF','rule':'#CBD4D9'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pos(cx,cy,r,a):
    a=math.radians(a)
    return [round(cx+r*math.sin(a),5),round(cy-r*math.cos(a),5)]
def sector(cx,cy,ro,ri,start,end):
    n=round(end-start)
    return [pos(cx,cy,ro,start+i) for i in range(n+1)]+[pos(cx,cy,ri,end-i) for i in range(n+1)]
def path_d(points,closed=True):return 'M '+' L '.join(f'{x:g} {y:g}' for x,y in points)+(' Z' if closed else '')

class Drawing:
    def __init__(self):self.items=[];self.views=[];self.arrow=None
    def add(self,tag,id,**a):
        el={'tag':tag,'id':id,**a};self.items.append(el);return el
    def circle(self,id,x,y,r,fill,stroke='none',sw=1,**a):return self.add('circle',id,cx=x,cy=y,r=r,fill=fill,stroke=stroke,stroke_width=sw,**a)
    def text(self,id,text,x,y,size=16,bold=False,anchor='middle',color=None,**a):return self.add('text',id,text=text,x=x,y=y,font_size=size,font_weight='bold' if bold else 'normal',text_anchor=anchor,fill=color or COLORS['ink'],font_family='Arial',**a)
    def line(self,id,x1,y1,x2,y2,stroke=None,sw=1,**a):return self.add('line',id,x1=x1,y1=y1,x2=x2,y2=y2,stroke=stroke or COLORS['rule'],stroke_width=sw,fill='none',**a)
    def path(self,id,points,fill='none',stroke='none',sw=1,closed=True,**a):return self.add('path',id,points=points,closed=closed,fill=fill,stroke=stroke,stroke_width=sw,**a)
    def view(self,view_id,cx,cy,r,start,primary=False):
        meta={'data_view':view_id,'data_entity':'contact-disk','data_object_part':'primary' if primary else 'detail'}
        self.circle(view_id+'-disk-side',cx,cy+5,r,COLORS['disk_edge'],data_entity='contact-disk',data_object_part='decoration',data_view=view_id)
        self.circle(view_id+'-disk',cx,cy,r,COLORS['disk'],COLORS['disk_edge'],1.2,**meta)
        centers=[]
        for item in FACTS['contacts']:
            cid,a=item['id'],item['angle_deg'];x,y=pos(cx,cy,r*.715,a)
            shown=start is None or 0<=((a-start)%360)<90
            cm={'data_entity':f'contact-{cid}','data_contact_id':cid,'data_angle_deg':a,'data_view':view_id,'data_visible':str(shown).lower(),'data_object_part':'primary' if primary else 'detail'}
            self.circle(f'{view_id}-contact-{cid}',x,y,r*.108,COLORS['contact'],COLORS['contact_edge'],1,**cm)
            self.text(f'{view_id}-number-{cid}',str(cid),x,y+5,15,True,data_entity=f'contact-{cid}',data_view=view_id,data_object_part='decoration')
            centers.append({'id':cid,'center':[x,y],'radius':r*.108,'visible':shown})
        if start is not None:
            ro,ri=r*.974,r*.32
            self.path(view_id+'-cover-side',sector(cx,cy+3,ro,ri,start+90,start+360),COLORS['cover_side'],data_entity='cover',data_object_part='decoration',data_view=view_id)
            self.path(view_id+'-cover',sector(cx,cy,ro,ri,start+90,start+360),COLORS['cover'],COLORS['cover_side'],1.1,data_entity='cover',data_object_part='primary' if view_id=='initial' else 'detail',data_view=view_id,data_opening_start_deg=start,data_opening_span_deg=90)
        self.circle(view_id+'-shaft-side',cx,cy+2,r*.235,COLORS['disk_edge'],data_entity='shaft',data_object_part='decoration',data_view=view_id)
        self.circle(view_id+'-shaft',cx,cy,r*.235,COLORS['shaft'],COLORS['disk_edge'],1.1,data_entity='shaft',data_object_part='primary' if primary else 'detail',data_view=view_id)
        self.text(view_id+'-fixed','fixed',cx,cy+4.2,13.5,data_entity='shaft',data_object_part='decoration',data_view=view_id)
        self.views.append({'id':view_id,'center':[cx,cy],'radius':r,'contacts':centers,'opening_start_deg':start})
    def rotation(self,cx,cy,r,a0=-22,a1=68):
        pts=[pos(cx,cy,r,a0+i) for i in range(int(a1-a0)+1)]
        self.path('rotation-arc',pts,stroke=COLORS['ink'],sw=1.8,closed=False,data_relation='cover-rotation')
        tip=pts[-1];ang=math.radians(a1);tangent=[math.cos(ang),math.sin(ang)];normal=[-tangent[1],tangent[0]]
        base=[tip[0]-9*tangent[0],tip[1]-9*tangent[1]]
        tri=[tip,[base[0]+4*normal[0],base[1]+4*normal[1]],[base[0]-4*normal[0],base[1]-4*normal[1]]]
        self.path('rotation-head',tri,COLORS['ink'],data_relation='cover-rotation')
        self.arrow={'center':[cx,cy],'radius':r,'start_deg':a0,'end_deg':a1,'tip':tip,'base':base,'direction':'clockwise','rotation_deg':90}

def layout(kind):
    d=Drawing();d.text('demo-title','DEMO  /  Selective viewing',22,29,21,True,'start')
    if kind=='row':
        d.text('baseline-title','Whole-cover removal',123,81,17,True)
        d.text('concept-title','Rotating-cover concept',479,81,17,True)
        d.line('baseline-underline',24,92,222,92)
        d.line('concept-underline',263,92,704,92)
        d.text('baseline-state','Cover removed',123,122,15.5)
        d.text('initial-state','Initial',360,122,15.5)
        d.text('rotated-state','90° clockwise',596,122,15.5)
        d.view('baseline',123,232,85,None,True)
        d.view('initial',360,232,85,0)
        d.view('rotated',596,232,85,90)
        d.rotation(596,232,103)
        d.text('baseline-visible','All 8 visible',123,349,16,True)
        d.text('initial-visible','1, 2 visible',360,349,16,True)
        d.text('rotated-visible','3, 4 visible',596,349,16,True)
        d.line('state-transition',459,232,488,232,COLORS['muted'],1.5,data_relation='initial-to-rotated')
        d.path('state-transition-head',[[488,232],[481,228.5],[481,235.5]],COLORS['muted'],data_relation='initial-to-rotated')
    else:
        d.text('baseline-title','Whole-cover removal',139,80,17,True)
        d.view('baseline',139,211,67,None,True)
        d.text('baseline-state','All 8 visible',139,311,16,True)
        d.text('concept-title','Rotating-cover concept',491,60,17,True)
        d.view('initial',466,160,67,0)
        d.view('rotated',466,337,67,90)
        d.text('initial-state','Initial',574,150,15.5,False,'start')
        d.text('initial-visible','1, 2 visible',574,174,15.5,True,'start')
        d.text('rotated-state','90° clockwise',574,325,15.5,False,'start')
        d.text('rotated-visible','3, 4 visible',574,349,15.5,True,'start')
        d.rotation(466,337,80)
        d.line('state-transition',466,236,466,253,COLORS['muted'],1.5)
        d.path('state-transition-head',[[466,253],[462,247],[470,247]],COLORS['muted'])
        d.line('separator',290,84,290,400)
    if kind=='row':
        d.line('legend-rule',24,378,704,378)
        d.circle('legend-fixed',39,408,7,COLORS['disk'],COLORS['disk_edge'],1,data_object_part='legend')
        d.text('legend-fixed-label','Fixed disk + shaft',54,413,14.5,False,'start')
        d.circle('legend-cover',308,408,7,COLORS['cover'],data_object_part='legend')
        d.text('legend-cover-label','Rotating cover',323,413,14.5,False,'start')
        d.circle('legend-contact',555,408,7,COLORS['contact'],COLORS['contact_edge'],1,data_object_part='legend')
        d.text('legend-contact-label','Contact',570,413,14.5,False,'start')
    return d

def render(d,out,font,bold,poppler):
    ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
    root=ET.Element('{'+ns+'}svg',{'width':f'{WIDTH_MM}mm','height':f'{H/W*WIDTH_MM:.8f}mm','viewBox':f'0 0 {W} {H}'})
    ET.SubElement(root,'{'+ns+'}title').text='DEMO: selective viewing by rotating an opaque cover'
    ET.SubElement(root,'{'+ns+'}desc').text='Three views repeat one eight-contact device. The contact disk and shaft stay fixed. The removed-cover baseline shows all contacts; the two covered states show contacts 1 and 2, then 3 and 4.'
    c=canvas.Canvas(str(out.with_suffix('.pdf')),pagesize=(W*SCALE,H*SCALE),pageCompression=0,invariant=1)
    c.setTitle('DEMO - Selective viewing');c.setAuthor('Concept illustration from supplied geometry')
    pdfmetrics.registerFont(TTFont('UserArial',str(font)));pdfmetrics.registerFont(TTFont('UserArialBold',str(bold)))
    for q in d.items:
        attrs={k.replace('_','-'):str(v) for k,v in q.items() if k not in ('tag','text','points','closed')}
        if q['tag']=='path':attrs['d']=path_d(q['points'],q['closed'])
        el=ET.SubElement(root,'{'+ns+'}'+q['tag'],attrs)
        if q['tag']=='text':el.text=q['text']
        fill=q.get('fill','none');stroke=q.get('stroke','none')
        c.setLineWidth(q.get('stroke_width',1)*SCALE)
        if fill!='none':c.setFillColor(HexColor(fill))
        if stroke!='none':c.setStrokeColor(HexColor(stroke))
        if q['tag']=='circle':c.circle(q['cx']*SCALE,(H-q['cy'])*SCALE,q['r']*SCALE,stroke=int(stroke!='none'),fill=int(fill!='none'))
        elif q['tag']=='line':c.line(q['x1']*SCALE,(H-q['y1'])*SCALE,q['x2']*SCALE,(H-q['y2'])*SCALE)
        elif q['tag']=='path':
            p=c.beginPath();p.moveTo(q['points'][0][0]*SCALE,(H-q['points'][0][1])*SCALE)
            for x,y in q['points'][1:]:p.lineTo(x*SCALE,(H-y)*SCALE)
            if q['closed']:p.close()
            c.drawPath(p,stroke=int(stroke!='none'),fill=int(fill!='none'))
        elif q['tag']=='text':
            c.setFont('UserArialBold' if q['font_weight']=='bold' else 'UserArial',q['font_size']*SCALE)
            fun={'middle':c.drawCentredString,'start':c.drawString,'end':c.drawRightString}[q['text_anchor']]
            fun(q['x']*SCALE,(H-q['y'])*SCALE,q['text'])
    ET.ElementTree(root).write(out.with_suffix('.svg'),encoding='utf-8',xml_declaration=True)
    c.showPage();c.save()
    cmd=[str(poppler),'-r','300','-png','-singlefile',str(out.with_suffix('.pdf')),str(out)]
    run=subprocess.run(cmd,capture_output=True,text=True,check=True)
    return {'command':cmd,'returncode':run.returncode,'stderr':run.stderr}

def point_in_polygon(x,y,pts):
    inside=False
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]+pts[:1]):
        if ((y1>y)!=(y2>y)) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside

def audit(d,stem):
    root=ET.parse(stem.with_suffix('.svg')).getroot();els=list(root)
    raster=Image.open(stem.with_suffix('.png')).convert('RGB');arr=np.asarray(raster);sx=raster.width/W;sy=raster.height/H
    views={};errors=[]
    for v in d.views:
        contacts=[e for e in els if e.get('data-contact-id') and e.get('data-view')==v['id']]
        ids=[int(e.get('data-contact-id')) for e in contacts]
        if sorted(ids)!=list(range(1,9)):errors.append(v['id']+' has incorrect object set')
        cover=next((e for e in els if e.get('id')==v['id']+'-cover'),None)
        pts=[]
        if cover is not None:
            nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',cover.get('d'))));pts=list(zip(nums[0::2],nums[1::2]))
            if cover.get('fill')!=COLORS['cover']:errors.append('Incorrect opaque cover fill')
        geometrically_visible=[];raster_visible=[]
        for e in contacts:
            cid=int(e.get('data-contact-id'));x,y=float(e.get('cx')),float(e.get('cy'));rr=float(e.get('r'))
            a=FACTS['contacts'][cid-1]['angle_deg'];xx,yy=pos(*v['center'],v['radius']*.715,a)
            if abs(x-xx)>1e-4 or abs(y-yy)>1e-4:errors.append('contact coordinate mismatch')
            if not pts or not point_in_polygon(x,y,pts):geometrically_visible.append(cid)
            crop=arr[round((y-rr*.75)*sy):round((y+rr*.75)*sy),round((x-rr*.75)*sx):round((x+rr*.75)*sx)]
            rgb=np.array([237,189,103]);ratio=float((np.max(np.abs(crop.astype(int)-rgb),axis=2)<12).mean())
            if ratio>.12:raster_visible.append(cid)
        expected=list(range(1,9)) if v['id']=='baseline' else next(s['visible_ids'] for s in FACTS['states'] if s['id']==v['id'])
        if geometrically_visible!=expected or raster_visible!=expected:errors.append(v['id']+' visibility mismatch')
        views[v['id']]={'logical_ids':ids,'expected_visible_ids':expected,'actual_svg_occlusion_visible_ids':geometrically_visible,'actual_pdf_raster_visible_ids':raster_visible}
    arc=next(e for e in els if e.get('id')=='rotation-arc');nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',arc.get('d'))));arcpts=list(zip(nums[0::2],nums[1::2]))
    cx,cy=d.arrow['center'];angles=np.unwrap([math.atan2(x-cx,cy-y) for x,y in arcpts]);delta=math.degrees(angles[-1]-angles[0])
    if abs(delta-90)>.001:errors.append('rotation arrow not clockwise 90 degrees')
    tip=np.array(d.arrow['tip']);base=np.array(d.arrow['base']);tangent=np.array(arcpts[-1])-np.array(arcpts[-2]);alignment=float(np.dot(tip-base,tangent)/(np.linalg.norm(tip-base)*np.linalg.norm(tangent)))
    if alignment<.99:errors.append('arrowhead does not follow path tangent')
    pdf=PdfReader(stem.with_suffix('.pdf'));page=pdf.pages[0];mm=[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72]
    if abs(mm[0]-160)>.001 or len(pdf.pages)!=1:errors.append('page size/page count')
    if page.images:errors.append('bitmap embedded in vector PDF')
    sizes=[float(e.get('font-size'))*SCALE for e in els if e.tag.endswith('text')]
    if min(sizes)<8:errors.append('small type')
    return {'technical_status':'FAIL' if errors else 'PASS','checks_scope':'Custom checks extracted from actual SVG plus actual PDF raster. Not the skill scene-engine PASS.','errors':errors,'views':views,'rotation_arc_clockwise_degrees':delta,'arrowhead_tangent_cosine':alignment,'pdf_size_mm':mm,'min_type_pt':min(sizes),'svg_text_nodes':len(sizes),'pdf_images':len(page.images),'pdf_text':page.extract_text(),'hashes':{p.name:sha(p) for p in [stem.with_suffix(e) for e in ('.svg','.pdf','.png')]}}

def main():
    global FACTS
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path(__file__).with_name('source_facts.json'));p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Refusing to overwrite an existing output directory')
    for f in [a.input,a.font,a.bold_font,a.pdftoppm]:
        if not f.is_file():p.error('Missing dependency: '+str(f))
    FACTS=json.loads(a.input.read_text(encoding='utf-8'));a.out.mkdir(parents=True)
    results={};runs={};selected=None
    for kind,name in [('row','figure'),('vertical','alternative')]:
        d=layout(kind);stem=a.out/name;runs[name]=render(d,stem,a.font,a.bold_font,a.pdftoppm);results[name]=audit(d,stem)
        if name=='figure':selected=d
    im=Image.open(a.out/'figure.png').convert('RGB');ImageOps.grayscale(im).save(a.out/'figure-gray.png')
    # Approximate full-severity deuteranopia matrix; an aid, not clinical certification.
    rgb=np.asarray(im).astype(float)/255;linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    linear=np.clip(linear@mat.T,0,1);sim=np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(sim*255,0,255))).save(a.out/'figure-deuteranopia-approx.png')
    spec={'status':'DEMO','source_sha256':sha(a.input),'script_sha256':sha(__file__),'output':{'width_mm':160,'height_mm':H/W*160,'placement_width_mm':160,'viewBox':[0,0,W,H]},'primary_takeaway':'Only the cover turns; its aperture moves the visible pair from contacts 1-2 to contacts 3-4 while the contact disk and shaft remain fixed.','locked_values':FACTS,'roles':COLORS,'depth':'D1: schematic top view with shallow rim offsets; not measured 3D geometry.','views':selected.views,'direction_relation':selected.arrow,'entity_scope':'Exactly eight logical contacts. Baseline is canonical primary; initial and rotated views are explicitly repeated state representations. No transparent/cutaway auxiliary contacts.','font':{'regular':str(a.font),'regular_sha256':sha(a.font),'bold':str(a.bold_font),'bold_sha256':sha(a.bold_font),'svg_family':'Arial','pdf':'Embedded subsets; live searchable text'},'drawing_items':selected.items,'scientific_review_status':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED','human_reader_test':'NOT_RUN','author_acceptance':'REVIEW_REQUIRED'}
    (a.out/'figure_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.out/'audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.out/'commands.json').write_text(json.dumps({'python':sys.executable,'argv':sys.argv,'renders':runs},ensure_ascii=False,indent=2),encoding='utf-8')
    html='<!doctype html><meta charset="utf-8"><title>DEMO comparison, 160 mm</title><style>body{font-family:Arial;background:#f2f3f4;padding:24px}figure{margin:0 0 32px;background:white;width:160mm}img{display:block;width:160mm;height:auto}figcaption{padding:8px;font-size:12pt}</style>'
    for name,title in [('figure','Selected: aligned states'),('alternative','Alternative: vertical state change'),('figure-gray','Selected: grayscale'),('figure-deuteranopia-approx','Selected: approximate deuteranopia')]:html+=f'<figure><figcaption>{title}</figcaption><img src="{name}.svg" alt="{title}"></figure>' if name in ['figure','alternative'] else f'<figure><figcaption>{title}</figcaption><img src="{name}.png" alt="{title}"></figure>'
    (a.out/'preview.html').write_text(html,encoding='utf-8')
    print(json.dumps({k:{'technical_status':v['technical_status'],'errors':v['errors'],'visible_ids':{s:t['actual_pdf_raster_visible_ids'] for s,t in v['views'].items()},'min_type_pt':v['min_type_pt']} for k,v in results.items()},indent=2))
    return 1 if any(v['errors'] for v in results.values()) else 0

if __name__=='__main__':raise SystemExit(main())
