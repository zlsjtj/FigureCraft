"""Original DEMO rack illustration; native vector SVG and PDF, with PNG QA.

Rebuild: python build_figure.py --data references.json --out NEW_DIRECTORY
    --font /path/arial.ttf --bold-font /path/arialbd.ttf --pdftoppm /path/pdftoppm
No output directory is overwritten. No renderer from another example is used.
"""
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

W, H = 160 * 72 / 25.4, 80 * 72 / 25.4
INK = '#263D4B'
OUTLINE = '#587B89'
TEAL = '#C1E3DF'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Drawing:
    def __init__(self, out):
        self.out = out
        self.pdf = canvas.Canvas(str(out / 'figure.pdf'), pagesize=(W, H), invariant=1)
        self.pdf.setTitle('DEMO dilution reference rack')
        self.pdf.setAuthor('Model-assisted original teaching illustration')
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="80mm" viewBox="0 0 {W:.6f} {H:.6f}">',
                    '<title>One physical rack and one shared reference list</title>',
                    '<desc>Six equal-fill capped vials, A to F, correspond to 0, 1, 4, 16, 64, 256 micromolar. Two independent analyses read one electronic list.</desc>']
        self.labels = []

    def style(self, fill, stroke, width):
        if fill != 'none':
            self.pdf.setFillColor(fill)
        if stroke != 'none':
            self.pdf.setStrokeColor(stroke)
        self.pdf.setLineWidth(width)

    def rect(self, id, x, y, w, h, fill='none', stroke='none', sw=.8, rx=0, attrs=''):
        self.style(fill, stroke, sw)
        self.svg.append(f'<rect id="{id}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {attrs}/>')
        self.pdf.roundRect(x, H-y-h, w, h, rx, stroke=int(stroke!='none'), fill=int(fill!='none'))

    def ellipse(self, id, cx, cy, rx, ry, fill='none', stroke='none', sw=.8, attrs=''):
        self.style(fill, stroke, sw)
        self.svg.append(f'<ellipse id="{id}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {attrs}/>')
        self.pdf.ellipse(cx-rx, H-cy-ry, cx+rx, H-cy+ry, stroke=int(stroke!='none'), fill=int(fill!='none'))

    def path(self, id, cmds, fill='none', stroke='none', sw=.8, attrs=''):
        self.style(fill, stroke, sw)
        d = ' '.join(c[0] + ' '.join(f'{n:g}' for n in c[1:]) for c in cmds)
        self.svg.append(f'<path id="{id}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {attrs}/>')
        p = self.pdf.beginPath()
        for c in cmds:
            if c[0]=='M': p.moveTo(c[1], H-c[2])
            elif c[0]=='L': p.lineTo(c[1], H-c[2])
            elif c[0]=='C': p.curveTo(c[1],H-c[2],c[3],H-c[4],c[5],H-c[6])
            elif c[0]=='Z': p.close()
        self.pdf.drawPath(p, fill=int(fill!='none'), stroke=int(stroke!='none'))

    def line(self, id, x1, y1, x2, y2, stroke=OUTLINE, sw=.8, attrs=''):
        self.style('none', stroke, sw)
        self.svg.append(f'<line id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" {attrs}/>')
        self.pdf.line(x1, H-y1, x2, H-y2)

    def text(self, id, x, y, text, size=10, bold=False, anchor='start', fill=INK):
        font = 'ArialBold' if bold else 'Arial'
        width = pdfmetrics.stringWidth(text,font,size)
        xx = x - (width/2 if anchor=='middle' else width if anchor=='end' else 0)
        self.svg.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{fill}">{escape(text)}</text>')
        self.pdf.setFont(font,size)
        self.pdf.setFillColor(fill)
        self.pdf.drawString(xx,H-y,text)
        self.labels.append({'id':id,'text':text,'size_pt':size,'bounds':[xx,y-size,xx+width,y+size*.22]})

    def save(self):
        self.svg.append('</svg>')
        (self.out/'figure.svg').write_text('\n'.join(self.svg),encoding='utf-8')
        self.pdf.showPage()
        self.pdf.save()


def main():
    ap=argparse.ArgumentParser()
    for arg in ('data','out','font','bold-font','pdftoppm'):
        ap.add_argument('--'+arg,required=True,type=Path)
    ap.add_argument('--revision',choices=['first','final'],default='first')
    args=ap.parse_args()
    data=json.loads(args.data.read_text(encoding='utf-8'))
    assert data['pairs']==[['A',0],['B',1],['C',4],['D',16],['E',64],['F',256]]
    assert data['unit']=='μM'
    args.out.mkdir(parents=True,exist_ok=False)
    pdfmetrics.registerFont(TTFont('Arial',str(args.font)))
    pdfmetrics.registerFont(TTFont('ArialBold',str(args.bold_font)))
    d=Drawing(args.out)
    d.rect('canvas',0,0,W,H,fill='#FFFFFF')
    d.text('rack-title',W/2,17,'One rack · six reference vials',11,True,'middle')
    xs=[77+60*i for i in range(6)]
    # Rack back edge and top plane; schematic geometry has no physical scale.
    d.path('rack-top',[('M',43,99),('L',402,99),('L',410,110),('L',51,110),('Z',)],'#E2E9ED',OUTLINE)
    for (id,value),x in zip(data['pairs'],xs):
        d.ellipse('slot-'+id,x,108,19,4.5,'#ADBDC6',OUTLINE,.65,
                  f'data-kind="slot" data-logical-id="slot-{id}"')
    for (id,value),x in zip(data['pairs'],xs):
        # Identical transparent bottle contours; equal liquid heights in all six.
        body=[('M',x-9,41),('L',x-9,47),('C',x-9,50,x-15,51,x-15,57),('L',x-15,109),('C',x-15,114,x-9,116,x,116),('C',x+9,116,x+15,114,x+15,109),('L',x+15,57),('C',x+15,51,x+9,50,x+9,47),('L',x+9,41),('Z',)]
        d.path('vial-'+id,body,'#F6FBFC',OUTLINE,.95,f'data-kind="vial" data-logical-id="{id}" data-fill-level="82"')
        d.path('liquid-'+id,[('M',x-13,82),('L',x-13,109),('C',x-13,113,x-7,114,x,114),('C',x+7,114,x+13,113,x+13,109),('L',x+13,82),('Z',)],TEAL,'none',attrs=f'data-role="equal-liquid" data-level="82"')
        d.ellipse('meniscus-'+id,x,82,13,2.9,'#DBF0ED','#89BEB7',.6)
        d.line('glass-highlight-'+id,x-10,60,x-10,103,'#FFFFFF',1.8)
        d.rect('cap-'+id,x-12,33,24,10,'#9AB6C0',OUTLINE,.8,2,attrs=f'data-kind="cap" data-logical-id="{id}"')
        d.line('cap-top-'+id,x-10,35,x+10,35,'#DDEBF0',1)
        for k in [-7,-2,3,8]:
            d.line(f'cap-rib-{id}-{k}',x+k,37,x+k,41,'#6A909E',.5)
    # Rack front occludes the seated vial bases and carries slot identities.
    d.rect('rack-front',51,110,359,21,'#D7E1E7',OUTLINE,.8)
    d.path('rack-side',[('M',43,99),('L',51,110),('L',51,131),('L',43,120),('Z',)],'#BACCD5',OUTLINE,.8)
    for (id,value),x in zip(data['pairs'],xs):
        d.text('slot-label-'+id,x,125,id,10.5,True,'middle')
    d.text('list-title',W/2,149,'Electronic reference list · shared, read-only',10.5,True,'middle')
    d.rect('reference-list',47,156,360,31,'#F2F7F8','#7E9FAA',.8,3,attrs='data-kind="electronic-list"')
    for i,((id,value),x) in enumerate(zip(data['pairs'],xs)):
        if i: d.line('list-divider-'+id,47+60*i,160,47+60*i,183,'#CBDADD',.6)
        d.text('list-id-'+id,x,167,id,9.5,True,'middle')
        d.text('list-value-'+id,x,181,f'{value} μM',10,False,'middle')
    # Undirected reference connections: no liquid flow and no run-to-run edge.
    dy = 2 * 72 / 25.4 if args.revision == 'final' else 0
    d.line('shared-stem',227,187,227,197-dy,OUTLINE,1.1,attrs='data-relation="shared-read-only"')
    d.line('shared-left',124,197-dy,227,197-dy,OUTLINE,1.1,attrs='data-relation="shared-read-only"')
    d.line('shared-right',227,197-dy,330,197-dy,OUTLINE,1.1,attrs='data-relation="shared-read-only"')
    d.line('run-1-link',124,197-dy,124,207-dy,OUTLINE,1.1,attrs='data-relation="shared-read-only"')
    d.line('run-2-link',330,197-dy,330,207-dy,OUTLINE,1.1,attrs='data-relation="shared-read-only"')
    for n,x in [(1,124),(2,330)]:
        d.rect('run-'+str(n),x-49,207-dy,98,17,'#FFFFFF',OUTLINE,.8,3,attrs=f'data-kind="analysis-run" data-logical-id="{n}"')
        d.text('run-label-'+str(n),x,219-dy,f'Analysis run {n}',10.5,False,'middle')
    d.save()
    subprocess.run([str(args.pdftoppm),'-png','-r','200','-singlefile',str(args.out/'figure.pdf'),str(args.out/'figure')],check=True,capture_output=True)
    im=Image.open(args.out/'figure.png').convert('RGB')
    ImageOps.grayscale(im).save(args.out/'figure-gray.png')
    # Machado-style full deuteranopia approximation applied in linear RGB.
    rgb=np.asarray(im,dtype=np.float64)/255
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.01182,.04294,.968881]])
    sim=np.clip(linear@matrix.T,0,1)
    srgb=np.where(sim<=.0031308,12.92*sim,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(args.out/'figure-deuteranopia.png')
    root=ET.parse(args.out/'figure.svg').getroot()
    elems=list(root.iter())
    kind=lambda k:[e for e in elems if e.get('data-kind')==k]
    assert len(kind('vial'))==len(kind('slot'))==len(kind('cap'))==6
    assert len(kind('electronic-list'))==1 and len(kind('analysis-run'))==2
    assert [e.get('data-logical-id') for e in kind('vial')]==list('ABCDEF')
    assert {e.get('data-fill-level') for e in kind('vial')}=={'82'}
    assert not root.findall('.//{http://www.w3.org/2000/svg}image')
    assert not root.findall('.//{http://www.w3.org/2000/svg}marker')
    page=PdfReader(args.out/'figure.pdf').pages[0]
    txt=page.extract_text()
    assert len(PdfReader(args.out/'figure.pdf').pages)==1
    assert abs(float(page.mediabox.width)-W)<.01 and abs(float(page.mediabox.height)-H)<.01
    for id,value in data['pairs']: assert f'{value} μM' in txt
    bounds_ok=all(0<=l['bounds'][0]<l['bounds'][2]<=W and 0<=l['bounds'][1]<l['bounds'][3]<=H for l in d.labels)
    assert bounds_ok
    audit={'technical_status':'PASS','reviewer':'model-assisted generator; no human review',
           'revision':args.revision,'size_mm':[160,80],'png_px':list(im.size),'minimum_text_pt':min(l['size_pt'] for l in d.labels),
           'counts':{'vials':6,'caps':6,'slots':6,'electronic_lists':1,'analysis_runs':2},
           'equal_fill_levels':True,'all_values_match_input':True,'all_vector':True,
           'font_paths':{'regular':str(args.font),'bold':str(args.bold_font)},
           'font_sha256':{'regular':sha(args.font),'bold':sha(args.bold_font)},
           'limitations':['Schematic geometry, not measured dimensions','No assay or spectra','SVG requires Arial or a compatible font','Automated checks do not assess all path collisions or visual quality'],
           'outputs':{p.name:sha(p) for p in args.out.iterdir() if p.is_file()}}
    (args.out/'technical-audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
    (args.out/'labels.json').write_text(json.dumps(d.labels,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'out':str(args.out),'technical_status':'PASS','counts':audit['counts']}))


if __name__=='__main__': main()
