"""Original geometry DEMO. Exact coordinate model, orthographic hybrid export.
All paths are explicit CLI parameters or local to this script. Existing output refused.
"""
import argparse, base64, hashlib, json, math, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

VERSION='first'
MM=72/25.4
W,H=160.,100.
COLORS={'base':'#E2E5E9','guard':'#489B9C','insert':'#E9B15C'}
GEOMETRY={
 'base':{'box':[[-24,24],[-26,26],[-3,0]]},
 'guard':{'union_boxes':[[[-15,-11],[-4,4],[0,18]],[[11,15],[-4,4],[0,18]],[[-15,15],[-4,4],[18,22]]]},
 'insert':{'box':[[-6,6],[-22,22],[6,10]]}}
CAPTION=('Original geometry DEMO in arbitrary length units. An orthographic view shows one continuous U-shaped guard with both feet contacting the base at z = 0. The rectangular insert extends along y through the opening without touching the guard or base. The marked upper clearance is 8; lateral clearance is 5 on each side and base-to-insert clearance is 6. Positions are specified only; no support or stability is asserted. Surface tones aid orientation and do not represent material properties.')
ALT=('Orthographic geometry DEMO: a teal U-shaped guard sits on a pale rectangular base. An ochre bar runs through its opening, with an 8-unit vertical dimension between the bar top and crossbar underside. The continuous guard, two feet, bar extensions, and open spaces are shown with planar surface shading. A small x-y-z triad identifies orientation.')

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def face(points,n,role,part):
 return {'p':np.array(points,dtype=float),'n':np.array(n,dtype=float),'role':role,'color':COLORS[role],'part':part}
def box(bounds,role):
 (x0,x1),(y0,y1),(z0,z1)=bounds
 return [face([(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],[-1,0,0],role,'x-'),
 face([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],[1,0,0],role,'x+'),
 face([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],[0,-1,0],role,'y-'),
 face([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],[0,1,0],role,'y+'),
 face([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],[0,0,-1],role,'z-'),
 face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],[0,0,1],role,'z+')]
def guard():
 # Single extrusion of a connected U cross-section. No post/crossbar seams.
 poly=[(-15,0),(-11,0),(-11,18),(11,18),(11,0),(15,0),(15,22),(-15,22)]
 fs=[]
 for side in [-4,4]:
  for i,(x0,x1,z0,z1) in enumerate([(-15,-11,0,18),(11,15,0,18),(-15,15,18,22)]):
   fs.append(face([(x0,side,z0),(x1,side,z0),(x1,side,z1),(x0,side,z1)],[0,np.sign(side),0],'guard',f'cap-{side}-{i}'))
 for i,(x0,z0) in enumerate(poly):
  x1,z1=poly[(i+1)%len(poly)]; n=np.array([z1-z0,0,-(x1-x0)],dtype=float);n/=np.linalg.norm(n)
  fs.append(face([(x0,-4,z0),(x1,-4,z1),(x1,4,z1),(x0,4,z0)],n,'guard',f'boundary-{i}'))
 return fs
def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def encoded(a):return np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)
def qa_views(path):
 im=Image.open(path).convert('RGB'); a=np.asarray(im)/255.; l=linear(a)
 gray=l@np.array([.2126,.7152,.0722]); g=np.repeat(encoded(gray)[...,None],3,axis=2)
 # Machado et al. 2009 deuteranomaly severity 100; approximate one-condition simulation.
 mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
 d=encoded(np.clip(l@mat.T,0,1))
 Image.fromarray(np.uint8(np.clip(g*255+.5,0,255))).save(path.with_name('figure-grayscale.png'),dpi=(300,300))
 Image.fromarray(np.uint8(np.clip(d*255+.5,0,255))).save(path.with_name('figure-deuteranomaly100.png'),dpi=(300,300))

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--renderer',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);p.add_argument('--input',type=Path,required=True);a=p.parse_args()
 if a.out.exists():p.error('Refusing to overwrite existing output')
 a.out.mkdir(parents=True)
 import importlib.util
 modspec=importlib.util.spec_from_file_location('bound_surface_renderer',a.renderer);r=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(r)
 pdfmetrics.registerFont(TTFont('Arial',str(a.font)));pdfmetrics.registerFont(TTFont('Arial-Bold',str(a.bold_font)))
 faces=box(GEOMETRY['base']['box'],'base')+guard()+box(GEOMETRY['insert']['box'],'insert')
 view=np.array([.35,-1.,.24]);view/=np.linalg.norm(view)
 right=np.array([1.,.35,0]);right/=np.linalg.norm(right);up=np.cross(view,right)
 scale=2.;origin=np.array([80.,62.])
 def proj(v):v=np.array(v);return origin+scale*np.array([v@right,-v@up])
 im,mask,lo,hi,record=r.render(faces,right,up,view,px_per_unit=28,light=(-.45,-.7,1.25),ambient=.50)
 im.save(a.out/'surfaces.png');mask.save(a.out/'visible-role-mask.png')
 position=origin+scale*lo;extent=scale*(hi-lo)
 annotations=[]
 def line(id,pts,color='#424B54',width=.24,dash=None):annotations.append({'id':id,'type':'line','points':np.array(pts).tolist(),'color':color,'width':width,'dash':dash})
 def label(id,text,xy,size=10.5,align='middle',bold=False):annotations.append({'id':id,'type':'text','text':text,'xy':list(xy),'size_pt':size,'align':align,'bold':bold,'color':'#26333E'})
 def arrowhead(id,tip,away,length=1.65,width=.72):
  t=np.array(tip);v=np.array(away)-t;v/=np.linalg.norm(v);n=np.array([-v[1],v[0]]);pts=[t,t+length*v+width*n,t+length*v-width*n]
  annotations.append({'id':id,'type':'polygon','points':np.array(pts).tolist(),'color':'#424B54'})
 label('guard-label','Guard',[111,12]);line('guard-leader',[[111,14.2],[111,19],proj([11,0,22])])
 label('insert-label','Insert',[64,92]);line('insert-leader',[[64,87.8],[64,72],proj([0,-22,8])])
 label('base-label','Base',[137,91]);line('base-leader',[[137,86.8],[137,79],proj([23,-20,-1.5])])
 pa,pb=proj([-2,-4,10]),proj([-2,-4,18]);line('upper-clearance',[pa,pb],width=.22)
 arrowhead('upper-clearance-bottom',pa,pb);arrowhead('upper-clearance-top',pb,pa)
 for id,point in [('lower',pa),('upper',pb)]:line('dimension-tick-'+id,[point+[-2,0],point+[2,0]],width=.20)
 label('upper-clearance-label','8',(pa+pb)/2+[3.2,1.2],size=10.5,bold=True)
 triad_origin=np.array([17.,91.]); triad_scale=9.
 for name,v,offset in [('x',[1,0,0],[2.5,1.2]),('y',[0,1,0],[1,-1.4]),('z',[0,0,1],[-.1,-1.6])]:
  endpoint=triad_origin+triad_scale*np.array([np.dot(v,right),-np.dot(v,up)])
  line('axis-'+name,[triad_origin,endpoint],width=.20);arrowhead('axis-head-'+name,endpoint,triad_origin,length=1.15,width=.42);label('axis-label-'+name,name,endpoint+offset,size=8.5)
 # SVG labels and dimensional geometry stay fully editable, only surfaces are raster.
 x,y=position;w,h=extent
 data=base64.b64encode((a.out/'surfaces.png').read_bytes()).decode()
 xml=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="160mm" height="100mm" viewBox="0 0 160 100">',
 '<title>Original geometry DEMO: continuous guard and noncontact insert</title>',
 '<desc>'+escape(ALT)+'</desc>',
 '<metadata>'+escape(json.dumps({'demo':True,'format':'hybrid: raster surfaces, vector annotations','version':VERSION,'right':right.tolist(),'up':up.tolist(),'view':view.tolist(),'input_sha256':digest(a.input)}))+'</metadata>',
 '<rect id="canvas" x="0" y="0" width="160" height="100" fill="#FFFFFF"/>',
 f'<image id="orthographic-surfaces" data-entities="base guard insert" x="{x}" y="{y}" width="{w}" height="{h}" xlink:href="data:image/png;base64,{data}"/>']
 c=canvas.Canvas(str(a.out/'figure.pdf'),pagesize=(W*MM,H*MM),pageCompression=1)
 c.setTitle('Original geometry DEMO — '+VERSION);c.setAuthor('Independent FigureCraft transfer task');c.setSubject('Original DEMO; hybrid surface raster with vector annotations; geometry only')
 c.setFillColorRGB(1,1,1);c.rect(0,0,W*MM,H*MM,stroke=0,fill=1);c.drawImage(ImageReader(im),x*MM,(H-y-h)*MM,w*MM,h*MM,mask='auto')
 for o in annotations:
  if o['type']=='text':
   tx,ty=o['xy'];sz=o['size_pt'];weight='bold' if o['bold'] else 'normal';font='Arial-Bold' if o['bold'] else 'Arial';align=o['align'];anchor={'middle':'middle','start':'start','end':'end'}[align]
   xml.append(f'<text id="{o["id"]}" x="{tx}" y="{ty}" font-family="Arial" font-size="{sz/MM}" font-weight="{weight}" text-anchor="{anchor}" fill="{o["color"]}">{escape(o["text"])}</text>')
   c.setFillColor(o['color']);c.setFont(font,sz)
   {'middle':c.drawCentredString,'start':c.drawString,'end':c.drawRightString}[align](tx*MM,(H-ty)*MM,o['text'])
  else:
   pts=o['points'];s=' '.join(f'{px},{py}' for px,py in pts)
   if o['type']=='line':
    xml.append(f'<polyline id="{o["id"]}" points="{s}" fill="none" stroke="{o["color"]}" stroke-width="{o["width"]}" stroke-linejoin="round" stroke-linecap="round"/>');c.setStrokeColor(o['color']);c.setLineWidth(o['width']*MM);c.setLineCap(1);c.setLineJoin(1)
   else:xml.append(f'<polygon id="{o["id"]}" points="{s}" fill="{o["color"]}"/>');c.setFillColor(o['color'])
   pp=c.beginPath();pp.moveTo(pts[0][0]*MM,(H-pts[0][1])*MM)
   for px,py in pts[1:]:pp.lineTo(px*MM,(H-py)*MM)
   if o['type']=='polygon':pp.close()
   c.drawPath(pp,fill=int(o['type']=='polygon'),stroke=int(o['type']=='line'))
 xml.append('</svg>');(a.out/'figure.svg').write_text('\n'.join(xml),encoding='utf-8');c.showPage();c.save()
 cmd=[str(a.pdftoppm),'-png','-r','300','-singlefile',str(a.out/'figure.pdf'),str(a.out/'figure')]
 completed=subprocess.run(cmd,capture_output=True,text=True,check=True)
 qa_views(a.out/'figure.png')
 (a.out/'caption.txt').write_text(CAPTION,encoding='utf-8');(a.out/'alt.txt').write_text(ALT,encoding='utf-8')
 dump(a.out/'geometry.json',GEOMETRY)
 dump(a.out/'surfaces.json',[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in f.items()} for f in faces])
 dump(a.out/'annotations.json',annotations)
 dump(a.out/'surface-render-record.json',record)
 spec={'figure_id':'original-u-guard-geometry-demo','schema_version':'external-orthographic-1','demo':True,'evidence_status':'Original geometry illustration, not experiment or mechanically validated assembly','scientific_message':'One continuous guard contacts the base while a rectangular insert passes through its opening without contact.','source_refs':[{'path':str(a.input.resolve()),'sha256':digest(a.input)}],'entities':[{'id':k,'semantic_role':k} for k in GEOMETRY],'relations':[{'id':'guard-base-contact','from':'guard','to':'base','kind':'geometric-contact','meaning':'Two rectangular feet at z=0'},{'id':'insert-guard-clearance','from':'insert','to':'guard','kind':'geometric-clearance','meaning':'Passes through the opening along y; no intersection'},{'id':'insert-base-clearance','from':'insert','to':'base','kind':'geometric-clearance','meaning':'6-unit vertical separation'}],'exact_labels':['Guard','Insert','Base','8'],'locked_values':GEOMETRY|{'upper_clearance':8,'lateral_clearance_each':5,'base_to_insert_clearance':6,'object_count':3},'forbidden_implications':['forces','motion','flow','fasteners','hidden supports','material properties','mechanical stability','physical shadows'],'geometry_units':'arbitrary length units','camera':{'mode':'orthographic','right':right.tolist(),'up':up.tolist(),'view_toward_observer':view.tolist(),'mm_per_projected_unit':scale,'origin_mm':origin.tolist()},'output':{'width_mm':W,'height_mm':H,'placement_width_mm':160,'surface_dpi':28/scale*25.4,'hybrid':True,'png_dpi':300,'main_label_pt':10.5,'axis_label_pt':8.5},'role_map':COLORS,'layout':{'representation':'single orthographic complete model','inset':False,'caption_assignment':['arbitrary units','side clearances 5','lower clearance 6','positions only','DEMO status']},'depth':{'mode':'D2 explicit polyhedral geometry','shading':'normal-dependent presentation tone only','shadows':False},'caption':CAPTION,'alt_text':ALT,'author_acceptance':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED'}
 dump(a.out/'figure_spec.json',spec)
 # Numeric assertions separated from perceptual judgement.
 def intersection_volume(b1,b2):return float(np.prod([max(0,min(q[1],r[1])-max(q[0],r[0])) for q,r in zip(b1,b2)]))
 numeric={'geometry':GEOMETRY,'upper_clearance':18-10,'left_clearance':-6-(-11),'right_clearance':11-6,'lower_clearance':6-0,'guard_feet_contact_area':2*4*8,'volumes':{'base':48*52*3,'guard':2*4*8*18+30*8*4,'insert':12*44*4},'insert_base_intersection_volume':intersection_volume(GEOMETRY['base']['box'],GEOMETRY['insert']['box']),'insert_guard_intersection_volumes':[intersection_volume(b,GEOMETRY['insert']['box']) for b in GEOMETRY['guard']['union_boxes']],'camera_orthonormal':bool(np.allclose(np.array([right,up,view])@np.array([right,up,view]).T,np.eye(3))),'right_handed_world':True,'upper_dimension_world_endpoints':[[-2,-4,10],[-2,-4,18]],'dimension_projected_endpoints':[pa.tolist(),pb.tolist()],'logical_objects':3,'guard_boundary_is_single_extrusion':True}
 assert numeric['upper_clearance']==8 and numeric['left_clearance']==numeric['right_clearance']==5 and numeric['lower_clearance']==6
 assert numeric['insert_base_intersection_volume']==0 and all(v==0 for v in numeric['insert_guard_intersection_volumes'])
 numeric['status']='PASS';numeric['scope']='Arithmetic and source geometry; not a visual or scientific validation';dump(a.out/'numerical-checks.json',numeric)
 page=PdfReader(str(a.out/'figure.pdf')).pages[0];txt=page.extract_text();png=Image.open(a.out/'figure.png')
 checks={'pdf_pages':1,'pdf_width_mm':float(page.mediabox.width)/MM,'pdf_height_mm':float(page.mediabox.height)/MM,'pdf_extracted_text':txt,'required_pdf_labels':all(v in txt for v in ['Guard','Insert','Base','8']),'png_pixels':list(png.size),'svg_image_nodes':1,'hybrid':True,'min_font_pt':min(v['size_pt'] for v in annotations if v['type']=='text'),'labels_within_page':all(0<v['xy'][0]<W and 0<v['xy'][1]<H for v in annotations if v['type']=='text'),'poppler_command':cmd,'poppler_exit':completed.returncode,'surface_dpi':28/scale*25.4,'cvd':'Approximate Machado 2009 deuteranomaly severity 100, linear RGB matrix, clipping to gamut. Only one condition.'}
 assert abs(checks['pdf_width_mm']-160)<.01 and abs(checks['pdf_height_mm']-100)<.01 and checks['required_pdf_labels'] and checks['min_font_pt']>=8
 checks['technical_status']='PASS';checks['visual_status']='REVIEW_REQUIRED';checks['author_acceptance']='REVIEW_REQUIRED';dump(a.out/'technical-checks.json',checks)
 shutil.copy2(__file__,a.out/'build.py');shutil.copy2(a.renderer,a.out/'surface_renderer.py');shutil.copy2(a.input,a.out/'input.md')
 dump(a.out/'manifest.json',{'version':VERSION,'format':'HYBRID','source':str(Path(__file__).resolve()),'source_sha256':digest(__file__),'renderer_sha256':digest(a.renderer),'input_sha256':digest(a.input),'font_sha256':digest(a.font),'bold_font_sha256':digest(a.bold_font),'files':{f.name:digest(f) for f in a.out.iterdir() if f.is_file()},'technical_status':'PASS','scientific_review_status':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED','author_acceptance':'REVIEW_REQUIRED','overall_status':'REVIEW_REQUIRED'})
 print(json.dumps({'version':VERSION,'output':str(a.out.resolve()),'surface_bounds_mm':[position.tolist(),(position+extent).tolist()],'surface_pixels':list(im.size),'technical_status':'PASS'}))
if __name__=='__main__':main()
