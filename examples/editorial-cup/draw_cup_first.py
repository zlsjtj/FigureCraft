"""Original, fully vector scientific DEMO. No measurements or simulation.

Run from any cwd. All paths are explicit. Fonts are external, never copied.
Python deps: reportlab, pypdf, Pillow, numpy. Raster export: pdftoppm.
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
from PIL import Image, ImageOps
import numpy as np

W, H = 160 * 72 / 25.4, 87 * 72 / 25.4
INK = '#283A42'
EDGE = '#728C95'
LEADER = '#7C8C92'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ellipse(cx, cy, rx, ry):
    k = .5522847498307936
    return [('M',cx-rx,cy),('C',cx-rx,cy-k*ry,cx-k*rx,cy-ry,cx,cy-ry),
            ('C',cx+k*rx,cy-ry,cx+rx,cy-k*ry,cx+rx,cy),
            ('C',cx+rx,cy+k*ry,cx+k*rx,cy+ry,cx,cy+ry),
            ('C',cx-k*rx,cy+ry,cx-rx,cy+k*ry,cx-rx,cy),('Z',)]

def rear(cx,cy,rx,ry,reverse=False):
    k=.5522847498307936
    if reverse:
        return [('C',cx+rx,cy-k*ry,cx+k*rx,cy-ry,cx,cy-ry),
                ('C',cx-k*rx,cy-ry,cx-rx,cy-k*ry,cx-rx,cy)]
    return [('C',cx-rx,cy-k*ry,cx-k*rx,cy-ry,cx,cy-ry),
            ('C',cx+k*rx,cy-ry,cx+rx,cy-k*ry,cx+rx,cy)]

def front(cx,cy,rx,ry,reverse=False):
    k=.5522847498307936
    if reverse:
        return [('C',cx+rx,cy+k*ry,cx+k*rx,cy+ry,cx,cy+ry),
                ('C',cx-k*rx,cy+ry,cx-rx,cy+k*ry,cx-rx,cy)]
    return [('C',cx-rx,cy+k*ry,cx-k*rx,cy+ry,cx,cy+ry),
            ('C',cx+k*rx,cy+ry,cx+rx,cy+k*ry,cx+rx,cy)]

def polygon(pts):
    return [('M',*pts[0])]+[('L',*p) for p in pts[1:]]+[('Z',)]

class Figure:
    def __init__(self, folder, font, bold):
        self.folder=folder
        pdfmetrics.registerFont(TTFont('FigureArial',str(font)))
        pdfmetrics.registerFont(TTFont('FigureArialBold',str(bold)))
        self.pdf=canvas.Canvas(str(folder/'figure.pdf'),pagesize=(W,H),pageCompression=1,invariant=1)
        self.pdf.setTitle('Cup and central post — fictional structural demonstration')
        self.pdf.setAuthor('Original vector illustration generated from input.md')
        self.svg=[]; self.defs=[]; self.labels=[]; self.shapes=[]
    def shape(self,id,cmds,fill,stroke=EDGE,width=.6,gradient=None,entity='cup'):
        p=self.pdf.beginPath()
        for a in cmds:
            op=a[0]; v=a[1:]
            if op=='M': p.moveTo(v[0],H-v[1])
            if op=='L': p.lineTo(v[0],H-v[1])
            if op=='C': p.curveTo(v[0],H-v[1],v[2],H-v[3],v[4],H-v[5])
            if op=='Z': p.close()
        self.pdf.saveState()
        if gradient:
            x1,y1,x2,y2,colors,stops=gradient
            self.pdf.clipPath(p,stroke=0,fill=0)
            self.pdf.linearGradient(x1,H-y1,x2,H-y2,[HexColor(c) for c in colors],positions=stops,extend=True)
        elif fill:
            self.pdf.setFillColor(HexColor(fill)); self.pdf.drawPath(p,fill=1,stroke=0)
        self.pdf.restoreState()
        if stroke:
            self.pdf.setStrokeColor(HexColor(stroke)); self.pdf.setLineWidth(width)
            self.pdf.setLineJoin(1); self.pdf.drawPath(p,fill=0,stroke=1)
        d=' '.join(a[0]+' '+' '.join(f'{v:.5f}' for v in a[1:]) for a in cmds)
        fillattr=fill or 'none'
        if gradient:
            x1,y1,x2,y2,colors,stops=gradient
            gid=id+'-gradient'
            self.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'+''.join(f'<stop offset="{s}" stop-color="{c}"/>' for s,c in zip(stops,colors))+'</linearGradient>')
            fillattr=f'url(#{gid})'
        self.svg.append(f'<path id="{id}" data-entity="{entity}" d="{d}" fill="{fillattr}" stroke="{stroke or "none"}" stroke-width="{width}" stroke-linejoin="round"/>')
        self.shapes.append({'id':id,'entity':entity})
    def text(self,id,text,x,y,size=10,bold=False,anchor='start'):
        name='FigureArialBold' if bold else 'FigureArial'
        tw=pdfmetrics.stringWidth(text,name,size)
        sx=x-tw if anchor=='end' else x-tw/2 if anchor=='middle' else x
        self.pdf.setFillColor(HexColor(INK));self.pdf.setFont(name,size)
        self.pdf.drawString(sx,H-y,text)
        self.svg.append(f'<text id="{id}" x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{"bold" if bold else "normal"}" text-anchor="{anchor}" fill="{INK}">{escape(text)}</text>')
        self.labels.append({'id':id,'text':text,'font_pt':size,'bounds':[sx,y-size,sx+tw,y+size*.22]})
    def leader(self,id,points):
        self.shape(id,[('M',*points[0])]+[('L',*p) for p in points[1:]],None,LEADER,.58,entity='annotation')
    def finish(self):
        self.pdf.showPage(); self.pdf.save()
        xml=f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="87mm" viewBox="0 0 {W} {H}"><title>Cup with a central post</title><desc>One fictional cup, one central cylindrical post and one support plate. In the cutaway view, the front half of the cup wall is omitted.</desc><defs>'+''.join(self.defs)+'</defs>'+''.join(self.svg)+'</svg>'
        (self.folder/'figure.svg').write_text(xml,encoding='utf-8')

def cutaway(f):
    cx=234; by=178; ty=76; fy=169; r=66; ri=55; e=.36
    # Only the support is an auxiliary object. It is not an exploded part.
    plate=[(130,135),(360,163),(323,224),(93,196)]
    f.shape('plate-front',polygon([plate[3],plate[2],(323,229),(93,201)]),'#D8DFE2','#A6B3B8',.55,entity='plate')
    f.shape('plate-right',polygon([plate[2],plate[1],(360,168),(323,229)]),'#CDD7DB','#A6B3B8',.55,entity='plate')
    f.shape('plate-top',polygon(plate),'#F1F4F5','#AFBDC2',.65,entity='plate')
    # Cup base: closed disk, with its continuous front thickness exposed.
    base=[('M',cx-r,fy)]+front(cx,fy,r,r*e)+[('L',cx+r,by)]+front(cx,by,r,r*e,True)+[('Z',)]
    f.shape('cup-base-front',base,'#B5CBD2',gradient=(cx-r,by,cx+r,by,['#B7CDD4','#D4E2E6','#A3BEC7'],[0,.43,1]))
    f.shape('cup-floor',ellipse(cx,fy,r,r*e),'#DCE9EC',gradient=(cx,fy-r*e,cx,fy+r*e,['#C1D6DD','#E6EFF1'],[0,1]))
    # Back half of the continuous cup wall. No transparent front wall is drawn.
    shell=[('M',cx-r,by),('L',cx-r,ty)]+rear(cx,ty,r,r*e)+[('L',cx+r,by)]+rear(cx,by,r,r*e,True)+[('Z',)]
    f.shape('cup-outer-back',shell,'#BAD0D7')
    inner=[('M',cx-ri,ty)]+rear(cx,ty,ri,ri*e)+[('L',cx+ri,fy)]+rear(cx,fy,ri,ri*e,True)+[('Z',)]
    f.shape('cup-inner-wall',inner,'#CEDFE4',gradient=(cx-ri,100,cx+ri,100,['#9BB9C3','#DDEAEF','#C1D7DE'],[0,.52,1]))
    rim=[('M',cx-r,ty)]+rear(cx,ty,r,r*e)+[('L',cx+ri,ty)]+rear(cx,ty,ri,ri*e,True)+[('Z',)]
    f.shape('cup-rim',rim,'#F1F6F7','#7E99A3',.65)
    f.shape('cup-cut-left',polygon([(cx-r,ty),(cx-ri,ty),(cx-ri,fy),(cx-r,fy)]),'#EDF3F4','#78949E',.65)
    f.shape('cup-cut-right',polygon([(cx+ri,ty),(cx+r,ty),(cx+r,fy),(cx+ri,fy)]),'#D6E4E8','#78949E',.65)
    # Restore the exposed front half of the same closed cup floor.
    f.shape('cup-floor-front',[('M',cx-r,fy),('L',cx+r,fy)]+front(cx,fy,r,r*e,True)+[('Z',)],'#E3ECEF',None)
    f.shape('cup-floor-front-edge',[('M',cx-r,fy)]+front(cx,fy,r,r*e),None,EDGE,.6)
    # One upright post joins the floor; its top is strictly below the cup rim.
    pr=19; ptop=102
    post=[('M',cx-pr,ptop),('L',cx-pr,fy)]+front(cx,fy,pr,pr*e)+[('L',cx+pr,ptop)]+front(cx,ptop,pr,pr*e,True)+[('Z',)]
    f.shape('post-side',post,'#C88257','#9D694E',.65,gradient=(cx-pr,130,cx+pr,130,['#B97650','#E0AA79','#B16D48'],[0,.4,1]),entity='post')
    f.shape('post-top',ellipse(cx,ptop,pr,pr*e),'#F0C79B','#9D694E',.65,entity='post')
    f.text('view-label','Cutaway view',20,25,9)
    f.text('label-rim','Open rim',20,59)
    f.leader('leader-rim',[(65,55),(131,55),(210,53)])
    f.text('label-wall','Cup wall',20,110)
    f.leader('leader-wall',[(66,106),(138,106),(173,114)])
    f.text('label-base','Closed base',20,170)
    f.leader('leader-base',[(78,166),(130,166),(185,184)])
    f.text('label-post','Central post',329,99)
    f.leader('leader-post',[(325,95),(294,95),(253,109)])
    f.text('label-plate','Support plate',329,213)
    f.leader('leader-plate',[(325,209),(315,207),(301,204)])

def section(f):
    f.text('view-label','Axial section',20,25,9)
    x0,x1,y0,y1,t=164,300,58,181,11
    f.shape('plate-section',polygon([(109,181),(351,181),(351,190),(109,190)]),'#E4EAED','#95A6AD',.65,entity='plate')
    pts=[(x0,y0),(x0+t,y0),(x0+t,y1-t),(x1-t,y1-t),(x1-t,y0),(x1,y0),(x1,y1),(x0,y1)]
    f.shape('cup-section',polygon(pts),'#DCE9ED','#7A98A3',.8)
    f.shape('post-section',polygon([(213,97),(251,97),(251,170),(213,170)]),'#DFA777','#A5704F',.75,entity='post')
    f.text('label-opening','Open top',20,61)
    f.leader('leader-opening',[(67,57),(127,57),(185,58)])
    f.text('label-wall','Cup wall',20,111)
    f.leader('leader-wall',[(66,107),(140,107),(169,114)])
    f.text('label-base','Closed base',20,170)
    f.leader('leader-base',[(78,166),(132,166),(181,176)])
    f.text('label-post','Central post',329,105)
    f.leader('leader-post',[(325,101),(290,101),(251,110)])
    f.text('label-plate','Support plate',329,222)
    f.leader('leader-plate',[(325,218),(312,218),(300,186)])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--bold-font',type=Path,required=True)
    ap.add_argument('--pdftoppm',type=Path,required=True)
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--variant',choices=['cutaway','section'],default='cutaway')
    args=ap.parse_args()
    if args.out.exists(): raise SystemExit('Refusing to overwrite an existing output directory')
    args.out.mkdir(parents=True)
    loaded={'utc':datetime.now(timezone.utc).isoformat(),'script_sha256_at_load':sha(__file__),'input_sha256_at_load':sha(args.input),'font_sha256':sha(args.font),'bold_font_sha256':sha(args.bold_font),'argv':sys.argv,'variant':args.variant}
    (args.out/'load_record.json').write_text(json.dumps(loaded,indent=2),encoding='utf-8')
    f=Figure(args.out,args.font,args.bold_font)
    (cutaway if args.variant=='cutaway' else section)(f);f.finish()
    subprocess.run([str(args.pdftoppm),'-png','-r','300','-singlefile',str(args.out/'figure.pdf'),str(args.out/'figure')],check=True,capture_output=True)
    im=Image.open(args.out/'figure.png').convert('RGB')
    im.save(args.out/'figure.png',dpi=(300,300))
    ImageOps.grayscale(im).convert('RGB').save(args.out/'qa_grayscale.png',dpi=(300,300))
    # Machado et al. (2009) severity-100 deuteranopia matrix, linear RGB.
    rgb=np.asarray(im,dtype=float)/255
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    v=np.clip(linear@matrix.T,0,1)
    v=np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(v*255,0,255))).save(args.out/'qa_deuteranopia.png',dpi=(300,300))
    root=ET.parse(args.out/'figure.svg').getroot()
    pdf=PdfReader(args.out/'figure.pdf')
    text=pdf.pages[0].extract_text()
    labels_ok=all(x['text'] in text for x in f.labels)
    bounds_ok=all(0<=b['bounds'][0]<b['bounds'][2]<=W and 0<=b['bounds'][1]<b['bounds'][3]<=H for b in f.labels)
    result={'technical_status':'PASS' if labels_ok and bounds_ok and len(pdf.pages)==1 else 'FAIL','scientific_review':'PENDING_VISUAL_SELF_REVIEW','visual_review':'PENDING_VISUAL_SELF_REVIEW','author_acceptance':'NOT_REQUESTED_FROM_THIS_SUBAGENT','width_mm':160,'height_mm':87,'png_pixels':im.size,'min_label_pt':min(x['font_pt'] for x in f.labels),'pdf_text':text,'labels_in_bounds':bounds_ok,'all_labels_extract':labels_ok,'svg_image_count':len(root.findall('.//{http://www.w3.org/2000/svg}image')),'entity_ids':['cup','post','plate'],'labels':f.labels,'editable':'All surfaces are vector paths with editable SVG gradient stops; SVG text remains text. PDF includes font subsets. No raster geometry layers.','sha256':{p.name:sha(p) for p in args.out.iterdir() if p.is_file()}}
    (args.out/'technical_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['technical_status','width_mm','height_mm','png_pixels','min_label_pt','svg_image_count']}))

if __name__=='__main__': main()
