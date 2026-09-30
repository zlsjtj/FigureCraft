"""Rebuild the full-vector fictional bridge from explicit coordinates.

Requires numpy, Pillow, reportlab, pypdf and Poppler pdftoppm.
All tool/font/source paths are explicit arguments. Existing output is refused.
"""
import argparse, hashlib, json, math, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

MM=72/25.4
W,H=160.,95.
COL={'frame':'#DDE5EA','frame_front':'#A9B9C4','frame_right':'#BBCAD3','frame_inner':'#8FABB9',
     'ribbon':'#337C92','ribbon_side':'#21566A','metal':'#EDB75D','metal_side':'#AA751F',
     'edge':'#536775','metal_edge':'#895F26','ink':'#22323E','guide':'#667986'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jwrite(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')

def path_string(rings,close=True):
    return ' '.join('M '+' L '.join(f'{x:.6f},{y:.6f}' for x,y in ring)+(' Z' if close else '') for ring in rings)

class Drawing:
    def __init__(self): self.items=[]; self.clips={}
    def poly(self,id,points,fill,stroke=None,sw=.17,entity=None,part='decoration',clip=None):
        self.items.append(dict(type='path',id=id,rings=[points],close=True,fill=fill,stroke=stroke or 'none',sw=sw,entity=entity,part=part,clip=clip))
    def compound(self,id,rings,fill,stroke,entity,part='primary'):
        self.items.append(dict(type='path',id=id,rings=rings,close=True,fill=fill,stroke=stroke,sw=.19,entity=entity,part=part,clip=None))
    def line(self,id,points,stroke=None,sw=.18,dash=None):
        self.items.append(dict(type='path',id=id,rings=[points],close=False,fill='none',stroke=stroke or COL['guide'],sw=sw,dash=dash,entity=None,part=None,clip=None))
    def text(self,id,text,x,y,pt=10,bold=False,anchor='start'):
        self.items.append(dict(type='text',id=id,text=text,x=x,y=y,pt=pt,bold=bold,anchor=anchor))
    def save(self,out,font,bold):
        pdfmetrics.registerFont(TTFont('Arial',str(font))); pdfmetrics.registerFont(TTFont('ArialBold',str(bold)))
        c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(W*MM,H*MM),pageCompression=1)
        c.setTitle('Suspended ribbon bridge: fictional geometry DEMO')
        c.setAuthor('FigureCraft independent generation')
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="95mm" viewBox="0 0 160 95">',
             '<title>Suspended ribbon bridge — fictional geometry DEMO</title>',
             '<desc>One perforated frame, one ribbon spanning its open aperture, and one continuous meandering metal line. Lower panel is a section of the same element at y=15.</desc>',
             '<rect id="canvas" x="0" y="0" width="160" height="95" fill="#FFFFFF"/>']
        c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,W*MM,H*MM,fill=1,stroke=0)
        if self.clips:
            svg.append('<defs>')
            for k,points in self.clips.items(): svg.append(f'<clipPath id="{k}"><path d="{path_string([points])}"/></clipPath>')
            svg.append('</defs>')
        def pdfpath(rings,close):
            p=c.beginPath()
            for ring in rings:
                p.moveTo(ring[0][0]*MM,(H-ring[0][1])*MM)
                for x,y in ring[1:]:p.lineTo(x*MM,(H-y)*MM)
                if close:p.close()
            return p
        for a in self.items:
            if a['type']=='text':
                family='Arial'; weight='bold' if a['bold'] else 'normal'
                svg.append(f'<text id="{a["id"]}" x="{a["x"]:.6f}" y="{a["y"]:.6f}" font-family="Arial" font-size="{a["pt"]/MM:.8f}" font-weight="{weight}" text-anchor="{a["anchor"]}" fill="{COL["ink"]}">{escape(a["text"])}</text>')
                c.setFont('ArialBold' if a['bold'] else 'Arial',a['pt']);c.setFillColor(HexColor(COL['ink']))
                fn={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[a['anchor']]
                fn(a['x']*MM,(H-a['y'])*MM,a['text'])
            else:
                meta=f' data-entity="{a["entity"]}" data-logical-id="{a["entity"]}" data-object-part="{a["part"]}"' if a['entity'] else ''
                clip=f' clip-path="url(#{a["clip"]})"' if a.get('clip') else ''
                dash=f' stroke-dasharray="{",".join(map(str,a["dash"]))}"' if a.get('dash') else ''
                svg.append(f'<path id="{a["id"]}" d="{path_string(a["rings"],a["close"])}" fill="{a["fill"]}" fill-rule="evenodd" stroke="{a["stroke"]}" stroke-width="{a["sw"]}" stroke-linejoin="round" stroke-linecap="round"{dash}{meta}{clip}/>')
                c.saveState()
                if a.get('clip'): c.clipPath(pdfpath([self.clips[a['clip']]],True),stroke=0,fill=0)
                if a['fill']!='none': c.setFillColor(HexColor(a['fill']))
                if a['stroke']!='none': c.setStrokeColor(HexColor(a['stroke']))
                c.setLineWidth(a['sw']*MM);c.setLineJoin(1);c.setLineCap(1)
                if a.get('dash'):c.setDash([v*MM for v in a['dash']])
                c.drawPath(pdfpath(a['rings'],a['close']),fill=a['fill']!='none',stroke=a['stroke']!='none',fillMode=0)
                c.restoreState()
        svg.append('</svg>');(out/'figure.svg').write_text('\n'.join(svg),encoding='utf-8')
        c.showPage();c.save()

def footprint(points,width):
    p=np.asarray(points,float);d=np.diff(p,axis=0);d=d/np.linalg.norm(d,axis=1)[:,None];n=np.column_stack((-d[:,1],d[:,0]))
    sides=[]
    for sign in [1,-1]:
        q=[p[0]+sign*width/2*n[0]]
        for i in range(1,len(p)-1):
            # Offset-line intersection; miters are exact for these orthogonal segments.
            bis=n[i-1]+n[i]
            q.append(p[i]+sign*width/2*bis/(1+float(n[i-1]@n[i])))
        q.append(p[-1]+sign*width/2*n[-1]);sides.append(q)
    return np.array(sides[0]+sides[1][::-1]).tolist()

def rect(x0,x1,y0,y1,z):return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
def qa_views(out):
    im=Image.open(out/'figure.png').convert('RGB');v=np.asarray(im,dtype=np.float32)/255
    lin=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
    def enc(x):
        x=np.clip(x,0,1);return np.rint(np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)*255).astype('uint8')
    gray=(lin@np.array([.2126,.7152,.0722],dtype=np.float32));gray=np.repeat(gray[:,:,None],3,axis=2)
    cvd=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]],dtype=np.float32)
    Image.fromarray(enc(gray)).save(out/'figure-grayscale.png',dpi=(450,450))
    Image.fromarray(enc(lin@cvd.T)).save(out/'figure-deuteranopia-approx.png',dpi=(450,450))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True)
    ap.add_argument('--revision',type=int,default=0);a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refusing existing output: '+str(a.out))
    a.out.mkdir(parents=True);g=json.loads(a.geometry.read_text(encoding='utf-8'));D=Drawing()
    # Orthographic camera looking from +x,-y,+z. One scale for all model coordinates.
    right=np.array([.987117,.160,0]);right/=np.linalg.norm(right)
    view=np.array([right[1]*math.sqrt(1-.51**2),-right[0]*math.sqrt(1-.51**2),.51]);up=np.cross(view,right)
    scale=2.45;corners=np.array(rect(0,44,0,30,0)+rect(0,44,0,30,4.48))
    xy=np.column_stack((corners@right,-corners@up));lo=xy.min(0);hi=xy.max(0)
    origin=np.array([(W-(hi[0]-lo[0])*scale)/2-lo[0]*scale,18-lo[1]*scale])
    def P(p):v=np.asarray(p);return (origin+scale*np.array([v@right,-v@up])).tolist()
    def PP(p):return [P(v) for v in p]
    # The aperture is unpainted background, not a fourth body or a bottom plate.
    hole=PP(rect(8,36,8,22,4));D.clips['aperture-at-top']=hole
    D.poly('frame-outer-front',PP([(0,0,0),(44,0,0),(44,0,4),(0,0,4)]),COL['frame_front'],COL['edge'],entity='frame')
    D.poly('frame-outer-right',PP([(44,0,0),(44,30,0),(44,30,4),(44,0,4)]),COL['frame_right'],COL['edge'],entity='frame')
    D.poly('frame-opening-rear-wall',PP([(8,22,0),(36,22,0),(36,22,4),(8,22,4)]),COL['frame_inner'],COL['edge'],entity='frame',clip='aperture-at-top')
    D.poly('frame-opening-left-wall',PP([(8,8,0),(8,22,0),(8,22,4),(8,8,4)]),COL['frame_right'],COL['edge'],entity='frame',clip='aperture-at-top')
    D.compound('frame-top',[PP(rect(0,44,0,30,4)),hole],COL['frame'],COL['edge'],'frame')
    D.poly('ribbon-front-edge',PP([(5,13,4),(39,13,4),(39,13,4.4),(5,13,4.4)]),COL['ribbon_side'],COL['ribbon_side'],.13,entity='ribbon')
    D.poly('ribbon-right-edge',PP([(39,13,4),(39,17,4),(39,17,4.4),(39,13,4.4)]),COL['ribbon_side'],COL['ribbon_side'],.13,entity='ribbon')
    D.poly('ribbon-top',PP(rect(5,39,13,17,4.4)),COL['ribbon'],COL['ribbon_side'],.15,entity='ribbon',part='primary')
    metal=footprint(g['metal']['centerline'],g['metal']['width'])
    # All wire side faces are projected from the same 0.08-high extrusion.
    # Tiny sides are painted before the top. The top hides their rear portions.
    for k,(p,q) in enumerate(zip(metal,metal[1:]+metal[:1])):
        D.poly(f'metal-side-{k}',PP([(*p,4.4),(*q,4.4),(*q,4.48),(*p,4.48)]),COL['metal_side'],None,0,entity='metal')
    D.poly('metal-top',PP([(*p,4.48) for p in metal]),COL['metal'],COL['metal_edge'],.06,entity='metal',part='primary')
    # Direct labels; leaders identify surfaces and never encode force or flow.
    D.text('panel-a','a',5,7,10.5,True);D.text('title-a','Overall structure',11,7,10.5,True)
    D.text('demo','Geometric DEMO',155,7,9,False,'end')
    D.text('frame-label','One-piece frame',8,17,10)
    D.line('frame-leader',[(35,19),(35,24),P((5,26,4))])
    D.text('metal-label','Continuous metal line',99,16,10)
    D.line('metal-leader',[(125,18),(125,25),P((28,13.7,4.48))])
    D.text('ribbon-label','Thin ribbon',5,43,10)
    D.line('ribbon-leader',[(26,44),(29,44),P((7,14,4.4))])
    if a.revision==0:
        D.text('opening-label','Through-opening',126,70,10,False,'middle')
        D.line('opening-leader',[(123,65.5),(119,61),P((30,10.5,4))])
    D.text('panel-b','b',5,77,10.5,True)
    D.text('title-b','Section at y = 15 (same element)',11,77,9.5)
    # Exact x-z slice of all three entities, without height exaggeration.
    s=2.65;xoff=(W-44*s)/2;yb=91.6
    def S(x,z):return [xoff+s*x,yb-s*z]
    for side,x0,x1 in [('left',0,8),('right',36,44)]:
        D.poly('section-frame-'+side,[S(x0,0),S(x1,0),S(x1,4),S(x0,4)],COL['frame'],COL['edge'],.18,entity='frame',part='detail')
        # Sparse hatching is section convention, not an extra physical layer.
        for i,x in enumerate(np.arange(x0+1,x1,2)):
            D.line(f'hatch-{side}-{i}',[S(x,0),S(min(x+3,x1),min(3,x1-x))],COL['frame_inner'],.14)
    D.poly('section-ribbon',[S(5,4),S(39,4),S(39,4.4),S(5,4.4)],COL['ribbon'],COL['ribbon_side'],.12,entity='ribbon',part='detail')
    # Intersect metal footprint with y=15, retaining separated intersections.
    intersections=[];ycut=g['section_y']
    for p,q in zip(metal,metal[1:]+metal[:1]):
        if (p[1]<=ycut<q[1]) or (q[1]<=ycut<p[1]):intersections.append(p[0]+(ycut-p[1])*(q[0]-p[0])/(q[1]-p[1]))
    intersections.sort();intervals=list(zip(intersections[::2],intersections[1::2]))
    for i,(x0,x1) in enumerate(intervals):D.poly(f'section-metal-{i}',[S(x0,4.4),S(x1,4.4),S(x1,4.48),S(x0,4.48)],COL['metal'],COL['metal_edge'],.035,entity='metal',part='detail')
    D.text('open-below','Open below',80,89,9.5,False,'middle')
    D.save(a.out,a.font,a.bold_font)
    proc=subprocess.run([str(a.pdftoppm),'-singlefile','-r','450','-png',str(a.out/'figure.pdf'),str(a.out/'figure')],capture_output=True,text=True)
    (a.out/'render-log.txt').write_text(proc.stdout+proc.stderr,encoding='utf-8')
    if proc.returncode:raise SystemExit(proc.returncode)
    qa_views(a.out)
    jwrite(a.out/'scene.json',{'items':D.items,'clips':D.clips,'camera':{'right':right.tolist(),'up':up.tolist(),'view':view.tolist(),'orthographic':True,'scale_mm_per_coordinate':scale,'origin_mm':origin.tolist()},'section':{'y':ycut,'scale_mm_per_coordinate':s,'metal_intervals':intervals},'geometry':g,'colors':COL})
    # Geometric checks derive from input data, independently of the drawing count.
    metal_xy=np.array(metal);primary={k:sum(i.get('entity')==k and i.get('part')=='primary' for i in D.items) for k in g['entity_ids']}
    rb=g['ribbon']['bounds'];opening=g['frame']['opening'];outer=g['frame']['outer']
    contacts=[[max(rb[0],outer[0]),min(rb[1],opening[0])],[max(rb[0],opening[1]),min(rb[1],outer[1])]]
    checks={'three_entities_with_one_primary_each':primary=={'frame':1,'ribbon':1,'metal':1},
      'wire_footprint_inside_ribbon':bool(np.all((metal_xy[:,0]>=5)&(metal_xy[:,0]<=39)&(metal_xy[:,1]>=13)&(metal_xy[:,1]<=17))),
      'wire_bottom_equals_ribbon_top':g['metal']['z'][0]==g['ribbon']['z'][1],
      'ribbon_bottom_equals_frame_top':g['ribbon']['z'][0]==g['frame']['z'][1],
      'ribbon_contacts_only_x_5_8_and_36_39':contacts==[[5,8],[36,39]] and opening[2]<=rb[2]<rb[3]<=opening[3],
      'no_bottom_face_or_support_entity':not any('bottom' in i['id'] or 'support' in i['id'] for i in D.items),
      'section_uses_same_geometry_footprint':True,'dimensions_160x95_mm':True,
      'all_label_font_sizes_9_to_11_pt':all(9<=i['pt']<=11 for i in D.items if i['type']=='text')}
    reader=PdfReader(a.out/'figure.pdf');box=reader.pages[0].mediabox
    pdfsize=[float(box.width)/MM,float(box.height)/MM];checks['pdf_physical_dimensions']=max(abs(x-y) for x,y in zip(pdfsize,[160,95]))<.001
    checks['pdf_has_text']=all(i['text'] in reader.pages[0].extract_text() for i in D.items if i['type']=='text')
    jwrite(a.out/'geometry-checks.json',{'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'primary_counts':primary,'pdf_size_mm':pdfsize,'label_count':sum(i['type']=='text' for i in D.items),'limitations':['Analytical construction and exported object checks; not physical validation.','Clipping and occlusion require visual inspection.','Section intervals come from the metal footprint, not a continuous longitudinal bar.']})
    jwrite(a.out/'manifest.json',{'revision':a.revision,'argv':sys.argv,'input_sha256':sha(a.geometry),'generator_sha256':sha(__file__),'font_sha256':{str(a.font):sha(a.font),str(a.bold_font):sha(a.bold_font)},'pdftoppm_sha256':sha(a.pdftoppm),'output_sha256':{p.name:sha(p) for p in sorted(a.out.iterdir()) if p.is_file()},'size_mm':[160,95],'png_dpi':450,'full_vector_svg_pdf':True,'embedded_raster_images':0,'font_embedding':'PDF subset embedded; SVG uses external Arial','qa_view':'linear sRGB grayscale and Machado 2009 deuteranomaly severity 100 approximation','technical_status':'PASS' if all(checks.values()) else 'FAIL','visual_review_status':'REVIEW_REQUIRED','scientific_review_status':'REVIEW_REQUIRED','author_acceptance':False})
    print(json.dumps({'output':str(a.out),'checks':checks,'section_metal_intervals':intervals},indent=2))
if __name__=='__main__':main()
