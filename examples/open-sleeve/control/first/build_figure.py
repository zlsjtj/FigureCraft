"""Rebuild the exact coaxial DEMO in a fresh directory; no external assets downloaded."""
import argparse, base64, hashlib, importlib.util, json, math, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

LOADED=['SKILL.md','references/workflow.md','references/quality-and-acceptance.md',
 'references/dependencies.md','references/surface-rendering.md','references/drawing-and-depth.md',
 'references/design-exploration.md','references/existing-svg-review.md',
 'scripts/probe_runtime.py','scripts/surface_renderer.py']
MM=72/25.4
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def polar(r,t,z): return np.array([r*math.cos(t),r*math.sin(t),z],dtype=float)

def model_faces():
    faces=[]
    def face(p,n,role,col,vn=None):
        f={'p':np.asarray(p),'n':np.asarray(n,dtype=float),'role':role,'color':col}
        if vn is not None: f['vertex_normals']=np.asarray(vn)
        faces.append(f)
    angles=np.linspace(math.radians(35),math.radians(325),581)
    blue='#68A2B4'; gold='#DCA75B'
    for a,b in zip(angles[:-1],angles[1:]):
        m=(a+b)/2
        for r,sign,role in [(12,1,'sleeve_outer'),(9,-1,'sleeve_inner')]:
            n=sign*np.array([math.cos(m),math.sin(m),0])
            ns=[sign*np.array([math.cos(t),math.sin(t),0]) for t in [a,b,b,a]]
            face([polar(r,a,0),polar(r,b,0),polar(r,b,30),polar(r,a,30)],n,role,blue,ns)
        for z,sign in [(0,-1),(30,1)]:
            face([polar(9,a,z),polar(12,a,z),polar(12,b,z),polar(9,b,z)],(0,0,sign),'sleeve_annular_rim',blue)
    for t,sgn in [(angles[0],-1),(angles[-1],1)]:
        n=sgn*np.array([-math.sin(t),math.cos(t),0])
        face([polar(9,t,0),polar(12,t,0),polar(12,t,30),polar(9,t,30)],n,'sleeve_opening_edge',blue)
    ca=np.linspace(0,2*math.pi,721)
    for a,b in zip(ca[:-1],ca[1:]):
        m=(a+b)/2
        face([polar(5,a,-3),polar(5,b,-3),polar(5,b,33),polar(5,a,33)],
             (math.cos(m),math.sin(m),0),'core_wall',gold,
             [(math.cos(t),math.sin(t),0) for t in [a,b,b,a]])
    for z,sgn in [(-3,-1),(33,1)]:
        face([polar(5,t,z) for t in ca[:-1]],(0,0,sgn),'core_end',gold)
    return faces

def camera(az,el,roll):
    az,el,roll=np.radians([az,el,roll])
    v=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    r=np.array([-np.sin(az),np.cos(az),0.]);u=np.cross(v,r)
    return r*np.cos(roll)-u*np.sin(roll),r*np.sin(roll)+u*np.cos(roll),v

class Draw:
    def __init__(self,out):
        self.out=out;self.svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="160mm" height="95mm" viewBox="0 0 160 95">', '<title>Longitudinally open sleeve and coaxial solid core</title>', '<desc>Two repeated views of the same two-object geometric demonstration.</desc>', '<rect width="160" height="95" fill="#FFFFFF"/>']
        self.c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(160*MM,95*MM));self.c.setTitle('Longitudinally open sleeve and coaxial solid core')
        self.texts=[]
    def image(self,path,x,y,w,h,id):
        b64=base64.b64encode(path.read_bytes()).decode()
        self.svg.append(f'<image id="{id}" x="{x:.5f}" y="{y:.5f}" width="{w:.5f}" height="{h:.5f}" xlink:href="data:image/png;base64,{b64}"/>')
        self.c.drawImage(ImageReader(str(path)),x*MM,(95-y-h)*MM,w*MM,h*MM,mask='auto')
    def text(self,id,text,x,y,size=10,bold=False,anchor='start',color='#263944'):
        font='Arial-Bold' if bold else 'Arial';sz=size/MM
        self.svg.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-size="{sz}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(text)}</text>')
        c=self.c;c.setFillColor(color);c.setFont(font,size)
        fn={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[anchor];fn(x*MM,(95-y)*MM,text)
        width=pdfmetrics.stringWidth(text,font,size)/MM
        left=x if anchor=='start' else x-width/2 if anchor=='middle' else x-width
        self.texts.append({'id':id,'text':text,'font_pt':size,'bounds_mm':[left,y-size/MM*.8,left+width,y+size/MM*.2]})
    def line(self,id,pts,color='#536873',width=.22):
        ds=' '.join(('M' if i==0 else 'L')+f'{x:.5f},{y:.5f}' for i,(x,y) in enumerate(pts))
        self.svg.append(f'<path id="{id}" d="{ds}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')
        c=self.c;c.setStrokeColor(color);c.setLineWidth(width*MM);p=c.beginPath();p.moveTo(pts[0][0]*MM,(95-pts[0][1])*MM)
        for x,y in pts[1:]:p.lineTo(x*MM,(95-y)*MM)
        c.drawPath(p)
    def finish(self):
        self.svg.append('</svg>');(self.out/'figure.svg').write_text('\n'.join(self.svg),encoding='utf-8');self.c.showPage();self.c.save()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--skill',type=Path,required=True);ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--stage',choices=['first','final'],required=True)
    ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():ap.error('Refusing to overwrite an existing output directory')
    a.out.mkdir(parents=True);out=a.out.resolve()
    hashes={str(p):digest(a.skill/p) for p in LOADED}
    modspec=importlib.util.spec_from_file_location('surface_renderer',a.skill/'scripts/surface_renderer.py');sr=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(sr)
    pdfmetrics.registerFont(TTFont('Arial',str(a.font)));pdfmetrics.registerFont(TTFont('Arial-Bold',str(a.bold_font)))
    faces=model_faces();r,u,v=camera(17,23,-18)
    light=(-.35,-.70,1.1)
    mainim,mask,lo,hi,record=sr.render(faces,r,u,v,px_per_unit=30,light=light,ambient=.42)
    mainim.save(out/'surface-main.png');mask.save(out/'surface-main-roles.png')
    scale=1.60;cx,cy=54,49;center=(lo+hi)/2
    x,y=cx-(hi[0]-lo[0])*scale/2,cy-(hi[1]-lo[1])*scale/2
    def project(p):
        q=np.array([np.dot(p,r),-np.dot(p,u)])
        return np.array([cx,cy])+(q-center)*scale
    d=Draw(out);d.image(out/'surface-main.png',x,y,(hi[0]-lo[0])*scale,(hi[1]-lo[1])*scale,'oblique-surfaces')
    d.text('main-heading','Oblique view',10,8,10.5,True)
    d.text('sleeve-label','Sleeve',9,22,10)
    p=project(polar(12,math.radians(160),23));d.line('sleeve-leader',[(22,23.3),(27,23.3),p])
    d.text('core-label','Solid core',62,88,10)
    p=project(polar(5,math.radians(5),-2));d.line('core-leader',[(62,84),(61,80),p])
    d.text('opening-label-1','Longitudinal',82,18,10)
    d.text('opening-label-2','opening',82,22.6,10)
    p=project(polar(9,math.radians(35),21));d.line('opening-leader',[(88,25),(88,29),p])
    # A true view along -z of the same model, with no additional sectioning.
    ar=np.array([1.,0,0]);au=np.array([0.,1,0]);av=np.array([0.,0,1.])
    ai,am,al,ah,arec=sr.render(faces,ar,au,av,px_per_unit=30,light=light,ambient=.72)
    ai.save(out/'surface-axial.png');am.save(out/'surface-axial-roles.png')
    ac=np.array([130.,54.]);ascale=1.45;acent=(al+ah)/2
    def axial(p):return ac+(np.array([p[0],-p[1]])-acent)*ascale
    aw,ahh=(ah-al)*ascale;d.image(out/'surface-axial.png',ac[0]-aw/2,ac[1]-ahh/2,aw,ahh,'axial-surfaces')
    d.text('axial-heading','Axial view',130,31,10.5,True,'middle')
    d.text('gap-label','Radial gap = 4',130,83,10,False,'middle')
    # Tick marks measure only the empty interval r=5...9 at theta=90 degrees.
    q5=axial((0,5,33));q9=axial((0,9,30));
    d.line('gap-dimension',[q5,q9],width=.24)
    for i,q in enumerate([q5,q9]):d.line('gap-tick-'+str(i),[(q[0]-1,q[1]),(q[0]+1,q[1])],width=.24)
    d.line('gap-leader',[(119,79),(109,74),(109,45),(q5[0],(q5[1]+q9[1])/2)],width=.2)
    d.finish()
    proc=subprocess.run([str(a.pdftoppm),'-png','-r','300','-singlefile',str(out/'figure.pdf'),str(out/'figure')],capture_output=True,text=True)
    if proc.returncode:raise RuntimeError(proc.stderr)
    im=Image.open(out/'figure.png').convert('RGB');im.convert('L').convert('RGB').save(out/'figure-grayscale.png')
    # Machado et al. (2009), deuteranopia severity 1.0, linear RGB approximation.
    arr=np.asarray(im,dtype=float)/255;lin=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    sim=np.clip(lin@matrix.T,0,1);sim=np.where(sim<=.0031308,sim*12.92,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(sim*255,0,255))).save(out/'figure-deuteranopia-approx.png')
    caption=('Geometric DEMO of a longitudinally open sleeve and a coaxial solid core. The sleeve has outer radius 12, inner radius 9, and axial extent z = 0 to 30. Its existing opening spans azimuths -35 degrees to +35 degrees, measured from +x toward +y, and extends through the full wall thickness and length. The sleeve wall remains one continuous piece with both ends open. The solid core has radius 5 and extends from z = -3 to 33. The radial gap is 4 wherever sleeve wall remains; the core and sleeve do not touch. The oblique view and the axial view along -z show the same two objects. Dimensions are arbitrary drawing units. Shading conveys geometry only; no supports, motion, transport, performance, or fabrication sequence is implied.')
    alt=('Oblique and axial views of one blue open sleeve around one gold solid cylindrical core. The longitudinal opening runs along the entire sleeve wall, exposing the core and empty space between the surfaces. The core projects beyond both sleeve ends. The axial view shows the C-shaped sleeve wall, the circular core, and a dimension tick spanning the radial gap of 4; the opening faces +x.')
    (out/'caption.txt').write_text(caption+'\n',encoding='utf-8');(out/'alt-text.txt').write_text(alt+'\n',encoding='utf-8')
    shutil.copy2(__file__,out/'build_figure.py');shutil.copy2(a.input,out/'input.md')
    spec={'type':'original geometric DEMO','size_mm':[160,95],'stage':a.stage,'representation':'hybrid: editable vector text/leaders and embedded raster surfaces; explicit 3D polygon geometry is editable in source',
      'input_sha256':digest(a.input),'entities':[{'id':'sleeve','outer_radius':12,'inner_radius':9,'z':[0,30],'removed_azimuth_deg':[-35,35],'ends':'open','continuous_objects':1},{'id':'core','radius':5,'z':[-3,33],'solid':True}],
      'relation':{'coaxial_axis':'z','contact':False,'radial_gap_over_retained_wall':4},'camera':{'azimuth_deg':17,'elevation_deg':23,'roll_deg':-18,'right':r.tolist(),'up':u.tolist(),'view_toward_observer':v.tolist(),'projection':'orthographic'},
      'axial_view':{'right':ar.tolist(),'up':au.tolist(),'view':av.tolist(),'observation_direction':'-z','same_objects':True},'light':light,'tessellation':{'sleeve_angular_step_deg':.5,'core_angular_step_deg':.5,'maximum_radial_chord_error':12*(1-math.cos(math.radians(.25)))},'font_min_pt':10,'forbidden_additions':['end caps on sleeve','supports','flow','motion','physical mechanisms'],
      'surface_dpi_main':30/scale*25.4,'surface_dpi_axial':30/ascale*25.4,'loaded_skill_files_sha256':hashes}
    dump(out/'figure_spec.json',spec);dump(out/'loaded-skill-hashes.json',hashes);dump(out/'surface-record-main.json',record);dump(out/'surface-record-axial.json',arec)
    dump(out/'labels.json',d.texts)
    page=PdfReader(out/'figure.pdf').pages[0];bounds=[float(page.mediabox.width)/MM,float(page.mediabox.height)/MM]
    txt=page.extract_text();checks={'page_mm':bounds,'page_count':1,'pdf_searchable_labels':txt,'png_px':list(im.size),'minimum_font_pt':10,'mesh_max_radial_error':spec['tessellation']['maximum_radial_chord_error'],'source_objects':2,'views_of_same_objects':2,'svg_image_nodes':2,'svg_text_nodes':len(d.texts),'pdftoppm_exit_code':proc.returncode,'cvd_method':'Machado 2009 full-severity deuteranopia 3x3 matrix applied in linear RGB; approximate preview only','technical_status':'PASS','scientific_status':'REVIEW_REQUIRED','visual_status':'REVIEW_REQUIRED','author_acceptance':'NOT_RUN','overall_status':'REVIEW_REQUIRED','unverified':['pixelwise independent occlusion oracle','third-party SVG editor roundtrip','physical print','all color vision conditions','author acceptance','journal acceptance']}
    assert np.allclose(bounds,[160,95],atol=.001)
    assert all(t['text'] in txt for t in d.texts)
    assert all(t['bounds_mm'][0]>=0 and t['bounds_mm'][2]<=160 and t['bounds_mm'][1]>=0 and t['bounds_mm'][3]<=95 for t in d.texts)
    dump(out/'checks.json',checks)
    dump(out/'build-record.json',{'command':sys.argv,'python':sys.executable,'font_sha256':digest(a.font),'bold_font_sha256':digest(a.bold_font),'source_sha256':digest(__file__),'exit_code':0})
    dump(out/'manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps({'output':str(out),'files':len(list(out.iterdir())),'size_mm':bounds,'surface_px':mainim.size,'technical_checks':'PASS','overall_status':'REVIEW_REQUIRED'},ensure_ascii=False))
if __name__=='__main__':main()
