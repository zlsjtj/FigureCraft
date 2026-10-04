#!/usr/bin/env python3
"""Rebuild the DEMO manuscript and editable vector figure in a fresh directory.

Requires reportlab, Pillow, numpy, pypdf, explicit font files and pdftoppm.
No input is retrieved from the network. No fixed user/workspace path is used.
The adjacent manuscript_template.md, caption.md and alt.md are source assets.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

MM = 72 / 25.4
W, H = 160.0, 100.0
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


class Scene:
    """A single flat scene renders SVG and embedded-text vector PDF."""
    def __init__(self, outline=False):
        self.items = []
        self.outline = outline
        self.n = 0

    def add(self, kind, **kw):
        self.n += 1
        kw.setdefault('id', f'{kind}-{self.n}')
        kw['kind'] = kind
        if self.outline and kind != 'text':
            if kw.get('fill') not in (None, 'none', '#FFFFFF'):
                kw['fill'] = '#FFFFFF'
            if kw.get('stroke'):
                kw['stroke'] = '#617181'
        self.items.append(kw)
        return kw

    def poly(self, pts, fill, stroke=None, sw=.3, **kw):
        return self.add('polygon', points=pts, fill=fill, stroke=stroke, sw=sw, **kw)

    def rect(self, x, y, w, h, fill, stroke=None, sw=.3, **kw):
        return self.add('rect', x=x, y=y, width=w, height=h, fill=fill, stroke=stroke, sw=sw, **kw)

    def circle(self, x, y, r, fill, stroke=None, sw=.3, **kw):
        return self.add('circle', cx=x, cy=y, r=r, fill=fill, stroke=stroke, sw=sw, **kw)

    def line(self, pts, stroke='#75828D', sw=.35, **kw):
        return self.add('polyline', points=pts, fill='none', stroke=stroke, sw=sw, **kw)

    def text(self, x, y, text, size=10, fill='#203444', bold=False, anchor='start', **kw):
        return self.add('text', x=x, y=y, text=text, size=size, fill=fill,
                        bold=bold, anchor=anchor, **kw)

    def arrow(self, pts, color='#536978', sw=.45, **kw):
        self.line(pts, color, sw, **kw)
        (x0,y0),(x1,y1)=pts[-2:]
        a=math.atan2(y1-y0,x1-x0)
        L,B=1.9,.95
        bx,by=x1-L*math.cos(a),y1-L*math.sin(a)
        self.poly([(x1,y1),(bx-B*math.sin(a),by+B*math.cos(a)),
                   (bx+B*math.sin(a),by-B*math.cos(a))],color,
                  **{k:v for k,v in kw.items() if k!='id'})

    def svg(self, dest):
        root=ET.Element(f'{{{NS}}}svg', {'width':'160mm','height':'100mm',
                           'viewBox':'0 0 160 100','role':'img',
                           'aria-labelledby':'title description'})
        ET.SubElement(root, f'{{{NS}}}title', id='title').text='DEMO: same carrier, new insertion'
        ET.SubElement(root, f'{{{NS}}}desc', id='description').text=(
            'Two successive insertion states of one carrier. Unlock invalidates the map; '
            'relock advances generation. Refit for the new pair, then reuse while locked.')
        for o in self.items:
            a={'id':o['id']}
            for k in ('logical_id','object_part','state','role','relation','entity'):
                if k in o:a['data-'+k.replace('_','-')]=str(o[k])
            if o['kind']=='text':
                a.update(x=str(o['x']),y=str(o['y']),fill=o['fill'],
                         **{'font-family':'Arial','font-size':f'{o["size"]/MM:.8f}',
                            'font-weight':'700' if o['bold'] else '400',
                            'text-anchor':o['anchor']})
                ET.SubElement(root,f'{{{NS}}}text',a).text=o['text']
                continue
            a['fill']=o.get('fill') or 'none'
            a['stroke']=o.get('stroke') or 'none'
            if o.get('stroke'):a['stroke-width']=str(o.get('sw',.3))
            if o.get('dash'):a['stroke-dasharray']=o['dash']
            a['stroke-linejoin']='round'
            a['stroke-linecap']='round'
            if o['kind'] in ('polygon','polyline'):
                a['points']=' '.join(f'{x:.6f},{y:.6f}' for x,y in o['points'])
            elif o['kind']=='rect':
                for k in ('x','y','width','height'):a[k]=str(o[k])
                if o.get('rx'):a['rx']=str(o['rx'])
            else:
                for k in ('cx','cy','r'):a[k]=str(o[k])
            ET.SubElement(root,f'{{{NS}}}'+o['kind'],a)
        ET.ElementTree(root).write(dest,encoding='utf-8',xml_declaration=True)

    def pdf(self, dest):
        c=canvas.Canvas(str(dest),pagesize=(W*MM,H*MM),pageCompression=1,invariant=1)
        c.setTitle('DEMO: same carrier, new insertion')
        c.setAuthor('Constructed demonstration; generated with PaperCraft and FigureCraft')
        for o in self.items:
            if o['kind']=='text':
                c.setFillColor(o['fill'])
                c.setFont('DemoBold' if o['bold'] else 'DemoRegular',o['size'])
                fn={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[o['anchor']]
                fn(o['x']*MM,(H-o['y'])*MM,o['text'])
                continue
            fill=o.get('fill') not in (None,'none')
            stroke=bool(o.get('stroke'))
            if fill:c.setFillColor(o['fill'])
            if stroke:c.setStrokeColor(o['stroke'])
            c.setLineWidth(o.get('sw',.3)*MM)
            c.setLineCap(1)
            c.setLineJoin(1)
            c.setDash([float(v)*MM for v in o['dash'].split()] if o.get('dash') else [])
            if o['kind'] in ('polygon','polyline'):
                p=c.beginPath()
                for i,(x,y) in enumerate(o['points']):
                    (p.moveTo if i==0 else p.lineTo)(x*MM,(H-y)*MM)
                if o['kind']=='polygon':p.close()
                c.drawPath(p,stroke=int(stroke),fill=int(fill))
            elif o['kind']=='rect':
                if o.get('rx'):
                    c.roundRect(o['x']*MM,(H-o['y']-o['height'])*MM,
                                o['width']*MM,o['height']*MM,o['rx']*MM,
                                stroke=int(stroke),fill=int(fill))
                else:
                    c.rect(o['x']*MM,(H-o['y']-o['height'])*MM,
                           o['width']*MM,o['height']*MM,stroke=int(stroke),fill=int(fill))
            else:c.circle(o['cx']*MM,(H-o['cy'])*MM,o['r']*MM,stroke=int(stroke),fill=int(fill))
        c.showPage()
        c.save()


def carrier(s, cx, cy, angle, state, primary):
    scale=1.16
    a=math.radians(angle)
    def xy(x,y):
        # Scientific x,y remain exact on the front face; display rotation is illustrative.
        X,Y=(x-15)*scale, -(y-10)*scale
        return cx+X*math.cos(a)-Y*math.sin(a),cy+X*math.sin(a)+Y*math.cos(a)
    corners=[xy(-5,25),xy(35,25),xy(35,-5),xy(-5,-5)]
    attrs={'logical_id':'carrier','state':state,'role':'carrier','entity':'carrier'}
    s.poly([(x,y+1.15) for x,y in corners], '#C8D7DD','#8CA5AF',.3,
           id=f'{state}-rim',object_part='decoration',**attrs)
    s.poly(corners,'#F3F8F9','#6E8E9A',.42,id=f'{state}-face',
           object_part='primary' if primary else 'detail',**attrs)
    for name,(x,y) in zip(('F1','F2','F3'),((0,0),(30,0),(0,20))):
        px,py=xy(x,y)
        s.circle(px,py,.8*scale,'#B9672F','#8E451B',.2,
                 id=f'{state}-{name}',logical_id=name,
                 object_part='primary' if primary else 'detail',
                 state=state,role='fiducial',entity='fiducial')
    for row,y in enumerate((6,12)):
        for col,x in enumerate((6,12,18,24)):
            name=f'W{row*4+col+1}'
            px,py=xy(x,y)
            s.circle(px,py,1.8*scale,'#CBE3ED','#34788F',.35,
                     id=f'{state}-{name}',logical_id=name,
                     object_part='primary' if primary else 'detail',
                     state=state,role='well',entity='well')
    # This symbol represents identification, not a claimed valid QR code or exact placement.
    def qr_rect(x,y,w,h,fill,tag):
        s.poly([xy(x,y),xy(x+w,y),xy(x+w,y-h),xy(x,y-h)],fill,
               id=f'{state}-id-{tag}',logical_id='carrier-id',
               state=state,role='identity',object_part='decoration')
    qr_rect(23.4,23.1,6.1,6.1,'#FFFFFF','background')
    for k,(x,y) in enumerate(((23.8,22.7),(27,22.7),(23.8,19.5))):
        qr_rect(x,y,1.9,1.9,'#2C4551',f'{k}-outer')
        qr_rect(x+.38,y-.38,1.14,1.14,'#FFFFFF',f'{k}-inner')
        qr_rect(x+.7,y-.7,.5,.5,'#2C4551',f'{k}-dot')
    for k,(x,y) in enumerate(((27,19.5),(28,19.5),(27,18.5),(28.5,18.2),(26.3,21),(26.3,20))):
        qr_rect(x,y,.65,.65,'#2C4551',f'bit-{k}')


def scene(outline=False):
    s=Scene(outline)
    s.rect(0,0,W,H,'#FFFFFF',id='paper')
    s.text(5,7.6,'Same carrier. New insertion.',12,bold=True,id='main-label')
    s.text(155,7.6,'DEMO',9,fill='#7C5544',bold=True,anchor='end',id='demo-label')
    s.text(5,16,'Insertion g',10.5,bold=True,id='state-g-label')
    s.text(94,16,'Insertion g+1',10.5,bold=True,id='state-gplus1-label')
    carrier(s,35.5,39,0,'g',True)
    carrier(s,124.5,39,-8,'gplus1',False)
    s.text(80,27,'Unlock',9.5,anchor='middle',id='unlock-label')
    s.text(80,32,'map invalid',9,fill='#954421',anchor='middle',id='invalid-label')
    s.arrow([(70,39),(90,39)],'#5C7180',.5,id='event-arrow',relation='reinsertion')
    s.text(80,47,'Relock',9.5,anchor='middle',id='relock-label')
    s.text(80,53,'g → g+1',9.5,anchor='middle',id='generation-label')
    s.text(5,65,'3 fiducials · 8 wells',9,fill='#425968',id='counts-label')
    s.text(94,65,'Same ID · changed pose',9,fill='#425968',id='pose-label')
    for x,state,key in ((5,'g','ID + g'),(94,'gplus1','ID + g+1')):
        s.rect(x,69,61,17,'#EEF5F8','#B5CBD5',.3,rx=1.8,
               id=f'{state}-map-box',logical_id='current-map',
               object_part='primary' if state=='g' else 'detail',state=state,role='mapping')
        s.text(x+4,74.7,key,9.5,bold=True,id=f'{state}-key-label')
        s.text(x+4,82,'Fit once → reuse while locked',9.5,id=f'{state}-reuse-label')
    s.text(80,78.3,'refit',9.5,fill='#4D6878',anchor='middle',id='refit-label')
    s.arrow([(69,82),(91,82)],'#7894A4',.38,id='map-update-arrow',relation='replace-current-map')
    s.rect(5,90,150,7.4,'#FAF1EA',None,rx=1.3,id='rejection-background')
    s.text(80,95,'Incomplete new fit → no coordinates',10,fill='#87451F',
           anchor='middle',id='rejection-rule')
    return s


def make_table(rows):
    out=['| Scenario | Frames | Insertions | Program | Time (s) | Error (mm) | Output | Rejected |',
         '|---|---:|---:|---|---:|---:|---:|---:|']
    for r in rows:
        label=r['scenario'].split('_',1)[0]
        vals=[label,r['frames'],r['insertions'],r['variant'],r['total_time_s'],
              r['median_error_mm'] or '—',r['output_frames'],r['rejected_frames']]
        out.append('| '+' | '.join(vals)+' |')
    return '\n'.join(out)


def check_content(rows, svg_file, pdf_file):
    svg=ET.parse(svg_file).getroot()
    circles=svg.findall(f'{{{NS}}}circle')
    by_state={}
    for st in ('g','gplus1'):
        fs=[o for o in circles if o.get('data-state')==st and o.get('data-role')=='fiducial']
        ws=[o for o in circles if o.get('data-state')==st and o.get('data-role')=='well']
        assert len(fs)==3 and len(ws)==8
        assert {o.get('data-logical-id') for o in fs}=={'F1','F2','F3'}
        assert {o.get('data-logical-id') for o in ws}=={f'W{k}' for k in range(1,9)}
        assert all(abs(float(o.get('r'))-.8*1.16)<1e-8 for o in fs)
        assert all(abs(float(o.get('r'))-1.8*1.16)<1e-8 for o in ws)
        by_state[st]={'fiducials':len(fs),'wells':len(ws),'identities_match':True}
    # Test pairwise geometry in the actual SVG, not only the sidecar declaration.
    p={st:{o.get('data-logical-id'):(float(o.get('cx')),float(o.get('cy')))
           for o in circles if o.get('data-state')==st} for st in ('g','gplus1')}
    max_pair_error=0
    for a in p['g']:
        for b in p['g']:
            max_pair_error=max(max_pair_error,abs(math.dist(p['g'][a],p['g'][b])-math.dist(p['gplus1'][a],p['gplus1'][b])))
    assert max_pair_error<1e-7
    labels=svg.findall(f'{{{NS}}}text')
    min_pt=min(float(o.get('font-size'))*MM for o in labels)
    assert min_pt>=8
    assert len(rows)==13
    assert sum(1 for r in rows if not r['median_error_mm'])==3
    for r in rows:assert int(r['output_frames'])+int(r['rejected_frames'])==int(r['frames'])
    pdf=PdfReader(pdf_file)
    assert len(pdf.pages)==1
    size=[float(pdf.pages[0].mediabox.width)/MM,float(pdf.pages[0].mediabox.height)/MM]
    assert abs(size[0]-160)<.001 and abs(size[1]-100)<.001
    text=pdf.pages[0].extract_text()
    assert 'DEMO' in text and 'Incomplete new fit' in text
    values={(r['scenario'],r['variant']):r for r in rows}
    speedup=float(values['B_reinserted','V2']['total_time_s'])/float(values['B_reinserted','V3']['total_time_s'])
    penalty=(float(values['C_one_frame','V3']['total_time_s'])/float(values['C_one_frame','V2']['total_time_s'])-1)*100
    return {'technical_status':'PASS','source_rows':len(rows),'missing_error_values':3,
            'actual_svg_object_counts':by_state,'max_repeated_geometry_distance_error_mm':max_pair_error,
            'pdf_page_mm':size,'svg_bitmap_count':len(svg.findall(f'{{{NS}}}image')),
            'minimum_effective_font_pt':min_pt,'text_nodes':len(labels),
            'derived_values':{'B_V2_time_divided_by_V3':speedup,'C_V3_extra_time_percent':penalty},
            'limits':['No arbitrary-shape collision guarantee','No clinical color-vision certification',
                      'No author acceptance','Geometry validates this demonstration, not a physical device']}


def qa_views(png,out):
    im=Image.open(png).convert('RGB')
    ImageOps.grayscale(im).save(out/'figure-gray.png')
    arr=np.asarray(im,dtype=float)/255
    lin=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    # Explicit full-severity deuteranopia approximation; not a medical assessment.
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    cv=np.clip(lin @ matrix.T,0,1)
    rgb=np.where(cv<=.0031308,12.92*cv,1.055*cv**(1/2.4)-.055)
    Image.fromarray(np.round(rgb*255).astype('uint8')).save(out/'figure-deuteranopia.png')
    record(out/'color-view-method.json',{'method':'linear RGB matrix approximation',
        'matrix':matrix.tolist(),'condition':'deuteranopia approximation, full severity',
        'scope':'Single screening view, not certification of all color-vision conditions'})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--bold-font',type=Path,required=True)
    ap.add_argument('--pdftoppm',type=Path,required=True)
    ap.add_argument('--outline',action='store_true')
    args=ap.parse_args()
    for p in (args.inputs/'materials.md',args.inputs/'results.csv',args.font,args.bold_font,args.pdftoppm):
        if not p.is_file():raise FileNotFoundError(p)
    if args.out.exists():raise FileExistsError(f'Refusing to overwrite existing output: {args.out}')
    args.out.mkdir(parents=True)
    source=Path(__file__).resolve().parent
    pdfmetrics.registerFont(TTFont('DemoRegular',str(args.font)))
    pdfmetrics.registerFont(TTFont('DemoBold',str(args.bold_font)))
    s=scene(args.outline)
    # All actual labels must be represented by the selected fonts.
    for o in s.items:
        if o['kind']=='text':
            cmap=pdfmetrics.getFont('DemoBold' if o['bold'] else 'DemoRegular').face.charToGlyph
            missing=[c for c in o['text'] if ord(c) not in cmap]
            if missing:raise ValueError(f'Missing font glyphs: {missing}')
    s.svg(args.out/'figure.svg')
    s.pdf(args.out/'figure.pdf')
    cmd=[str(args.pdftoppm),'-png','-singlefile','-r','300',str(args.out/'figure.pdf'),str(args.out/'figure')]
    proc=subprocess.run(cmd,check=False,capture_output=True,text=True)
    record(args.out/'render-command.json',{'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    if proc.returncode:raise RuntimeError(f'pdftoppm failed: {proc.stderr}')
    with (args.inputs/'results.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    check=check_content(rows,args.out/'figure.svg',args.out/'figure.pdf')
    record(args.out/'technical-checks.json',check)
    qa_views(args.out/'figure.png',args.out)
    if not args.outline:
        caption=(source/'caption.md').read_text(encoding='utf-8').strip()
        manuscript=(source/'manuscript_template.md').read_text(encoding='utf-8').replace('@CAPTION@',caption).replace('@RESULTS_TABLE@',make_table(rows))
        (args.out/'manuscript.md').write_text(manuscript,encoding='utf-8')
        for n in ('caption.md','alt.md'):shutil.copyfile(source/n,args.out/n)
        shutil.copyfile(args.inputs/'results.csv',args.out/'results.csv')
        prose='\n'.join(line for line in manuscript.splitlines() if line and not line.startswith(('#','|','![','*Table','**Figure','*DEMO')))
        word_count=len(re.findall(r"\b[\w]+(?:[’'−–-][\w]+)*\b",prose))
        record(args.out/'word-count.json',{'words':word_count,'scope':'Abstract plus section prose; title, headings, figure caption, table and DEMO notice excluded',
                                        'method':'Unicode word tokens, hyphenated compounds count once'})
        html='<html><head><meta charset="utf-8"><title>DEMO manuscript preview</title><style>body{max-width:175mm;margin:12mm auto;font:11pt/1.5 Arial;color:#203444}h1{font-size:22pt;line-height:1.15}h2{font-size:13pt}pre{white-space:pre-wrap;font:inherit}img{width:160mm;height:100mm}table{border-collapse:collapse;font-size:9pt}td,th{padding:3px 7px;border-bottom:1px solid #ccd8df}td:nth-child(n+2){text-align:right}.caption{font-size:10pt}</style></head><body>'
        # Minimal review preview, preserving literal Markdown table rather than changing its values.
        for block in manuscript.split('\n\n'):
            if block.startswith('# '):html+='<h1>'+escape(block[2:])+'</h1>'
            elif block.startswith('## '):html+='<h2>'+escape(block[3:])+'</h2>'
            elif block.startswith('!['):html+='<img src="figure.svg" alt="'+escape((source/'alt.md').read_text()).replace('"','&quot;')+'">'
            elif block.startswith('|'):
                lines=block.splitlines();html+='<table>'
                for i,line in enumerate(lines):
                    if i==1:continue
                    tag='th' if i==0 else 'td'
                    html+='<tr>'+''.join(f'<{tag}>'+escape(v.strip())+f'</{tag}>' for v in line.strip('|').split('|'))+'</tr>'
                html+='</table>'
            else:html+='<p>'+escape(block).replace('**','').replace('*','')+'</p>'
        (args.out/'manuscript_preview.html').write_text(html+'</body></html>',encoding='utf-8')
    record(args.out/'figure_spec.json',{
        'evidence_status':'DEMO; manually constructed data, no physical experiments',
        'size_mm':[160,100],'placement_width_mm':160,
        'takeaway':'An unchanged carrier ID does not preserve a map across reinsertion; generation bounds reuse.',
        'representation':'One carrier shown in two successive insertion states; same scale and geometry, illustrative second pose.',
        'depth':'D1 shallow schematic rim; exact planar front-face geometry; no depth measurement.',
        'primary_entities':{'carrier':1,'fiducials':3,'wells':8,'valid_map_at_one_time':1},
        'state_views':['g','gplus1'],
        'locked_values':{'outline_x':[-5,35],'outline_y':[-5,25],
                         'fiducials':[[0,0],[30,0],[0,20]],'fiducial_radius_mm':.8,
                         'well_x':[6,12,18,24],'well_y':[6,12],'well_radius_mm':1.8},
        'relations':[{'id':'reinsertion','from':'g','to':'gplus1','type':'temporal event',
                      'meaning':'unlock invalidates immediately; reclosing increments generation'},
                     {'id':'replace-current-map','from':'g-map-box','to':'gplus1-map-box',
                      'type':'temporal replacement','meaning':'new fit replaces the single current mapping'}],
        'role_colors':{'carrier':'#F3F8F9','fiducial':'#B9672F','well':'#CBE3ED',
                       'map':'#EEF5F8','invalid_or_rejected':'#954421'},
        'noncolor_cues':'fiducials smaller and solid; wells larger and outlined; failure has explicit words',
        'exact_labels':['DEMO','Insertion g','Insertion g+1','Old map','invalid','ID + g','ID + g+1',
                        'Fit once → reuse while locked','Incomplete new fit → no coordinates'],
        'allowed_schematic_choices':['second insertion image rotation','ID icon placement','unmeasured shallow rim'],
        'excluded_from_figure':'performance data and affine numerical example retained in manuscript',
        'sources':{p.name:sha(p) for p in args.inputs.iterdir() if p.is_file()},
        'items':s.items})
    runtime={'python':sys.version,'python_executable_sha256':sha(sys.executable),
             'versions':{n:importlib.metadata.version(n) for n in ('reportlab','numpy','Pillow','pypdf')},
             'dependencies':{str(p.resolve()):sha(p) for p in (args.font,args.bold_font,args.pdftoppm)},
             'executed_module_files':{str(Path(m.__file__).resolve()):sha(m.__file__) for m in list(sys.modules.values())
                                      if getattr(m,'__file__',None) and Path(m.__file__).is_file()
                                      and any(str(m.__name__).startswith(n) for n in ('reportlab','PIL','numpy','pypdf'))}}
    record(args.out/'runtime-dependencies.json',runtime)
    record(args.out/'manifest.json',{p.name:sha(p) for p in args.out.iterdir() if p.is_file()})
    print(json.dumps({'output':str(args.out.resolve()),'technical_status':check['technical_status'],
                      'font_min_pt':check['minimum_effective_font_pt'],
                      'word_count':None if args.outline else word_count},ensure_ascii=False))


if __name__=='__main__':main()
