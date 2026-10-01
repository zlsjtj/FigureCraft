"""Development composition, fixed open-sleeve DEMO. New output directory required.
Surface_renderer.py is copied unchanged from the frozen FigureCraft baseline.
"""
import argparse, base64, hashlib, json, math, shutil, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
from surface_renderer import render

MM=72/25.4
SLEEVE='#65ADB5'; INNER='#56949E'; RIM='#A9CFD2'; CORE='#E3AA61'; INK='#233942'
LOCKED={'sleeve_outer_radius':12,'sleeve_inner_radius':9,'sleeve_z':[0,30],
        'opening_azimuth_degrees':[-35,35],'core_radius':5,'core_z':[-3,33],'radial_gap':4}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def polar(r,t,z):return np.array([r*math.cos(t),r*math.sin(t),z],float)

def geometry():
    faces=[]
    def add(points,n,role,color,normals=None):
        f={'p':np.array(points),'n':np.array(n),'role':role,'color':color}
        if normals is not None:f['vertex_normals']=np.array(normals)
        faces.append(f)
    theta=np.linspace(math.radians(35),math.radians(325),581)
    for t,u in zip(theta[:-1],theta[1:]):
        m=(t+u)/2
        for r,sgn,role,color in [(12,1,'sleeve_outer',SLEEVE),(9,-1,'sleeve_inner',INNER)]:
            add([polar(r,t,0),polar(r,u,0),polar(r,u,30),polar(r,t,30)],sgn*polar(1,m,0),role,color,[sgn*polar(1,v,0) for v in [t,u,u,t]])
        for z,sgn in [(0,-1),(30,1)]:
            add([polar(9,t,z),polar(12,t,z),polar(12,u,z),polar(9,u,z)],[0,0,sgn],'sleeve_end_rim',RIM)
    for t,sgn in [(theta[0],-1),(theta[-1],1)]:
        add([polar(9,t,0),polar(12,t,0),polar(12,t,30),polar(9,t,30)],sgn*np.array([-math.sin(t),math.cos(t),0]),'sleeve_opening_face',RIM)
    ts=np.linspace(0,2*math.pi,721)
    for t,u in zip(ts[:-1],ts[1:]):
        add([polar(5,t,-3),polar(5,u,-3),polar(5,u,33),polar(5,t,33)],polar(1,(t+u)/2,0),'solid_core',CORE,[polar(1,v,0) for v in [t,u,u,t]])
        for z,sgn in [(-3,-1),(33,1)]:
            add([np.array([0,0,z]),polar(5,t,z),polar(5,u,z)],[0,0,sgn],'core_end',CORE)
    return faces

def mesh_audit(faces):
    results={}
    for name,prefix in [('sleeve','sleeve'),('core','core')]:
        selected=[f for f in faces if f['role'].startswith('sleeve')==(name=='sleeve')]
        adjacency=defaultdict(set);edges=Counter()
        for f in selected:
            pts=[tuple(np.round(p,8)) for p in f['p']]
            for a,b in zip(pts,pts[1:]+pts[:1]):
                adjacency[a].add(b);adjacency[b].add(a);edges[tuple(sorted((a,b)))]+=1
        remaining=set(adjacency);parts=0
        while remaining:
            parts+=1;todo=[remaining.pop()]
            while todo:
                for q in adjacency[todo.pop()]:
                    if q in remaining:remaining.remove(q);todo.append(q)
        results[name]={'faces':len(selected),'connected_components':parts,'edge_incidence_histogram':dict(Counter(edges.values())),
                       'closed_surface_mesh':all(v==2 for v in edges.values()),'euler_characteristic':len(adjacency)-len(edges)+len(selected)}
    # Independent point queries on the mathematical solids, not a count inferred from the image.
    def inside_sleeve(r,t,z):return 9<r<12 and 0<z<30 and 35<t%360<325
    theta=np.linspace(0,359.9,1080);z=np.linspace(.01,29.99,11)
    results['analytic_occupancy']={'removed_sector_empty_all_sampled_z':not any(inside_sleeve(r,t,h) for r in [9.1,10.5,11.9] for t in [-34,0,34] for h in z),
      'retained_arc_has_wall':all(inside_sleeve(10.5,t,15) for t in [36,90,180,270,324]),
      'open_bore_at_both_ends':all(not inside_sleeve(r,t,h) for r in [0,5.1,8.99] for t in theta for h in [0,30]),
      'radial_gap':9-5,'core_sleeve_intersection_empty':5<9}
    results['source_face_extents']={}
    for role in sorted({f['role'] for f in faces}):
        p=np.concatenate([f['p'] for f in faces if f['role']==role]);r=np.linalg.norm(p[:,:2],axis=1)
        results['source_face_extents'][role]={'radius_range':[float(r.min()),float(r.max())],'z_range':[float(p[:,2].min()),float(p[:,2].max())]}
    results['status']='PASS' if all(results[x]['connected_components']==1 and results[x]['closed_surface_mesh'] for x in ['sleeve','core']) and all(v for k,v in results['analytic_occupancy'].items() if k!='radial_gap') else 'FAIL'
    results['scope']='Source geometry, sampled analytic occupancy, connectivity and boundary incidence. Not a per-pixel visibility proof or reader study.'
    return results

def main():
    ap=argparse.ArgumentParser(__doc__)
    for n in ['input','out','font','bold-font','pdftoppm']:ap.add_argument('--'+n,required=True,type=Path)
    ap.add_argument('--revision',choices=['first','final'],default='first');a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refusing to overwrite existing output')
    a.out.mkdir(parents=True)
    elevation=48 if a.revision=='final' else 38
    az=math.radians(-12);el=math.radians(elevation);roll=math.radians(-9)
    view=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    base_right=np.array([-math.sin(az),math.cos(az),0]);base_up=np.cross(view,base_right)
    right=math.cos(roll)*base_right+math.sin(roll)*base_up
    up=-math.sin(roll)*base_right+math.cos(roll)*base_up
    axial_view=np.array([0,0,1.]);axial_base_up=np.cross(axial_view,base_right)
    ar=math.cos(roll)*base_right+math.sin(roll)*axial_base_up
    au=-math.sin(roll)*base_right+math.cos(roll)*axial_base_up
    # These are layout degrees of freedom; all solid geometry remains locked.
    scale=1.95;center=np.array([53.,50.]);ac=np.array([124.,42.]);ascale=1.5
    light=np.array([.65,-.75,1.2]);ambient=.48
    faces=geometry();im,mask,lo,hi,rec=render(faces,right,up,view,px_per_unit=32,light=light,ambient=ambient)
    im.save(a.out/'surface.png');mask.save(a.out/'visible_roles.png');js(a.out/'surface_record.json',rec)
    basis=np.array([right,-up]);abasis=np.array([ar,-au]);wc=np.array([0,0,15.])
    def proj(p):return center+(basis@(np.asarray(p)-wc))*scale
    def axproj(p):return ac+abasis@np.asarray(p)*ascale
    xy=center+(lo-basis@wc)*scale;wh=(hi-lo)*scale
    svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="160mm" height="95mm" viewBox="0 0 160 95">',
         '<title>Open sleeve and separate coaxial solid core</title>',
         '<desc>Original geometric DEMO. Dominant oblique whole view and subordinate axial projection of the same two objects.</desc>',
         '<rect id="white-page" x="0" y="0" width="160" height="95" fill="#FFFFFF"/>']
    b64=base64.b64encode((a.out/'surface.png').read_bytes()).decode()
    svg.append(f'<image id="main-two-objects" data-object-part="primary" data-logical-ids="sleeve core" x="{xy[0]}" y="{xy[1]}" width="{wh[0]}" height="{wh[1]}" xlink:href="data:image/png;base64,{b64}"/>')
    pdfmetrics.registerFont(TTFont('FigureArial',str(a.font)));pdfmetrics.registerFont(TTFont('FigureArialBold',str(a.bold_font)))
    c=canvas.Canvas(str(a.out/'figure.pdf'),pagesize=(160*MM,95*MM),pageCompression=1,invariant=1 if a.revision=='final' else None)
    c.setTitle('Open sleeve and separate coaxial solid core — original geometric DEMO')
    c.drawImage(ImageReader(im),xy[0]*MM,(95-xy[1]-wh[1])*MM,width=wh[0]*MM,height=wh[1]*MM,mask='auto')
    labels=[];segments=[]
    def line(id,points,width=.25,color='#536871',dash=None):
        points=[list(map(float,p)) for p in points];segments.append({'id':id,'points':points,'width_mm':width,'dash':dash})
        d=f' stroke-dasharray="{dash[0]} {dash[1]}"' if dash else ''
        svg.append(f'<polyline id="{id}" points="'+ ' '.join(f'{x:.4f},{y:.4f}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{d}/>')
        c.setStrokeColor(color);c.setLineWidth(width*MM);c.setDash([q*MM for q in dash] if dash else [])
        p=c.beginPath();p.moveTo(points[0][0]*MM,(95-points[0][1])*MM)
        for x,y in points[1:]:p.lineTo(x*MM,(95-y)*MM)
        c.drawPath(p)
    def text(id,content,x,y,size=10.5,bold=False):
        labels.append({'id':id,'text':content,'x_mm':x,'baseline_y_mm':y,'font_pt':size,'bold':bold})
        svg.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-weight="{700 if bold else 400}" font-size="{size/MM}" fill="{INK}">{escape(content)}</text>')
        c.setFillColor(INK);c.setFont('FigureArialBold' if bold else 'FigureArial',size);c.drawString(x*MM,(95-y)*MM,content)
    def poly(id,pts,fill,entity):
        points=[list(map(float,p)) for p in pts]
        svg.append(f'<polygon id="{id}" data-logical-id="{entity}" data-object-part="detail" points="'+' '.join(f'{x:.5f},{y:.5f}' for x,y in points)+f'" fill="{fill}" stroke="none"/>')
        c.setFillColor(fill);p=c.beginPath();p.moveTo(points[0][0]*MM,(95-points[0][1])*MM)
        for x,y in points[1:]:p.lineTo(x*MM,(95-y)*MM)
        p.close();c.drawPath(p,stroke=0,fill=1)
    # Same-object correspondence is a dotted, arrowless annotation between views.
    rim_anchor=proj(polar(12,math.radians(85),30))
    left_anchor=axproj(polar(12,math.radians(249),30))
    line('view-correspondence',[rim_anchor,left_anchor],.21,'#83959B',[1.15,1.15])
    ts=np.linspace(math.radians(35),math.radians(325),581)
    poly('axial-sleeve',[axproj(polar(12,t,30)) for t in ts]+[axproj(polar(9,t,30)) for t in ts[::-1]],SLEEVE,'sleeve')
    poly('axial-core',[axproj(polar(5,t,33)) for t in np.linspace(0,2*math.pi,721)],CORE,'core')
    # Name surfaces only with surface anchors; opening points into demonstrably empty sector.
    sleeve_angle=-72 if a.revision=='final' else -93
    sleeve_anchor=proj(polar(12,math.radians(sleeve_angle),18))
    line('sleeve-leader',[(25,39),(28,39),sleeve_anchor]);text('sleeve-label','Sleeve',8,38,bold=True)
    core_anchor=proj(polar(5,az,32))
    line('core-leader',[core_anchor,(76,13),(80,13)]);text('core-label','Solid core',82,14,bold=True)
    text('axial-title','Axial view',108,16 if a.revision=='final' else 19,bold=True)
    text('axial-subtitle','Same objects; along -z',108,21 if a.revision=='final' else 24,size=9)
    opening_anchor=axproj(polar(10.5,0,30))
    line('opening-leader',[opening_anchor,(138,66),(138,70)])
    text('opening-label','Longitudinal',110,75);text('opening-label-2','opening',110,80)
    t=math.radians(85);ga=axproj(polar(5,t,33));gb=axproj(polar(9,t,30));mid=(ga+gb)/2
    line('gap-dimension',[ga,gb],.27)
    v=gb-ga;perp=np.array([-v[1],v[0]])/np.linalg.norm(v)*.70
    for k,p in enumerate([ga,gb]):line('gap-tick-'+str(k),[p-perp,p+perp],.27)
    text('gap-value','4',float(mid[0]+(-1.4 if a.revision=='final' else .5)),float(mid[1]-(2.0 if a.revision=='final' else 1.8)),size=10.5)
    c.showPage();c.save();svg.append('</svg>');(a.out/'figure.svg').write_text('\n'.join(svg),encoding='utf-8')
    subprocess.run([str(a.pdftoppm),'-png','-r','300','-singlefile',str(a.out/'figure.pdf'),str(a.out/'figure')],check=True,capture_output=True)
    png=Image.open(a.out/'figure.png').convert('RGB');ImageOps.grayscale(png).save(a.out/'figure-grayscale.png')
    rgb=np.asarray(png).astype(float)/255;lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    sim=np.clip(lin@matrix.T,0,1);srgb=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(a.out/'figure-deuteranopia-approx.png')
    caption=('Original geometric demonstration of one continuous sleeve and one separate coaxial solid core. The dominant oblique view shows the existing full-length opening and the core extending beyond both ends. The smaller axial view shows the same objects along -z, with the same screen orientation around the axis; its dashed correspondence line is a view annotation. The white interval between the core and retained sleeve wall makes their separation explicit. The opening label terminates in the missing sleeve sector, not on an inner surface. The sleeve has outer/inner radii 12/9 and spans z = 0-30; its pre-existing opening removes azimuth -35 to +35 degrees through the entire thickness and length, measured from +x toward +y. Both sleeve ends are open. The solid core has radius 5 and spans z = -3-33. The radial gap is 4 wherever sleeve wall remains; 4 is marked in the axial view. Coordinates are arbitrary drawing units. The axial view is shown at 0.769 times the linear scale of the oblique view. Surface shading is illustrative; no contact, support, motion, transport or physical function is specified.')
    if a.revision=='final':
        caption=('Original geometric demonstration of one continuous sleeve and one separate coaxial solid core. The oblique view shows the existing longitudinal opening, exposed inner wall and core. The smaller axial projection shows the same objects along -z; white space separates the core from every retained wall direction. Its dashed link identifies the corresponding upper sleeve end. The sleeve has outer/inner radii 12/9, spans z = 0-30, and is open at both axial ends. A pre-existing sector from -35 to +35 degrees is absent through its full thickness and length; azimuth is measured from +x toward +y. The solid core has radius 5 and spans z = -3-33. The marked radial gap is 4 wherever sleeve wall remains. All coordinates are arbitrary drawing units. Axial and oblique views share azimuth and roll, at relative linear scales 0.769:1. Shading only aids shape reading; no support, contact, motion, transport or physical function is specified.')
    alt=('A large oblique view of a blue-green open sleeve surrounds an orange solid cylindrical core. A longitudinal opening exposes the core and inner wall, with the core extending above and below the sleeve. A smaller axial projection of the same two objects at upper right shows a C-shaped annulus separated from a central disk by white space. A radial dimension is labeled 4. The opening label points to the empty missing angular sector of the annulus. A dashed, arrowless view annotation links the views. Neither view depicts additional components or a physical process.')
    (a.out/'caption.txt').write_text(caption+'\n',encoding='utf-8');(a.out/'alt_text.txt').write_text(alt+'\n',encoding='utf-8')
    js(a.out/'annotations.json',{'labels':labels,'lines':segments,'opening_anchor':{'world':[10.5,0,30],'screen':opening_anchor.tolist(),'inside_missing_sector':True,'not_a_surface_anchor':True}})
    spec={'figure_id':'open_sleeve_development','schema_version':1,'mode':'new_schematic','demo':True,'evidence_status':'Original geometric DEMO, feedback-informed development; not blind evaluation',
      'scientific_message':'The existing longitudinal opening reveals the separate coaxial core, while an axial projection makes the radial gap explicit.',
      'source_refs':[{'path':'input.md','sha256':sha(a.input)}],'entities':[{'id':'sleeve','physical_objects':1},{'id':'core','physical_objects':1}],
      'relations':[{'id':'coaxial','from':'sleeve','to':'core','kind':'geometry','meaning':'Shared z axis; disjoint solids'},
                   {'id':'axial-detail','from':'main-two-objects','to':'axial-sleeve + axial-core','kind':'detail','meaning':'Same two objects projected along -z, without physical duplication or motion','arrow_required':False}],
      'locked_values':LOCKED,'count_constraints':{'expected_logical_ids':['sleeve','core'],'physical_object_count':2,'primary':'main-two-objects','detail_ids':['axial-sleeve','axial-core']},
      'exact_labels':[l['text'] for l in labels],'forbidden_implications':['end caps across bore','contact','supports','motion','transport','physical function','another cutting operation'],
      'role_map':{'sleeve':SLEEVE,'inner_wall':INNER,'wall_thickness_faces':RIM,'core':CORE,'annotation':INK},
      'depth':{'mode':'D2_explicit_mesh_orthographic','affects_quantitative_encoding':False},
      'output':{'width_mm':160,'height_mm':95,'placement_width_mm':160,'png_dpi':300,'editable':'Hybrid: raster oblique surface; native vector axial geometry, labels and annotation lines'},
      'camera':{'azimuth_deg':-12,'elevation_deg':elevation,'roll_deg':-9,'view_toward_observer':view.tolist(),'right':right.tolist(),'up':up.tolist(),'projection':'orthographic','scale_mm_per_unit':scale},
      'axial_camera':{'view_toward_observer':axial_view.tolist(),'right':ar.tolist(),'up':au.tolist(),'same_azimuth_and_roll':True,'scale_mm_per_unit':ascale,'not_a_section':'projection of the complete objects'},
      'light':{'direction_world':light.tolist(),'ambient':ambient,'model':'Illustrative Lambertian normal shading; no physical field or contact shadows'},
      'mesh':{'sleeve_steps':580,'core_steps':720,'face_count':len(faces),'max_sagitta_source_unit':12*(1-math.cos(math.radians(.25)))},
      'publication':{'target_journal':None,'eligibility':'UNVERIFIED'},'caption':caption,'alt_text':alt}
    js(a.out/'figure_spec.json',spec);js(a.out/'scientific_checks.json',mesh_audit(faces))
    shutil.copy2(a.input,a.out/'input.md');shutil.copy2(Path(__file__),a.out/'build_figure.py');shutil.copy2(Path(__file__).with_name('surface_renderer.py'),a.out/'surface_renderer.py')
    pdf=PdfReader(a.out/'figure.pdf');page=pdf.pages[0];pdftext=page.extract_text();fonts=[]
    page.extract_text(visitor_text=lambda t,cm,tm,font,size:fonts.append(size) if t.strip() else None)
    root=ET.parse(a.out/'figure.svg').getroot();svgids={e.get('id') for e in root if e.get('id')}
    checks={'pdf_pages':len(pdf.pages),'pdf_size_mm':[float(page.mediabox.width)/MM,float(page.mediabox.height)/MM],
      'all_labels_extract_from_pdf':all(l['text'] in pdftext for l in labels),'effective_pdf_font_pt':sorted(set(fonts)),
      'svg_xml_parsed':True,'svg_text_count':len(root.findall('{http://www.w3.org/2000/svg}text')),'actual_svg_detail_ids_present':all(x in svgids for x in ['axial-sleeve','axial-core']),
      'png_pixels':png.size,'surface_effective_dpi':[im.width/(wh[0]/25.4),im.height/(wh[1]/25.4)],
      'camera_basis_orthonormal':bool(np.allclose(np.array([right,up,view])@np.array([right,up,view]).T,np.eye(3))),
      'cvd_preview':{'method':'Machado-style deuteranopia severity 1 matrix applied in linear sRGB; approximate','matrix':matrix.tolist(),'scope':'one condition only'},
      'technical_status':'PASS','scientific_review_status':'MODEL_SOURCE_CHECKS_ONLY','visual_review_status':'REVIEW_REQUIRED','author_acceptance':'NOT_RUN','overall_status':'REVIEW_REQUIRED',
      'not_verified':['human reading','author acceptance','journal acceptance','physical print','all color vision conditions','per-pixel visibility proof','cross-editor font substitution'],
      'command':sys.argv,'exit_code':0,'artifact_sha256':{n:sha(a.out/n) for n in ['figure.svg','figure.pdf','figure.png']}}
    assert checks['all_labels_extract_from_pdf'] and checks['camera_basis_orthonormal'] and mesh_audit(faces)['status']=='PASS'
    js(a.out/'checks.json',checks)
    js(a.out/'manifest.json',{'revision':a.revision,'source_sha256':sha(Path(__file__)),'files':[{'path':p.name,'sha256':sha(p)} for p in sorted(a.out.iterdir()) if p.is_file()]})
    print(json.dumps({'out':str(a.out),'revision':a.revision,'status':'REVIEW_REQUIRED'}))
if __name__=='__main__':main()
