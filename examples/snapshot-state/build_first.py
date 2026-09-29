"""Original, fully vector heat-story mechanism figure. DEMO FICTION.

Run with explicit font and Poppler paths; all outputs go below --out.
No solver, benchmark, physical model, or image assets are generated.
"""
from pathlib import Path
import argparse, hashlib, html, json, math, subprocess, sys
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

MM = 72 / 25.4
W, H = 160, 96
P = dict(ink='#233B44', muted='#526871', grid='#CBD8DB', pale='#F4F7F7',
         a='#147A79', afill='#E1F1ED', b='#A56619', bfill='#F6E9D4',
         white='#FFFFFF', boundary='#8BA2A9', faint='#E9EFEF')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Figure:
    def __init__(self, out, name, title):
        self.out, self.name = out, name
        self.c = canvas.Canvas(str(out / (name + '.pdf')), pagesize=(W * MM, H * MM),
                               invariant=1, pageCompression=1)
        self.c.setTitle(title + ' — DEMO FICTION')
        self.c.setAuthor('Original vector diagram; model-assisted design')
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
                      '<title>' + html.escape(title) + '</title>',
                      '<desc>DEMO FICTION. Logical ownership of a representative inter-group face. '
                      'A cached coefficient and its two endpoint snapshots retain A\'s refresh r '
                      'while B independently refreshes its own face set from s to s+1. '
                      'Cache geometry is logical, not a physical heat-flow path.</desc>']
        self.texts, self.lines = [], []
        self.counter = 0
        self.rect(0, 0, W, H, P['white'], None, id='canvas')

    def attrs(self, id=None, entity=None, role=None):
        self.counter += 1
        s = f' id="{id or "shape-"+str(self.counter)}"'
        if entity: s += f' data-entity="{html.escape(entity)}"'
        if role: s += f' data-role="{role}"'
        return s

    def style(self, fill, stroke, lw):
        if fill: self.c.setFillColor(HexColor(fill))
        if stroke: self.c.setStrokeColor(HexColor(stroke))
        self.c.setLineWidth(lw * MM)

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=.3, r=0, **kw):
        self.parts.append(f'<rect{self.attrs(**kw)} x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"/>')
        self.style(fill, stroke, lw)
        self.c.roundRect(x * MM, (H-y-h) * MM, w * MM, h * MM, r * MM,
                         stroke=bool(stroke), fill=bool(fill))

    def line(self, x1, y1, x2, y2, color=None, lw=.3, dash=False, **kw):
        color = color or P['grid']
        self.parts.append(f'<line{self.attrs(**kw)} x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{lw}" stroke-linecap="round"' + (' stroke-dasharray="1.2 1"' if dash else '') + '/>')
        self.style(None, color, lw)
        self.c.setLineCap(1)
        self.c.setDash([1.2*MM, 1*MM] if dash else [])
        self.c.line(x1 * MM, (H-y1) * MM, x2 * MM, (H-y2) * MM)
        self.c.setDash([])
        self.lines.append([x1, y1, x2, y2])

    def poly(self, pts, fill=None, stroke=None, lw=.3, **kw):
        self.parts.append(f'<polygon{self.attrs(**kw)} points="' + ' '.join(f'{x},{y}' for x,y in pts) + f'" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"/>')
        self.style(fill, stroke, lw)
        p=self.c.beginPath(); p.moveTo(pts[0][0]*MM,(H-pts[0][1])*MM)
        for x,y in pts[1:]: p.lineTo(x*MM,(H-y)*MM)
        p.close(); self.c.drawPath(p,fill=bool(fill),stroke=bool(stroke))

    def path(self, points, color, lw=.35, dash=False, **kw):
        # An editable orthogonal/diagonal polyline; logical association only.
        d='M '+' L '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<path{self.attrs(**kw)} d="{d}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linejoin="round"' + (' stroke-dasharray="1.2 1"' if dash else '') + '/>')
        self.style(None,color,lw)
        self.c.setDash([1.2*MM,MM] if dash else [])
        p=self.c.beginPath(); p.moveTo(points[0][0]*MM,(H-points[0][1])*MM)
        for x,y in points[1:]: p.lineTo(x*MM,(H-y)*MM)
        self.c.drawPath(p,stroke=1,fill=0); self.c.setDash([])

    def circle(self, x, y, r, fill=None, stroke=None, lw=.3, **kw):
        self.parts.append(f'<circle{self.attrs(**kw)} cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"/>')
        self.style(fill,stroke,lw)
        self.c.circle(x*MM,(H-y)*MM,r*MM,fill=bool(fill),stroke=bool(stroke))

    def text(self, x, y, txt, size=10, color=None, bold=False, align='left', **kw):
        color=color or P['ink']; face='ArialBold' if bold else 'Arial'
        width=pdfmetrics.stringWidth(txt,face,size)/MM
        lo=x-({'left':0,'center':.5,'right':1}[align])*width
        cmap=pdfmetrics.getFont(face).face.charToGlyph
        assert all(ord(ch) in cmap for ch in txt), ('font',txt)
        assert lo >= 0 and lo+width <= W and y <= H and y-size/MM >= 0, ('bounds',txt,lo,width,y)
        self.parts.append(f'<text{self.attrs(**kw)} x="{x}" y="{y}" font-family="Arial" font-size="{size/MM:.6f}" font-weight="{700 if bold else 400}" text-anchor="' + {'left':'start','center':'middle','right':'end'}[align] + f'" fill="{color}">{html.escape(txt)}</text>')
        self.c.setFont(face,size); self.c.setFillColor(HexColor(color))
        self.c.drawString(lo*MM,(H-y)*MM,txt)
        self.texts.append(dict(text=txt,size_pt=size,left=lo,right=lo+width,top=y-size/MM,bottom=y))

    def arrow(self, x1,y1,x2,y2,color,lw=.45, **kw):
        self.line(x1,y1,x2,y2,color,lw,**kw)
        a=math.atan2(y2-y1,x2-x1); length=1.8; half=.85
        self.poly([(x2,y2),(x2-length*math.cos(a)+half*math.sin(a),y2-length*math.sin(a)-half*math.cos(a)),
                  (x2-length*math.cos(a)-half*math.sin(a),y2-length*math.sin(a)+half*math.cos(a))],color)

    def save(self, pdftoppm):
        self.parts.append('</svg>')
        svg=self.out/(self.name+'.svg'); svg.write_text('\n'.join(self.parts),encoding='utf-8')
        ET.parse(svg)
        self.c.showPage(); self.c.save()
        subprocess.run([str(pdftoppm),'-singlefile','-r','300','-png',str(self.out/(self.name+'.pdf')),str(self.out/self.name)],check=True,capture_output=True)
        im=Image.open(self.out/(self.name+'.png')).convert('RGB')
        im.convert('L').convert('RGB').save(self.out/(self.name+'_gray.png'))
        a=np.asarray(im)/255.; linear=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
        mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
        sim=np.clip(linear@mat.T,0,1)
        srgb=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
        Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(self.out/(self.name+'_deuteranopia.png'))
        reader=PdfReader(self.out/(self.name+'.pdf')); page=reader.pages[0]
        report=dict(pdf_page_count=len(reader.pages),pdf_size_mm=[float(page.mediabox.width)/MM,float(page.mediabox.height)/MM],
                    png_size=list(im.size),font_min_pt=min(t['size_pt'] for t in self.texts),font_max_pt=max(t['size_pt'] for t in self.texts),
                    font_coverage_checked=True,text_bounds_checked=True,svg_images=0,svg_editable_texts=len(self.texts),
                    pdf_searchable_text=page.extract_text(),text_items=self.texts,
                    svg_external_font='Arial; font not redistributed',pdf_fonts='Embedded Arial subsets',
                    geometry='D0. Mesh fragment and logical cache views. No heat-flow arrow.',
                    scientific_status='REVIEW_REQUIRED',author_acceptance='PENDING')
        (self.out/(self.name+'_technical.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report


def header(f):
    f.text(4,6,'Owner-consistent reuse',11,bold=True,id='title')
    f.text(156,6,'DEMO FICTION',9,color=P['muted'],align='right',id='evidence-label')


def mesh(f, x=40, y=16, cols=8, rows=3, sx=10, sy=8, idsuffix=''):
    """A crop, not a full 16x16 group. Row-major i<j face at boundary."""
    mid=x+cols*sx/2; w=cols*sx; h=rows*sy
    f.rect(x,y,w/2,h,P['pale'],None,entity='group-A',role='mesh-context')
    f.rect(mid,y,w/2,h,P['pale'],None,entity='group-B',role='mesh-context')
    for k in range(1,cols):
        f.line(x+k*sx,y,x+k*sx,y+h,P['grid'],.22)
    for k in range(1,rows):
        f.line(x,y+k*sy,x+w,y+k*sy,P['grid'],.22)
    # Open-ended exterior grid: the crop is not the insulated external boundary.
    for k in range(cols+1):
        f.line(x+k*sx,y-1.2,x+k*sx,y,P['grid'],.22)
        f.line(x+k*sx,y+h,x+k*sx,y+h+1.2,P['grid'],.22)
    for k in range(rows+1):
        f.line(x-1.2,y+k*sy,x,y+k*sy,P['grid'],.22)
        f.line(x+w,y+k*sy,x+w+1.2,y+k*sy,P['grid'],.22)
    f.line(mid,y-1.2,mid,y+h+1.2,P['boundary'],.45,dash=True,entity='group-boundary')
    iy=y+sy
    f.rect(mid-sx,iy,sx,sy,P['afill'],P['a'],.32,entity='cell-i')
    f.rect(mid,iy,sx,sy,P['afill'],P['a'],.32,entity='cell-j')
    f.line(mid,iy,mid,iy+sy,P['a'],.9,entity='face-f',role='owned-face')
    f.text(mid-sx/2,iy+sy/2+1.2,'i',11,bold=True,align='center',entity='cell-i')
    f.text(mid+sx/2,iy+sy/2+1.2,'j',11,bold=True,align='center',entity='cell-j')
    f.text(mid,y-2.4,'Face f',10,bold=True,align='center',color=P['a'],entity='face-f')
    return {'i':(mid-sx/2,iy+sy),'f':(mid,iy+sy),'j':(mid+sx/2,iy+sy),'bottom':y+h,'mid':mid}


def triple(f,x,y,w,h,state='r',emphasis=False,order=('Gf','Ti','Tj'),prefix=''):
    f.rect(x,y,w,h,P['afill'],P['a'],.55 if emphasis else .35,r=1.0,entity='A-record-'+prefix,role='retained-cache')
    for k in (1,2):f.line(x+w*k/3,y+1.5,x+w*k/3,y+h-1.5,P['a'],.25)
    for k,t in enumerate(order):
        f.text(x+w*(k+.5)/3,y+h/2+1.1,f'{t}({state})',10,bold=emphasis,align='center',entity=t+'-'+prefix,role='same-owner-event')


def candidate_a(out,args,refined=False):
    name='figure1_owner_states' if not refined else 'figure1_owner_states_final'
    f=Figure(out,name,'A face record before and after independent group decisions')
    header(f)
    mesh(f,y=16)
    f.text(21,25.5,'Group A',10.5,bold=True,align='center',entity='group-A')
    f.text(21,31,'owns f',9.5,color=P['a'],align='center')
    f.text(139,25.5,'Group B',10.5,bold=True,align='center',entity='group-B')
    f.text(139,31,'i < j',9.5,color=P['muted'],align='center')
    if refined:
        f.text(61.5,48,'Before decisions',10,bold=True,align='center')
        f.text(130.5,48,'After decisions',10,bold=True,align='center')
    else:
        f.text(61.5,48,'Before',10,bold=True,align='center')
        f.text(130.5,48,'After',10,bold=True,align='center')
    f.text(4,59,'A-owned',10,bold=True)
    f.text(4,64,'face f',10)
    triple(f,36,54,51,15,prefix='before')
    triple(f,105,54,51,15,emphasis=True,prefix='after')
    f.text(96,58,'Reuse',9,color=P['a'],align='center',bold=True)
    f.arrow(90,63,101.5,63,P['a'],role='state-transition')
    f.text(4,82.5,'B-owned',10,bold=True)
    f.text(4,87.5,'face set',10)
    for x,version in [(36,'s'),(105,'s + 1')]:
        f.rect(x,78,51,12,P['bfill'] if version!='s' else P['pale'],P['b'] if version!='s' else P['boundary'],.4,r=1,entity='B-cache-'+version)
        f.text(x+25.5,85.5,version,11,bold=version!='s',align='center')
    f.text(96,79,'Refresh',9,color=P['b'],align='center',bold=True)
    f.arrow(90,84,101.5,84,P['b'],role='state-transition')
    if refined:
        # Group identities are row labels; equal versioned triples express preservation.
        f.line(36,72,156,72,P['faint'],.25)
    return f.save(args.pdftoppm)


def candidate_b(out,args,refined=False):
    name='figure1_shared_record' if not refined else 'figure1_shared_record_final'
    f=Figure(out,name,'One owner record shared by the face and both endpoint snapshots')
    header(f)
    # A common computational mesh is kept distinct from logical storage below.
    m=mesh(f,x=39,y=18,cols=8,rows=3,sx=10,sy=7)
    f.text(19,26,'Group A',10.5,bold=True,align='center')
    f.text(19,31.5,'owns f',9.5,color=P['a'],align='center')
    f.text(138,26,'Group B',10.5,bold=True,align='center')
    f.text(138,31.5,'i < j',9.5,color=P['muted'],align='center')
    # Three non-directed associations bind the common record to its actual inputs.
    targets=[(29,'Ti','i'),(59,'Gf','f'),(89,'Tj','j')]
    for tx,label,key in targets:
        x,y=m[key]
        f.path([(x,y+.5),(x,40.5),(tx,48.5),(tx,54)],P['a'],.33,dash=True,entity='association-'+key,role='logical-reference')
    f.text(4,49.5,'A-owned',10,bold=True)
    f.text(4,54,'record',10,bold=True)
    triple(f,14,58,90,15,emphasis=refined,order=('Ti','Gf','Tj'),prefix='retained')
    # Shared refresh origin spans all three fields; this is a record, not a thermal layer.
    f.path([(14,75),(14,78),(104,78),(104,75)],P['a'],.4,entity='same-refresh-bracket',role='common-event')
    f.rect(40,75.8,38,4.6,P['white'],None)
    f.text(59,79.3,'same refresh r',10,align='center',bold=True,color=P['a'])
    f.text(59,89,'A reuses',10.5,align='center',bold=True)
    f.text(136,46.5,'B-owned',10,bold=True,align='center')
    f.text(136,51,'face set',10,align='center')
    f.rect(119,54,34,10,P['pale'],P['boundary'],.35,r=1,entity='B-cache-before')
    f.text(136,60.5,'s',11,align='center')
    f.arrow(136,65.5,136,71,P['b'],role='state-transition')
    f.rect(119,72.5,34,10,P['bfill'],P['b'],.5,r=1,entity='B-cache-after')
    f.text(136,79,'s + 1',11,bold=True,align='center')
    f.text(136,89,'B refreshes',10.5,align='center',bold=True)
    return f.save(args.pdftoppm)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True)
    p.add_argument('--bold-font',type=Path,required=True)
    p.add_argument('--pdftoppm',type=Path,required=True)
    p.add_argument('--stage',choices=['first','final-a','final-b'],default='first')
    a=p.parse_args()
    if a.out.exists():p.error('Refusing to overwrite existing directory: '+str(a.out))
    for path in (a.font,a.bold_font,a.pdftoppm):
        if not path.is_file():p.error('Missing dependency: '+str(path))
    pdfmetrics.registerFont(TTFont('Arial',str(a.font)))
    pdfmetrics.registerFont(TTFont('ArialBold',str(a.bold_font)))
    a.out.mkdir(parents=True)
    reports=[]
    if a.stage=='first':reports=[candidate_a(a.out,a),candidate_b(a.out,a)]
    elif a.stage=='final-a':reports=[candidate_a(a.out,a,True)]
    else:reports=[candidate_b(a.out,a,True)]
    manifest={'evidence':'DEMO FICTION; no solver executed','stage':a.stage,
              'builder_sha256':sha(__file__),'font_sha256':sha(a.font),'bold_font_sha256':sha(a.bold_font),
              'python':sys.version,'output_size_mm':[W,H],
              'outputs':{p.name:sha(p) for p in sorted(a.out.iterdir()) if p.is_file()},
              'technical_status':'PASS','scientific_review_status':'REVIEW_REQUIRED',
              'visual_review_status':'REVIEW_REQUIRED','author_acceptance':'PENDING',
              'overall_status':'REVIEW_REQUIRED'}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(a.out),'stage':a.stage,'figures':len(reports),'size_mm':[W,H],'min_font_pt':9}))


if __name__=='__main__':main()
