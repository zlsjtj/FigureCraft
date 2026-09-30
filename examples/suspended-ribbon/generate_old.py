"""Original suspended-bridge DEMO; editable orthographic vector geometry.

Run with explicit --font, --bold-font, --pdftoppm, --input and --out.
The output folder must not already exist. All coordinates below are geometric
coordinates only; no dimensional measurement or physical simulation is implied.
"""
from pathlib import Path
import argparse, hashlib, json, math, subprocess, sys
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

W, H = 160*72/25.4, 95*72/25.4
TRACE = [(5,15),(10,15),(10,13.7),(14,13.7),(14,16.3),
         (18,16.3),(18,13.7),(22,13.7),(22,16.3),(26,16.3),
         (26,13.7),(30,13.7),(30,16.3),(34,16.3),(34,15),(39,15)]
AZ, EL, SCALE = math.radians(-80), math.radians(50), 6.1
RIGHT = np.array([-math.sin(AZ),math.cos(AZ),0.])
UP = np.array([-math.sin(EL)*math.cos(AZ),-math.sin(EL)*math.sin(AZ),math.cos(EL)])
VIEW = np.array([math.cos(EL)*math.cos(AZ),math.cos(EL)*math.sin(AZ),math.sin(EL)])
ORIGIN = (82,204)
COLORS = {'frame_top':'#DCE3EB','frame_front':'#AAB7C9','frame_right':'#91A0B7',
          'frame_inner_back':'#A6B4C6','frame_inner_left':'#BBC6D4',
          'frame_edge':'#73849B','ribbon_top':'#3896A4','ribbon_front':'#276B79',
          'ribbon_right':'#2C7987','ribbon_edge':'#256875','metal_top':'#E1AC49',
          'metal_side':'#A77826','metal_edge':'#926921','text':'#243442','leader':'#5C6B77'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def proj(p):
    p=np.asarray(p,dtype=float)
    return (ORIGIN[0]+SCALE*float(p@RIGHT),ORIGIN[1]-SCALE*float(p@UP))
def polygon_offset(polyline, halfwidth):
    p=np.array(polyline,dtype=float)
    u=np.diff(p,axis=0);u=u/np.linalg.norm(u,axis=1)[:,None]
    n=np.column_stack([-u[:,1],u[:,0]])
    offsets=[n[0]*halfwidth]
    for i in range(1,len(p)-1):
        bis=n[i-1]+n[i]
        offsets.append(bis*halfwidth/float(bis@n[i]))
    offsets.append(n[-1]*halfwidth)
    offsets=np.array(offsets)
    return np.vstack([p+offsets,(p-offsets)[::-1]])

class Figure:
    def __init__(self): self.items=[]
    def poly(self,id,pts,fill,stroke,width=.45,entity=None,points3d=None):
        self.items.append(dict(type='polygon',id=id,points=pts,fill=fill,stroke=stroke,
                               stroke_width=width,entity=entity,points3d=points3d))
    def face(self,id,pts,color,entity,edge=None,width=.45):
        self.poly(id,[proj(p) for p in pts],COLORS[color],COLORS[edge or entity+'_edge'],width,entity,pts)
    def ring(self,id,outer,inner):
        self.items.append(dict(type='ring',id=id,loops=[[proj(p) for p in outer],[proj(p) for p in inner]],
                               fill=COLORS['frame_top'],stroke=COLORS['frame_edge'],stroke_width=.5,
                               entity='frame',points3d=[outer,inner]))
    def leader(self,id,pts,target,void=False):
        self.items.append(dict(type='polyline',id=id,points=pts+[proj(target)],fill='none',
                               stroke=COLORS['leader'],stroke_width=.55,relation='annotation',
                               target3d=target,arrow_required=False))
        if not void:
            self.items.append(dict(type='circle',id=id+'-anchor',center=proj(target),radius=.8,
                                   fill=COLORS['leader'],stroke='none',stroke_width=0))
    def text(self,id,text,x,y):
        self.items.append(dict(type='text',id=id,text=text,x=x,y=y,font_size=10,
                               fill=COLORS['text'],font_family='Arial',font_weight='normal'))

def build():
    f=Figure()
    f.face('frame-front',[(0,0,0),(44,0,0),(44,0,4),(0,0,4)],'frame_front','frame')
    f.face('frame-right',[(44,0,0),(44,30,0),(44,30,4),(44,0,4)],'frame_right','frame')
    f.face('hole-back-wall',[(8,22,0),(36,22,0),(36,22,4),(8,22,4)],'frame_inner_back','frame')
    f.face('hole-left-wall',[(8,8,0),(8,22,0),(8,22,4),(8,8,4)],'frame_inner_left','frame')
    f.ring('frame-top',[(0,0,4),(44,0,4),(44,30,4),(0,30,4)],
           [(8,8,4),(36,8,4),(36,22,4),(8,22,4)])
    f.face('ribbon-front',[(5,13,4),(39,13,4),(39,13,4.4),(5,13,4.4)],'ribbon_front','ribbon',width=.35)
    f.face('ribbon-right',[(39,13,4),(39,17,4),(39,17,4.4),(39,13,4.4)],'ribbon_right','ribbon',width=.35)
    f.face('ribbon-top',[(5,13,4.4),(39,13,4.4),(39,17,4.4),(5,17,4.4)],'ribbon_top','ribbon',width=.4)
    outline=polygon_offset(TRACE,.35/2)
    # This polygon is clockwise. The left normal therefore points outward.
    for i,(a,b) in enumerate(zip(outline,np.roll(outline,-1,axis=0))):
        d=b-a;n=np.array([-d[1],d[0],0.])
        if float(n@VIEW)>1e-8:
            xyz=[[*a,4.4],[*b,4.4],[*b,4.48],[*a,4.48]]
            f.face('metal-side-'+str(i),xyz,'metal_side','metal',width=.12)
    f.face('metal-top',[[*p,4.48] for p in outline],'metal_top','metal',width=.18)
    f.leader('metal-label-line',[(69,120),(106,120)],(7,15,4.48))
    f.text('metal-label','Metal trace',12,123)
    f.leader('ribbon-label-line',[(379,139),(342,139)],(37.5,16.9,4.4))
    f.text('ribbon-label','Thin ribbon',383,142)
    f.leader('frame-label-line',[(115,247),(137,225)],(11,0,2))
    f.text('frame-label','Monolithic frame',29,251)
    f.leader('opening-label-line',[(302,246),(302,218)],(25,10.7,2.5),void=True)
    f.text('opening-label','Through opening',284,258)
    return f,outline

def write_svg(f,path):
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="95mm" viewBox="0 0 {W:.8f} {H:.8f}">',
         '<title>Suspended ribbon with a continuous metal trace</title>',
         '<desc>Fictional geometry DEMO. A single frame has an open through-hole, spanned by one continuous ribbon carrying one continuous metal trace. No bottom plate or central support is present.</desc>',
         f'<rect id="canvas" width="{W:.8f}" height="{H:.8f}" fill="#FFFFFF"/>']
    def pairs(pts): return ' '.join(f'{x:.6f},{y:.6f}' for x,y in pts)
    for o in f.items:
        extra=''
        if o.get('entity'):extra=f' data-entity="{o["entity"]}" data-logical-id="{o["entity"]}-1"'
        if o.get('relation'):extra+=' data-relation="annotation"'
        at=f'id="{o["id"]}"{extra} fill="{o["fill"]}"'
        if o['type']!='text':at+=f' stroke="{o["stroke"]}" stroke-width="{o["stroke_width"]}" stroke-linejoin="round" stroke-linecap="round"'
        if o['type'] in ('polygon','polyline'):
            out.append(f'<{o["type"]} {at} points="{pairs(o["points"])}"/>')
        elif o['type']=='ring':
            d=' '.join('M '+' L '.join(f'{x:.6f} {y:.6f}' for x,y in loop)+' Z' for loop in o['loops'])
            out.append(f'<path {at} fill-rule="evenodd" d="{d}"/>')
        elif o['type']=='circle':out.append(f'<circle {at} cx="{o["center"][0]:.6f}" cy="{o["center"][1]:.6f}" r="{o["radius"]}"/>')
        elif o['type']=='text':out.append(f'<text {at} x="{o["x"]}" y="{o["y"]}" font-family="Arial" font-size="10" font-weight="normal">{escape(o["text"])}</text>')
    out.append('</svg>');path.write_text('\n'.join(out),encoding='utf-8')

def write_pdf(f,path,font):
    pdfmetrics.registerFont(TTFont('Arial',str(font)))
    c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1)
    c.setTitle('Suspended ribbon geometry DEMO');c.setAuthor('FigureCraft baseline independent trial')
    c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,W,H,fill=1,stroke=0)
    for o in f.items:
        fill=int(o['fill']!='none');stroke=int(o.get('stroke','none')!='none')
        if fill:c.setFillColor(HexColor(o['fill']))
        if stroke:c.setStrokeColor(HexColor(o['stroke']));c.setLineWidth(o['stroke_width'])
        c.setLineJoin(1);c.setLineCap(1)
        if o['type']=='text':
            c.setFont('Arial',o['font_size']);c.drawString(o['x'],H-o['y'],o['text']);continue
        if o['type']=='circle':
            x,y=o['center'];c.circle(x,H-y,o['radius'],fill=fill,stroke=stroke);continue
        p=c.beginPath()
        loops=o['loops'] if o['type']=='ring' else [o['points']]
        for pts in loops:
            p.moveTo(pts[0][0],H-pts[0][1])
            for x,y in pts[1:]:p.lineTo(x,H-y)
            if o['type']!='polyline':p.close()
        c.drawPath(p,fill=fill,stroke=stroke,fillMode=0)
    c.showPage();c.save()

BODY='''The geometric DEMO comprises three continuous entities: a monolithic frame, a thin ribbon, and a metal trace. A rectangular opening passes through the full thickness of the frame. The ribbon bridges this opening and rests on the frame at both ends, leaving its central span unsupported. A single metal trace follows a repeated folded path on the upper surface of the ribbon and terminates on the ribbon itself. This construction specifies spatial relationships only; no device application or performance is assigned.'''
CAPTION='''Figure 1. Suspended-ribbon geometry DEMO. An orthographic view shows a monolithic frame with a rectangular through-opening, a continuous ribbon contacting the frame at both ends, and a continuous metal trace on the ribbon's upper surface. The opening has no bottom plate, and the central ribbon span has no supporting pillar. Colors identify the three entities; fine gray leaders identify features without implying physical transport. The geometry is fictional and carries no measurement units or performance data.'''
ALT='''A pale blue-gray rectangular frame surrounds an open rectangular hole. A thin teal ribbon bridges the hole from left to right and contacts the top of the frame at both ends. A gold line runs continuously along the ribbon through alternating folds before ending on the ribbon. The visible interior walls show that the opening passes through the frame. There is no support under the central ribbon span.'''

def main():
    a=argparse.ArgumentParser();a.add_argument('--font',required=True,type=Path);a.add_argument('--bold-font',required=True,type=Path)
    a.add_argument('--pdftoppm',required=True,type=Path);a.add_argument('--input',required=True,type=Path);a.add_argument('--out',required=True,type=Path)
    args=a.parse_args()
    if args.out.exists():raise SystemExit('Refusing to overwrite an existing output folder')
    args.out.mkdir(parents=True)
    # Read the authorized source on every build and bind it to every output.
    input_text=args.input.read_text(encoding='utf-8-sig')
    assert 'x=8..36' in input_text and 'z=4..4.4' in input_text
    f,outline=build();write_svg(f,args.out/'figure.svg');write_pdf(f,args.out/'figure.pdf',args.font)
    cmd=[str(args.pdftoppm),'-png','-singlefile','-r','300',str(args.out/'figure.pdf'),str(args.out/'figure')]
    p=subprocess.run(cmd,capture_output=True,text=True);p.check_returncode()
    rgb=Image.open(args.out/'figure.png').convert('RGB')
    ImageOps.grayscale(rgb).save(args.out/'figure-grayscale.png',dpi=(300,300))
    srgb=np.asarray(rgb,dtype=float)/255
    lin=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    sim=np.clip(lin@matrix.T,0,1)
    sim=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.round(sim*255).astype('uint8')).save(args.out/'figure-deuteranopia-approx.png',dpi=(300,300))
    texts=[x for x in f.items if x['type']=='text']
    spec={'evidence_status':'FICTIONAL_GEOMETRY_DEMO','input_sha256':sha(args.input),
          'main_reading':'One continuous ribbon bridges a bottomless through-opening and carries one continuous metal trace.',
          'output':{'width_mm':160,'height_mm':95,'placement_width_mm':160,'png_dpi':300,'label_pt':10,'vector_status':'FULL_VECTOR'},
          'entities':{'frame':{'count':1,'bounds':[0,44,0,30,0,4],'through_hole':[8,36,8,22,0,4]},
                      'ribbon':{'count':1,'bounds':[5,39,13,17,4,4.4]},
                      'metal':{'count':1,'centerline':TRACE,'width':.35,'bottom_z':4.4,'top_z':4.48,'ends':'flush on ribbon'}},
          'relations':[{'from':'ribbon','to':'frame','kind':'contact','areas':[[5,8,13,17,4],[36,39,13,17,4]]},
                       {'from':'metal','to':'ribbon','kind':'surface_contact','z':4.4},
                       {'from':'ribbon','to':'through_hole','kind':'unsupported_span','x':[8,36]}],
          'forbidden_entities':['bottom plate','support pillar','end pad','connection box'],
          'projection':{'kind':'orthographic','azimuth_deg':-80,'elevation_deg':50,'right':RIGHT.tolist(),'up':UP.tolist(),'view':VIEW.tolist(),'points_per_geometry_unit':SCALE,'origin_pt':ORIGIN},
          'shading':'Constant per planar face for legibility; no physical lighting or field simulation.',
          'role_colors':COLORS,'exact_labels':[t['text'] for t in texts],
          'items':f.items,'metal_plan_polygon':outline.tolist()}
    (args.out/'figure_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.out/'body-and-caption.md').write_text('## English paragraph\n\n'+BODY+'\n\n## Figure caption\n\n'+CAPTION+'\n\n## Alternative text\n\n'+ALT+'\n',encoding='utf-8')
    # Checks tied to actual exported SVG and PDF, not only the content contract.
    root=ET.parse(args.out/'figure.svg').getroot()
    entities=sorted({el.get('data-entity') for el in root.iter() if el.get('data-entity')})
    pdf=PdfReader(args.out/'figure.pdf');page=pdf.pages[0];pdf_text=page.extract_text()
    checks={'entity_types_in_actual_svg':entities,'entity_types_match':entities==['frame','metal','ribbon'],
            'svg_image_nodes':len(root.findall('.//{http://www.w3.org/2000/svg}image')),
            'svg_text_nodes':len(root.findall('.//{http://www.w3.org/2000/svg}text')),
            'svg_labels_match':all(t['text'] in ''.join(root.itertext()) for t in texts),
            'pdf_pages':len(pdf.pages),'pdf_dimensions_mm':[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72],
            'pdf_searchable_labels_match':all(t['text'] in pdf_text for t in texts),'png_pixels':rgb.size,
            'centerline_count':len(TRACE),'continuous_centerline':all(np.linalg.norm(np.array(b)-a)>0 for a,b in zip(TRACE,TRACE[1:])),
            'metal_inside_ribbon':bool(np.all(outline[:,0]>=5) and np.all(outline[:,0]<=39) and np.all(outline[:,1]>=13) and np.all(outline[:,1]<=17)),
            'minimum_metal_edge_clearance_y':float(min(outline[:,1].min()-13,17-outline[:,1].max())),
            'contact_z_exact':4.4==spec['entities']['metal']['bottom_z'],
            'label_font_pt':[t['font_size'] for t in texts],'arrow_markers':len(root.findall('.//{http://www.w3.org/2000/svg}marker')),
            'orthogonal_camera':bool(np.allclose(np.array([RIGHT,UP,VIEW])@np.array([RIGHT,UP,VIEW]).T,np.eye(3)))}
    check={'status':'PASS' if all(checks[k] for k in ['entity_types_match','svg_labels_match','pdf_searchable_labels_match','continuous_centerline','metal_inside_ribbon','contact_z_exact','orthogonal_camera']) else 'FAIL',
           'technical_scope':'Explicit checks only; not whole-figure scientific or aesthetic approval','checks':checks,
           'normal_view':'figure.png','grayscale':'figure-grayscale.png','color_vision':{'file':'figure-deuteranopia-approx.png','condition':'approximate deuteranopia','linear_rgb_matrix':matrix.tolist(),'scope':'single fixed-matrix screen preview, not clinical validation'},
           'scientific_review_status':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED','author_acceptance':'PENDING','overall_status':'REVIEW_REQUIRED',
           'not_run':['Word placement','human reader study','physical print','other color vision conditions','physical simulation'],
           'render_command':cmd,'render_exit_code':p.returncode,'stderr':p.stderr,
           'source_sha256':sha(__file__),'input_sha256':sha(args.input),'font_sha256':sha(args.font),
           'artifacts':{q.name:sha(q) for q in args.out.iterdir() if q.is_file()}}
    (args.out/'checks.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(args.out),'checks':checks,'status':check['status']},indent=2))

if __name__=='__main__':main()
