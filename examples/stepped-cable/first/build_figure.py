"""Standalone vector cable schematic. All lengths are illustrative layout coordinates.

No image assets, measurements, simulation, network access, or candidate sampling.
Rebuild example is in REBUILD.md. Output directories must not already exist.
"""
import argparse
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

W, H = 160 * 72 / 25.4, 90 * 72 / 25.4
CY, ELLIPSE_RATIO = 143.0, 0.47
INK, GUIDE = '#24333C', '#56646D'
CAPTION = ('Schematic of one layered cable with a stepped exposed end. '
           'The outer jacket, solid metal shield sleeve, and polymer insulation '
           'terminate successively, leaving a short tip of the solid copper conductor. '
           'The concentric layers remain continuous toward the intact cable at left. '
           'Illustrative geometry; not to scale.')
ALT = ('A single cable extends from the left and becomes successively narrower toward '
       'the right. A dark blue outer jacket surrounds a thin silver metal sleeve; '
       'the sleeve surrounds pale teal polymer insulation; the insulation surrounds '
       'the central copper conductor. Curved termination faces and contiguous surfaces '
       'show the three covering layers ending in that order, with a small copper tip last.')
PALETTE = {
    'jacket': {'base': '#4B657A', 'surface': ['#384E62', '#7995AB', '#57748B', '#293E50'],
               'face': ['#A2B6C6', '#536F85'], 'stroke': '#2A4153'},
    'shield': {'base': '#A8B4BD', 'surface': ['#7E919F', '#EDF2F4', '#BCC8D0', '#748996'],
               'face': ['#DFE7EB', '#82949F'], 'stroke': '#5D717F'},
    'insulation': {'base': '#7CAFA7', 'surface': ['#5E918B', '#C7E0D9', '#A2CBC2', '#65948E'],
                   'face': ['#DDECE6', '#8AB8AD'], 'stroke': '#477C73'},
    'conductor': {'base': '#BF773E', 'surface': ['#9B5B2D', '#E9B379', '#C8874D', '#8C4C26'],
                  'face': ['#E8BC8B', '#B9753F'], 'stroke': '#81502F'}
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ellipse(x, y, rx, ry):
    k = 0.5522847498307936
    return [('M', x, y-ry), ('C', x+rx*k,y-ry,x+rx,y-ry*k,x+rx,y),
            ('C',x+rx,y+ry*k,x+rx*k,y+ry,x,y+ry),
            ('C',x-rx*k,y+ry,x-rx,y+ry*k,x-rx,y),
            ('C',x-rx,y-ry*k,x-rx*k,y-ry,x,y-ry), ('Z',)]

def cylinder_side(x0, x1, r):
    # Visible cylindrical wall is bounded by the same left ellipse half at each end.
    rx, k, y = r * ELLIPSE_RATIO, 0.5522847498307936, CY
    return [('M',x0,y-r), ('L',x1,y-r),
            ('C',x1-rx*k,y-r,x1-rx,y-r*k,x1-rx,y),
            ('C',x1-rx,y+r*k,x1-rx*k,y+r,x1,y+r), ('L',x0,y+r),
            ('C',x0-rx*k,y+r,x0-rx,y+r*k,x0-rx,y),
            ('C',x0-rx,y-r*k,x0-rx*k,y-r,x0,y-r), ('Z',)]

def path_svg(commands):
    return ' '.join(c[0] + (' ' + ' '.join(f'{v:.5f}' for v in c[1:]) if len(c)>1 else '') for c in commands)

def path_pdf(c, commands):
    p = c.beginPath()
    for a in commands:
        if a[0] == 'M': p.moveTo(a[1], H-a[2])
        elif a[0] == 'L': p.lineTo(a[1], H-a[2])
        elif a[0] == 'C': p.curveTo(a[1],H-a[2],a[3],H-a[4],a[5],H-a[6])
        elif a[0] == 'Z': p.close()
    return p

def scene(revision):
    # Actual material intervals all begin at the same off-frame left position.
    # Only the visible segment begins at the enclosing material's termination.
    layers = [
        dict(id='jacket', label='Outer jacket', radius=43, inner_radius=35, end=190),
        dict(id='shield', label='Metal shield', radius=35, inner_radius=31, end=282),
        dict(id='insulation', label='Polymer insulation', radius=31, inner_radius=11.5, end=350),
        dict(id='conductor', label='Copper conductor', radius=11.5, inner_radius=0, end=405),
    ]
    objects, x0 = [], -30.0
    for l in layers:
        role, r, ri, xe = l['id'], l['radius'], l['inner_radius'], l['end']
        pal = PALETTE[role]
        objects.append(dict(id=role+'-surface', type='path', entity=role, object_part='primary',
                            commands=cylinder_side(x0,xe,r), gradient=pal['surface'],
                            positions=[0,0.25,0.6,1], bounds=[x0-r*ELLIPSE_RATIO,CY-r,xe,CY+r],
                            stroke=pal['stroke'], width=0.65))
        ring = ellipse(xe,CY,r*ELLIPSE_RATIO,r)
        if ri: ring += ellipse(xe,CY,ri*ELLIPSE_RATIO,ri)
        objects.append(dict(id=role+'-termination',type='path',entity=role,object_part='decoration',
                            commands=ring,gradient=pal['face'],positions=[0,1],
                            bounds=[xe-r*ELLIPSE_RATIO,CY-r,xe+r*ELLIPSE_RATIO,CY+r],
                            stroke=pal['stroke'],width=0.65))
        x0 = xe
    labels = [
        dict(id='label-jacket', text='Outer jacket', x=86, y=61, anchor='middle', owner='jacket', size=10.5),
        dict(id='label-shield',text='Metal shield', x=225, y=55, anchor='middle',owner='shield',size=10.5),
        dict(id='label-shield-type',text='Solid sleeve',x=225,y=69,anchor='middle',owner='shield',size=10.5),
        dict(id='label-conductor',text='Copper conductor',x=365,y=66,anchor='middle',owner='conductor',size=10.5),
        dict(id='label-insulation',text='Polymer insulation',x=287,y=219,anchor='middle',owner='insulation',size=10.5),
    ]
    leaders = [
        dict(id='guide-jacket',owner='jacket',points=[[86,70],[106,70],[127,108]]),
        dict(id='guide-shield',owner='shield',points=[[225,78],[225,91],[230,116]]),
        dict(id='guide-conductor',owner='conductor',points=[[365,75],[385,75],[385,134]]),
        dict(id='guide-insulation',owner='insulation',points=[[287,204],[303,204],[315,167]]),
    ]
    return layers,objects,labels,leaders

def write_outputs(out, args):
    out.mkdir(parents=True, exist_ok=False)
    pdfmetrics.registerFont(TTFont('TaskArial', args.font))
    pdfmetrics.registerFont(TTFont('TaskArialBold', args.bold_font))
    layers, objects, labels, leaders = scene(args.revision)
    defs, elements = [], []
    c = canvas.Canvas(str(out/'figure.pdf'), pagesize=(W,H), pageCompression=1, invariant=1)
    c.setTitle('Layered cable: stepped exposed end')
    c.setAuthor('Codex; illustrative structure only')
    c.setFillColor(HexColor('#FFFFFF')); c.rect(0,0,W,H,fill=1,stroke=0)
    for ob in objects:
        gid = 'gradient-' + ob['id']
        xlo,ylo,xhi,yhi = ob['bounds']
        stops=''.join(f'<stop offset="{v}" stop-color="{col}"/>' for v,col in zip(ob['positions'],ob['gradient']))
        defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{ylo}" x2="0" y2="{yhi}">{stops}</linearGradient>')
        d = path_svg(ob['commands'])
        elements.append(f'<path id="{ob["id"]}" data-entity="{ob["entity"]}" data-role="{ob["entity"]}" data-object-part="{ob["object_part"]}" d="{d}" fill="url(#{gid})" fill-rule="evenodd" stroke="{ob["stroke"]}" stroke-width="{ob["width"]}"/>')
        p=path_pdf(c,ob['commands'])
        c.saveState(); c.clipPath(p,stroke=0,fill=0,fillMode=0)
        c.linearGradient(0,H-ylo,0,H-yhi,[HexColor(v) for v in ob['gradient']],positions=ob['positions'],extend=True)
        c.restoreState(); c.setStrokeColor(HexColor(ob['stroke'])); c.setLineWidth(ob['width'])
        c.drawPath(p,stroke=1,fill=0,fillMode=0)
    for guide in leaders:
        pts=guide['points']
        for n,(a,b) in enumerate(zip(pts,pts[1:])):
            elements.append(f'<line id="{guide["id"]}-{n}" data-owner="{guide["owner"]}" x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{GUIDE}" stroke-width="0.7" fill="none"/>')
            c.setStrokeColor(HexColor(GUIDE)); c.setLineWidth(0.7); c.line(a[0],H-a[1],b[0],H-b[1])
        x,y=pts[-1]
        elements.append(f'<circle id="{guide["id"]}-anchor" data-owner="{guide["owner"]}" cx="{x}" cy="{y}" r="1.3" fill="{INK}"/>')
        c.setFillColor(HexColor(INK)); c.circle(x,H-y,1.3,stroke=0,fill=1)
    for label in labels:
        elements.append(f'<text id="{label["id"]}" data-owner="{label["owner"]}" x="{label["x"]}" y="{label["y"]}" font-family="Arial" font-size="{label["size"]}" text-anchor="{label["anchor"]}" fill="{INK}">{escape(label["text"])}</text>')
        c.setFillColor(HexColor(INK)); c.setFont('TaskArial',label['size'])
        c.drawCentredString(label['x'],H-label['y'],label['text'])
    c.showPage(); c.save()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="90mm" viewBox="0 0 {W:.8f} {H:.8f}">\n'
           f'<title>Layered cable: stepped exposed end</title><desc>{escape(ALT)}</desc>\n'
           '<defs>\n'+'\n'.join(defs)+'</defs>\n'+f'<rect id="canvas" width="{W}" height="{H}" fill="#FFFFFF"/>\n'
           +'\n'.join(elements)+'\n</svg>\n')
    (out/'figure.svg').write_text(svg,encoding='utf-8')
    (out/'caption.txt').write_text(CAPTION+'\n',encoding='utf-8')
    (out/'alt_text.txt').write_text(ALT+'\n',encoding='utf-8')
    spec = dict(title='Layered cable: stepped exposed end', evidence='DEMO; no measurements or simulation',
        main_reading='One intact coaxial cable has coverings terminating successively toward one exposed copper tip.',
        input=dict(path=str(args.input),sha256=sha(args.input)),
        output=dict(width_mm=160,height_mm=90,placement_width_mm=160,png_dpi=300),
        representation='D1 vector 2.5D, common elliptical cross-sections, opaque layers, no extra local view',
        geometry_basis='Illustrative layout units only. No real diameter, length, tolerance or cutting method is asserted.',
        object_count=1, material_count=4, layers=layers, actual_common_left_start=-30,
        relations=[dict(type='contains',outer='jacket',inner='shield'),dict(type='contains',outer='shield',inner='insulation'),
                   dict(type='contains',outer='insulation',inner='conductor'),dict(type='separates',material='insulation',a='shield',b='conductor'),
                   dict(type='termination_order',left_to_right=['jacket','shield','insulation','conductor'])],
        exact_labels=[l['text'] for l in labels],locked_values=['one cable','solid copper core','continuous polymer insulation',
          'continuous solid thin-walled metal shield sleeve, not braid','outer jacket surrounds sleeve','coaxial nesting',
          'shield does not touch conductor','no applied flow or signal','no physical dimensions'],
        allowed_modifications='Illustrative viewpoint, geometry proportions, labels, styling; at most one content revision after first render',
        semantic_roles=PALETTE, palette_origin='New task-specific hand-selected palette; no reference-palette attribution',
        fonts=dict(latin=str(args.font),bold=str(args.bold_font),latin_sha256=sha(args.font),bold_sha256=sha(args.bold_font)),
        revision=args.revision, objects=objects,labels=labels,leaders=leaders)
    (out/'figure_spec.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    command=[str(args.pdftoppm),'-png','-r','300','-singlefile',str(out/'figure.pdf'),str(out/'figure')]
    run=subprocess.run(command,capture_output=True,text=True)
    (out/'render_receipt.json').write_text(json.dumps(dict(command=command,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr),indent=2)+'\n')
    run.check_returncode()
    im=Image.open(out/'figure.png').convert('RGB')
    im.save(out/'figure.png',dpi=(300,300))
    a=np.asarray(im,dtype=np.float64)/255
    linear=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    lum=linear@np.array([.2126,.7152,.0722])
    gray=np.repeat(lum[:,:,None],3,axis=2)
    mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    def encode(rgb):
        rgb=np.clip(rgb,0,1)
        return np.uint8(np.rint(255*np.where(rgb<=.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055)))
    Image.fromarray(encode(gray)).save(out/'qa-grayscale.png',dpi=(300,300))
    Image.fromarray(encode(linear@mat.T)).save(out/'qa-deuteranomaly100.png',dpi=(300,300))
    # At 96 CSS px/in: 160 mm spans 605 px. Physical monitor calibration is not asserted.
    screen=(round(160/25.4*96),round(90/25.4*96))
    im.resize(screen,Image.Resampling.LANCZOS).save(out/'qa-160mm-at96dpi.png',dpi=(96,96))
    (out/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Cable schematic 160 mm</title>'
       '<style>body{margin:24px;background:#e9ecef}img{display:block;width:160mm;height:90mm;background:white;'
       'margin-bottom:24px}</style><img src="figure.svg" alt="Normal vector view">'
       '<img src="qa-grayscale.png" alt="Linear luminance grayscale">'
       '<img src="qa-deuteranomaly100.png" alt="Machado deuteranomaly severity 100">',encoding='utf-8')
    pdf=PdfReader(out/'figure.pdf'); page=pdf.pages[0]
    texts=page.extract_text()
    checks=dict(one_pdf_page=len(pdf.pages)==1,vector_pdf_no_images=len(page.images)==0,
       pdf_width_mm=round(float(page.mediabox.width)*25.4/72,6),
       pdf_height_mm=round(float(page.mediabox.height)*25.4/72,6),
       png_pixels=list(im.size),png_dpi=Image.open(out/'figure.png').info.get('dpi'),
       labels_searchable=all(l['text'] in texts for l in labels),
       min_label_pt=min(l['size'] for l in labels),all_labels_ge_8pt=all(l['size']>=8 for l in labels),
       nesting_radii=all(layers[i]['inner_radius']==layers[i+1]['radius'] for i in range(3)),
       ordered_end_positions=all(layers[i]['end']<layers[i+1]['end'] for i in range(3)),
       distinct_termination_planes=len({l['end'] for l in layers})==4,
       svg_text_nodes=svg.count('<text '),svg_embedded_images=svg.count('<image '),svg_primary_materials=svg.count('data-object-part="primary"'))
    status='PASS' if all(checks[k] for k in ['one_pdf_page','vector_pdf_no_images','labels_searchable','all_labels_ge_8pt','nesting_radii','ordered_end_positions','distinct_termination_planes']) else 'FAIL'
    record=dict(technical_status=status,scientific_review_status='REVIEW_REQUIRED',visual_review_status='REVIEW_REQUIRED',
        author_acceptance='NOT_REQUESTED_OR_RECEIVED',overall_status='REVIEW_REQUIRED',checks=checks,
        runtime=dict(python=platform.python_version(),executable=str(args.python or 'current interpreter')),
        simulation=dict(grayscale='linear sRGB luminance',cvd='Machado 2009 deuteranomaly severity 100',matrix=mat.tolist()),
        limitations=['No measured geometry','No physical render or optical/electrical simulation','No human reading study or author approval',
                    'No journal-specific rules checked','SVG cross-platform font substitution not tested','Curved-surface topology visually reviewed separately'],
        hashes={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    (out/'checks.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(out),technical_status=status,checks=checks),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--font',required=True,type=Path)
    p.add_argument('--bold-font',required=True,type=Path)
    p.add_argument('--pdftoppm',required=True,type=Path)
    p.add_argument('--python')
    p.add_argument('--revision',choices=['first','final'],default='first')
    write_outputs(p.parse_args().out,p.parse_args())
