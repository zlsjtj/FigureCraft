"""Rebuild the supplied geometric DEMO. No external artwork or measured data.

Usage: python build_figure.py --skill ROOT --input INPUT.md --out NEW_DIR
       --font Arial.ttf --bold-font Arialbd.ttf --pdftoppm EXE --revision first|final|post-review --review ASSESSMENT.md
"""
import argparse, base64, hashlib, importlib.util, json, math, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

MM = 72/25.4
LOADED = ['SKILL.md','references/workflow.md','references/quality-and-acceptance.md',
          'references/dependencies.md','references/drawing-and-depth.md',
          'references/surface-rendering.md','references/design-exploration.md',
          'references/existing-svg-review.md','references/figure-spec.md',
          'scripts/surface_renderer.py','scripts/probe_runtime.py']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8')
def polar(r,t,z): return np.array([r*math.cos(t),r*math.sin(t),z],float)

def geometry():
    faces=[]; shell='#65ADB5'; inner='#56949E'; cut='#B2D3D6'; core='#E3AA61'
    def add(points,n,role,color,normals=None):
        f={'p':np.array(points),'n':np.array(n),'role':role,'color':color}
        if normals is not None: f['vertex_normals']=np.array(normals)
        faces.append(f)
    theta=np.linspace(math.radians(35),math.radians(325),581)
    for t,u in zip(theta[:-1],theta[1:]):
        m=(t+u)/2
        for r,sgn,role,color in [(12,1,'sleeve_outer',shell),(9,-1,'sleeve_inner',inner)]:
            pts=[polar(r,t,0),polar(r,u,0),polar(r,u,30),polar(r,t,30)]
            norms=[sgn*polar(1,v,0) for v in [t,u,u,t]]
            add(pts,sgn*polar(1,m,0),role,color,norms)
        for z,sgn in [(0,-1),(30,1)]:
            add([polar(9,t,z),polar(12,t,z),polar(12,u,z),polar(9,u,z)],
                [0,0,sgn],'sleeve_end_rim',cut)
    for t,sgn in [(theta[0],-1),(theta[-1],1)]:
        n=sgn*np.array([-math.sin(t),math.cos(t),0])
        add([polar(9,t,0),polar(12,t,0),polar(12,t,30),polar(9,t,30)],n,'sleeve_opening_face',cut)
    ts=np.linspace(0,2*math.pi,721)
    for t,u in zip(ts[:-1],ts[1:]):
        add([polar(5,t,-3),polar(5,u,-3),polar(5,u,33),polar(5,t,33)],
            polar(1,(t+u)/2,0),'solid_core',core,[polar(1,v,0) for v in [t,u,u,t]])
        for z,sgn in [(-3,-1),(33,1)]:
            add([np.array([0,0,z]),polar(5,t,z),polar(5,u,z)], [0,0,sgn],'core_end',core)
    return faces

def main():
    ap=argparse.ArgumentParser(__doc__)
    for n in ['skill','input','out','font','bold-font','pdftoppm']: ap.add_argument('--'+n,required=True,type=Path)
    ap.add_argument('--revision',choices=['first','final','post-review'],default='post-review')
    ap.add_argument('--review',type=Path); a=ap.parse_args()
    if a.revision=='post-review' and (a.review is None or not a.review.is_file()):
        raise SystemExit('--review ASSESSMENT.md is required for an explicitly feedback-informed revision')
    if a.out.exists(): raise SystemExit('Refusing to overwrite an existing artifact directory')
    a.out.mkdir(parents=True)
    module=a.skill/'scripts/surface_renderer.py'
    loader=importlib.util.spec_from_file_location('candidate_surface_renderer',module)
    render_module=importlib.util.module_from_spec(loader);loader.loader.exec_module(render_module)
    js(a.out/'loaded_skill_hashes.json',{'skill_root':str(a.skill.resolve()),'files':[{'path':p,'sha256':sha(a.skill/p)} for p in LOADED]})
    subprocess.run([sys.executable,str(a.skill/'scripts/probe_runtime.py'),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--out',str(a.out/'runtime.json')],check=True,stdout=subprocess.DEVNULL)
    az=math.radians(-16);el=math.radians(25)
    view=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    right=np.array([-math.sin(az),math.cos(az),0]); up=np.cross(view,right)
    light=np.array([.65,-.75,1.2] if a.revision in ('final','post-review') else [-.30,-.55,1.0]); faces=geometry()
    im,mask,lo,hi,record=render_module.render(faces,right,up,view,px_per_unit=32,light=light,ambient=.48)
    im.save(a.out/'surface.png');mask.save(a.out/'visible_roles.png');js(a.out/'surface_record.json',record)
    # The one autonomous revision changes illustrative light and one label anchor.
    scale=1.78; center=np.array([69.5,47.8]); world_center=np.array([0,0,15])
    basis=np.array([right,-up])
    def proj(p):return center+(basis@(np.asarray(p)-world_center))*scale
    xy=center+(lo-basis@world_center)*scale; wh=(hi-lo)*scale
    svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="160mm" height="95mm" viewBox="0 0 160 95">',
         '<title>Coaxial sleeve with a longitudinal opening and separate solid core</title>',
         '<desc>Original geometric DEMO, orthographic projection, hybrid surface raster and editable vector labels.</desc>',
         '<rect x="0" y="0" width="160" height="95" fill="#FFFFFF"/>']
    b64=base64.b64encode((a.out/'surface.png').read_bytes()).decode()
    svg.append(f'<image id="opaque-geometry" x="{xy[0]}" y="{xy[1]}" width="{wh[0]}" height="{wh[1]}" xlink:href="data:image/png;base64,{b64}"/>')
    pdfmetrics.registerFont(TTFont('FigureArial',str(a.font)))
    pdfmetrics.registerFont(TTFont('FigureArialBold',str(a.bold_font)))
    c=canvas.Canvas(str(a.out/'figure.pdf'),pagesize=(160*MM,95*MM),pageCompression=1)
    c.setTitle('Coaxial sleeve with longitudinal opening — original geometric DEMO')
    c.drawImage(ImageReader(im),xy[0]*MM,(95-xy[1]-wh[1])*MM,width=wh[0]*MM,height=wh[1]*MM,mask='auto')
    labels=[];segments=[]
    def line(id,points,width=.27,color='#52636C'):
        points=[list(map(float,p)) for p in points];segments.append({'id':id,'points':points,'width_mm':width})
        svg.append(f'<polyline id="{id}" points="'+ ' '.join(f'{x:.4f},{y:.4f}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')
        c.setStrokeColor(color);c.setLineWidth(width*MM);p=c.beginPath();p.moveTo(points[0][0]*MM,(95-points[0][1])*MM)
        for x,y in points[1:]:p.lineTo(x*MM,(95-y)*MM)
        c.drawPath(p)
    def text(id,content,x,y,size=10.5,bold=False):
        labels.append({'id':id,'text':content,'x_mm':x,'baseline_y_mm':y,'font_pt':size,'bold':bold})
        svg.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-weight="{700 if bold else 400}" font-size="{size/MM}" fill="#22343E">{escape(content)}</text>')
        c.setFillColor('#22343E');c.setFont('FigureArialBold' if bold else 'FigureArial',size);c.drawString(x*MM,(95-y)*MM,content)
    # Labels use direct anchors computed by the camera, never displaced geometry.
    sleeve_anchor=proj(polar(12,math.radians(-88),21))
    line('sleeve-leader',[(31,28),(39,28),sleeve_anchor]);text('sleeve-label','Sleeve',13,27,bold=True)
    core_anchor=proj(polar(5,az,32))
    line('core-leader',[core_anchor,(105,17),(111,17)]);text('core-label','Solid core',113,18,bold=True)
    # Feedback repair: the opening is already shown by its continuous boundaries.
    # Remove the ambiguous surface-directed leader and its two-line label only.
    if a.revision!='post-review':
        opening_anchor=proj(polar(7,math.radians(35),15)) if a.revision=='final' else proj(polar(10.5,math.radians(35),15))
        line('opening-leader',[opening_anchor,(105,45),(111,45)])
        text('opening-label','Longitudinal',113,44);text('opening-label-2','opening',113,48.5)
    gap_theta=math.radians(-65);gap_a=proj(polar(5,gap_theta,30));gap_b=proj(polar(9,gap_theta,30))
    line('radial-gap-dimension',[gap_a,gap_b],.30)
    vec=gap_b-gap_a;perp=np.array([-vec[1],vec[0]])/np.linalg.norm(vec)*.72
    for k,p in enumerate([gap_a,gap_b]):line('gap-tick-'+str(k),[p-perp,p+perp],.30)
    mid=(gap_a+gap_b)/2
    line('gap-leader',[mid,(40,14),(31,14)])
    text('gap-label','Radial gap = 4',8,13)
    c.showPage();c.save();svg.append('</svg>');(a.out/'figure.svg').write_text('\n'.join(svg),encoding='utf-8')
    subprocess.run([str(a.pdftoppm),'-png','-r','300','-singlefile',str(a.out/'figure.pdf'),str(a.out/'figure')],check=True,capture_output=True)
    png=Image.open(a.out/'figure.png').convert('RGB');ImageOps.grayscale(png).save(a.out/'figure-grayscale.png')
    # A stated approximate single-condition view, not a diagnostic certification.
    rgb=np.asarray(png).astype(float)/255;lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    sim=np.clip(lin@matrix.T,0,1);srgb=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(a.out/'figure-deuteranopia-approx.png')
    caption=('Original geometric demonstration of a coaxial sleeve and solid core. The sleeve has outer radius 12 and inner radius 9, spans z = 0–30, and has an existing longitudinal opening over azimuth −35° to +35° through its entire wall thickness and length. Azimuth is measured from +x toward +y. The remaining sleeve wall is one continuous body; both axial ends are open. The solid core has radius 5 and spans z = −3–33. It does not contact the sleeve; the radial separation is 4 wherever sleeve material remains. The dimension line marks that radial separation at the upper opening of the sleeve. All coordinates are arbitrary drawing units. Orthographic geometry is rendered with illustrative surface shading. No support, motion, transport, or physical function is specified.')
    alt=('An oblique view shows a blue-green sleeve surrounding an orange solid cylindrical core. A full-length vertical opening reveals the core, the sleeve inner surface, and the intervening space. The core projects beyond both sleeve ends. The sleeve upper end is an open annular rim, with no cap across the central opening. A short radial dimension at the top marks the separation of 4 between core and inner wall. Labels identify the sleeve, solid core, and longitudinal opening.')
    if a.revision=='post-review':
        alt=alt.replace('Labels identify the sleeve, solid core, and longitudinal opening.', 'Labels identify the sleeve and solid core. The longitudinal opening is shown by the continuous exposed wall-thickness faces and upper C-shaped rim, without a separate leader.')
    (a.out/'caption.txt').write_text(caption+'\n',encoding='utf-8');(a.out/'alt_text.txt').write_text(alt+'\n',encoding='utf-8')
    js(a.out/'annotations.json',{'labels':labels,'lines':segments})
    spec={'figure_id':'longitudinal_open_sleeve','schema_version':1,'mode':'new_schematic','demo':True,'evidence_status':'Original geometry; no measurements or device mechanism',
          'scientific_message':'A longitudinal opening makes the separate coaxial core and radial clearance visible.',
          'source_refs':[{'path':'input.md','sha256':sha(a.input)}],
          'entities':[{'id':'sleeve','semantic_role':'sleeve','description':'One continuous open-ended sleeve'},{'id':'core','semantic_role':'core','description':'One solid cylinder'}],
          'relations':[{'id':'coaxial','from':'sleeve','to':'core','kind':'geometry','meaning':'common z axis; no contact'}],
          'count_constraints':{'expected_logical_ids':['sleeve','core'],'number_of_physical_objects':2},
          'locked_values':{'sleeve_outer_radius':12,'sleeve_inner_radius':9,'sleeve_z':[0,30],'opening_azimuth_degrees':[-35,35],'core_radius':5,'core_z':[-3,33],'radial_gap':4},
          'forbidden_implications':['end caps across sleeve bore','supports','flow','motion','physical action','another cutting operation'],
          'exact_labels':[l['text'] for l in labels], 'depth':{'mode':'D2_explicit_mesh_orthographic','affects_quantitative_encoding':False},
          'output':{'width_mm':160,'height_mm':95,'placement_width_mm':160,'png_dpi':300,'editable':'HYBRID: raster surface; native SVG/PDF text and lines; parameterized mesh source'},
          'camera':{'azimuth_deg':-16,'elevation_deg':25,'view_toward_observer':view.tolist(),'right':right.tolist(),'up':up.tolist(),'projection':'orthographic','scale_mm_per_native_unit':scale},
          'light':{'world_direction':light.tolist(),'ambient':.48,'purpose':'illustrative Lambertian normal shading, no physical simulation'},
          'mesh':{'sleeve_arc_steps':580,'core_arc_steps':720,'face_count':len(faces),'end_rims':'only 9 <= r <= 12, retained 290 degree sector','cut_faces':'two radial rectangles at ±35 degrees','no_end_caps_over_sleeve_bore':True},
          'publication':{'target_journal':None,'eligibility':'UNVERIFIED'},'caption':caption,'alt_text':alt}
    if a.revision=='post-review':
        shutil.copy2(a.review,a.out/'feedback-assessment.md')
        spec['feedback_revision']={'type':'feedback-informed repair, not feedback-free generation','assessment_sha256':sha(a.review),'change':'remove opening-leader, opening-label, opening-label-2 only','protected':['geometry','camera','dimensions','palette','light','gap annotation'],'followup_independent_review':'PENDING'}
    js(a.out/'figure_spec.json',spec)
    shutil.copy2(a.input,a.out/'input.md');shutil.copy2(Path(__file__),a.out/'build_figure.py')
    pdf=PdfReader(a.out/'figure.pdf');page=pdf.pages[0];pdftext=page.extract_text()
    import xml.etree.ElementTree as ET
    root=ET.parse(a.out/'figure.svg').getroot()
    checks={'source_geometry':{'outer_radius':12,'inner_radius':9,'core_radius':5,'gap_recomputed':9-5,'wall_thickness_recomputed':12-9,'sleeve_angular_span_degrees':325-35,'continuous_sleeve':True,'physical_object_count':2},
      'pdf_pages':len(pdf.pages),'pdf_size_mm':[float(page.mediabox.width)/MM,float(page.mediabox.height)/MM],
      'all_labels_extract_from_pdf':all(l['text'] in pdftext for l in labels),'minimum_font_pt':min(l['font_pt'] for l in labels),
      'svg_xml_parsed':True,'svg_text_count':len(root.findall('{http://www.w3.org/2000/svg}text')),'png_pixels':png.size,
      'embedded_surface_effective_dpi':[im.width/(wh[0]/25.4),im.height/(wh[1]/25.4)],
      'camera_basis_orthonormal':bool(np.allclose(np.array([right,up,view])@np.array([right,up,view]).T,np.eye(3))),
      'source_discretization_max_sagitta':{'sleeve':12*(1-math.cos(math.radians(.5)/2)),'core':5*(1-math.cos(math.radians(.5)/2))},
      'cvd_preview':{'method':'Machado-style deuteranopia severity 1 matrix applied in linear sRGB; approximate','matrix':matrix.tolist(),'scope':'one condition only'},
      'technical_status':'PASS','scientific_status':'REVIEW_REQUIRED','visual_status':'REVIEW_REQUIRED','author_acceptance':'NOT_RUN','overall_status':'REVIEW_REQUIRED',
      'not_verified':['author acceptance','independent scientific or visual review','journal compliance','printed output','other CVD conditions','cross-editor editability','per-pixel analytic visibility proof'],
      'command':sys.argv,'exit_code':0}
    assert checks['all_labels_extract_from_pdf'] and checks['camera_basis_orthonormal']
    js(a.out/'checks.json',checks)
    js(a.out/'manifest.json',{'revision':a.revision,'files':[{'path':p.name,'sha256':sha(p)} for p in sorted(a.out.iterdir()) if p.is_file()]})
    print(json.dumps({'out':str(a.out),'files':len(list(a.out.iterdir())),'svg':str(a.out/'figure.svg'),'png':str(a.out/'figure.png'),'pdf':str(a.out/'figure.pdf'),'status':'REVIEW_REQUIRED'}))
if __name__=='__main__':main()
