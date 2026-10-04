"""Rebuild the post-review MosaicPair merge. No LLM generation or image synthesis.
All scientific inputs are constructed DEMO material. Paths are explicit/relative.
"""
import argparse, csv, hashlib, json, math, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

W,H=160*72/25.4,100*72/25.4
C={'ink':'#243B46','muted':'#52616B','line':'#A8B7BE','context':'#F0F3F4','context_ink':'#ADBEC6',
   'A':'#216D91','Af':'#E4F2F8','As':'#78B5D0','B':'#925739','Bf':'#FFF0DF','Bs':'#D9AE75',
   'record':'#EAF0EE','record_edge':'#405D58'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,o):Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

class Drawing:
    def __init__(self,out,variant,skeleton=False):
        self.out,self.variant,self.skeleton=out,variant,skeleton
        self.pdf=canvas.Canvas(str(out/'figure.pdf'),pagesize=(W,H),invariant=1)
        self.pdf.setTitle('MosaicPair shared placement — constructed DEMO')
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="100mm" viewBox="0 0 {W} {H}">',
        '<title>MosaicPair: one placement decision for a paired tile</title>',
        '<desc>Constructed DEMO; schematic, not to scale. Separate A and B images share the immutable translation for tile T5.</desc>']
        self.items=[];self.labels=[]
    def color(self,v):return '#FFFFFF' if self.skeleton and v not in ('none',C['ink'],C['muted']) else v
    def attrs(self,id,role,extra=None):
        attrs={'id':id,'data-role':role};attrs.update(extra or {})
        return ' '.join(f'{k}="{escape(str(v))}"' for k,v in attrs.items())
    def rect(self,id,x,y,w,h,fill='none',stroke=None,lw=.7,role='decoration',extra=None):
        stroke=stroke or C['line'];fill=self.color(fill)
        if self.skeleton and stroke!='none':stroke=C['muted']
        self.svg.append(f'<rect {self.attrs(id,role,extra)} x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{lw}"/>')
        self.pdf.setLineWidth(lw)
        if fill!='none':self.pdf.setFillColor(HexColor(fill))
        if stroke!='none':self.pdf.setStrokeColor(HexColor(stroke))
        self.pdf.rect(x,H-y-h,w,h,fill=int(fill!='none'),stroke=int(stroke!='none'))
        self.items.append({'id':id,'role':role,'bounds':[x,y,x+w,y+h],'extra':extra})
    def ellipse(self,id,x,y,w,h,fill,role='illustrative-stain'):
        fill=self.color(fill)
        self.svg.append(f'<ellipse {self.attrs(id,role)} cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}"/>')
        self.pdf.setFillColor(HexColor(fill));self.pdf.ellipse(x,H-y-h,x+w,H-y,fill=1,stroke=0)
    def line(self,id,pts,color=None,lw=1,arrow=False,role='relation',extra=None):
        color=C['muted'] if self.skeleton else color or C['ink']
        self.svg.append(f'<polyline {self.attrs(id,role,extra)} points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linejoin="round"/>')
        p=self.pdf.beginPath();p.moveTo(pts[0][0],H-pts[0][1])
        for x,y in pts[1:]:p.lineTo(x,H-y)
        self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(lw);self.pdf.drawPath(p)
        if arrow:
            x,y=pts[-1];x0,y0=pts[-2];ang=math.atan2(y-y0,x-x0)
            tri=[(x,y),(x-5*math.cos(ang)+2*math.sin(ang),y-5*math.sin(ang)-2*math.cos(ang)),(x-5*math.cos(ang)-2*math.sin(ang),y-5*math.sin(ang)+2*math.cos(ang))]
            self.svg.append(f'<polygon id="{id}-arrow" data-role="arrowhead" points="'+ ' '.join(f'{xx},{yy}' for xx,yy in tri)+f'" fill="{color}"/>')
            p=self.pdf.beginPath();p.moveTo(tri[0][0],H-tri[0][1])
            for xx,yy in tri[1:]:p.lineTo(xx,H-yy)
            p.close();self.pdf.setFillColor(HexColor(color));self.pdf.drawPath(p,fill=1,stroke=0)
        self.items.append({'id':id,'role':role,'points':pts,'directed':arrow,'extra':extra})
    def text(self,id,x,y,s,size=10.5,color=None,bold=False,anchor='start',role='label'):
        color=color or C['ink'];font='ArialBold' if bold else 'Arial'
        self.svg.append(f'<text {self.attrs(id,role)} x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="'+('bold' if bold else 'normal')+f'" text-anchor="{anchor}" fill="{color}">{escape(s)}</text>')
        self.pdf.setFont(font,size);self.pdf.setFillColor(HexColor(color))
        {'start':self.pdf.drawString,'middle':self.pdf.drawCentredString,'end':self.pdf.drawRightString}[anchor](x,H-y,s)
        w=pdfmetrics.stringWidth(s,font,size);l=x-w*{'start':0,'middle':.5,'end':1}[anchor]
        self.labels.append({'id':id,'text':s,'font_pt':size,'bounds':[l,y-size,l+w,y+2]})
    def finish(self):
        self.pdf.showPage();self.pdf.save();(self.out/'figure.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        js(self.out/'scene.json',{'items':self.items,'labels':self.labels})

def tile(d,id,x,y,s,ch,context=False,state='acquired'):
    co=C['context_ink'] if context else C[ch];fill=C['context'] if context else C[ch+'f']
    d.rect(id,x,y,s,s,fill,co,.8 if context else 1.3,'positioned-overlap' if context else 'tile-'+ch,
        {'data-logical-id':'positioned-overlap-'+ch if context else ch+'-T5','data-state':state,'data-pixel-bounds':'0,0,96,96'})
    spots=[(.25,.49,.11,.24),(.62,.28,.22,.13),(.56,.76,.23,.10)] if ch=='A' else [(.63,.52,.17,.11),(.35,.68,.10,.19)]
    for i,(a,b,w,h) in enumerate(spots):d.ellipse(id+f'-stain-{i}',x+a*s,y+b*s,w*s,h*s,C['context_ink'] if context else C[ch+'s'])
    if not context:
        fx,fy=x+s*10/96,y+s*18/96
        for axis,pts in [('x',[(fx-2.5,fy),(fx+2.5,fy)]),('y',[(fx,fy-2.5),(fx,fy+2.5)])]:
            d.line(id+'-fid-'+axis,pts,co,1.1,role='illustrative-fiducial',extra={'data-local-pixel':'10,18','data-global-pixel':'94,21' if state=='placed' else '10,18'})
        d.text(id+'-id',x+s-5,y+15,'T5',9.5,co,anchor='end')

def mosaic(d,ch,x,y,s):
    # Context is a schematic fragment only; it is not a complete acquisition grid.
    tx,ty=x+84*s/96,y+3*s/96
    tile(d,'context-'+ch,x,y,s,ch,True,'already-positioned')
    tile(d,'placed-'+ch,tx,ty,s,ch,False,'placed')
    return tx,ty

def record(d,x,y,w=123):
    d.rect('shared-record',x,y,w,37,C['record'],C['record_edge'],1.05,'single-immutable-record',{'data-record-id':'T5','data-translation-px':'84,3'})
    d.text('record-label',x+w/2,y+14,'T5 · immutable',9.5,bold=True,anchor='middle')
    d.text('record-value',x+w/2,y+29,'t = (84, 3) px',10.5,bold=True,anchor='middle')

def common(d):
    d.rect('canvas',0,0,W,H,'#FFFFFF','none')
    d.text('heading',12,17,'One placement for a tile pair',11,bold=True)
    d.text('demo',W-12,17,'DEMO',9.5,C['muted'],anchor='end')
    d.text('estimate-source',12,36,'A vs positioned overlap: phase correlation',9.5)
    d.text('gate',12,50,'A score ≥ 0.8: estimate; otherwise: stage grid',9.5)
    d.text('scale-note',W-12,277,'Schematic, not to scale',9,C['muted'],anchor='end')

def draw_vertical(d):
    common(d)
    for ch,x in [('A',75),('B',322)]:
        d.text('input-label-'+ch,x+27.5,75,ch+' tile',10.5,C[ch],True,'middle')
        tile(d,'input-'+ch,x,84,55,ch)
    record(d,165,98)
    for ch,x in [('A',12),('B',262)]:
        tx,ty=mosaic(d,ch,x+8,188,76)
        d.text('output-label-'+ch,x+8,180,'Mosaic '+ch,10.5,C[ch],True)
        sx=102.5 if ch=='A' else 349.5
        d.line('apply-'+ch,[(sx,139),(sx,ty-3)],C[ch],1.6,True,'image-resampling',{'data-from':'input-'+ch,'data-to':'placed-'+ch})
        d.text('resample-label-'+ch,sx-8 if ch=='A' else sx+8,156,'resample',9.5,C[ch],anchor='end' if ch=='A' else 'start')
        side=165 if ch=='A' else 288
        d.line('reference-'+ch,[(side,117),(151 if ch=='A' else 302,117),(151 if ch=='A' else 302,165),(sx,165)],C['record_edge'],1.1,False,'shared-reference',{'data-from':'shared-record','data-to':'apply-'+ch})
        d.text('read-'+ch,158 if ch=='A' else 295,153,'read t',9.5,C['record_edge'],anchor='start' if ch=='A' else 'end')
    d.text('same-map',W/2,221,'p → p + t[T5]',10.5,bold=True,anchor='middle')
    d.text('example-input',W/2,240,'(10, 18) →',9.5,anchor='middle')
    d.text('example-output',W/2,256,'(94, 21) px',9.5,anchor='middle')

def draw_lanes(d):
    common(d)
    for ch,y in [('A',82),('B',192)]:
        d.text('input-label-'+ch,18,y-9,ch+' tile',10.5,C[ch],True)
        tile(d,'input-'+ch,18,y,64,ch)
        mosaic(d,ch,254,y-3,75)
        d.text('output-label-'+ch,337,y-9,'Mosaic '+ch,10.5,C[ch],True,'middle')
        d.line('apply-'+ch,[(94,y+32),(242,y+32)],C[ch],1.7,True,'image-resampling',{'data-from':'input-'+ch,'data-to':'placed-'+ch})
        d.text('resample-label-'+ch,168,y+23 if ch=='A' else y+47,'resample',10,C[ch],anchor='middle')
    record(d,107,150)
    d.line('reference-A',[(168.5,150),(168.5,114)],C['record_edge'],1.1,False,'shared-reference',{'data-from':'shared-record','data-to':'apply-A'})
    d.line('reference-B',[(168.5,187),(168.5,224)],C['record_edge'],1.1,False,'shared-reference',{'data-from':'shared-record','data-to':'apply-B'})
    d.text('read-a',178,137,'read t',9.5,C['record_edge'])
    d.text('read-b',178,209,'read t',9.5,C['record_edge'])
    d.text('same-map',322,167,'Same map: p → p + t',10.5,bold=True,anchor='middle')
    d.text('example',12,277,'(10, 18) → (94, 21) px',9.5)

CAPTION='Figure 1. Shared placement of a paired tile. Constructed DEMO schematic, not to scale; stains and fiducial crosses are illustrative, not acquired images. Each 96 × 96-pixel A/B pair is acquired at one stage position after the supplied chromatic-offset correction. The existing phase-correlation library compares A with its already-positioned overlap. A score of at least 0.8 selects that estimate; otherwise the stage-grid translation is used, with no independent B registration. One immutable record keyed by tile ID T5 supplies both separately resampled mosaics. Plain links labelled read t join that record to the two resampling arrows; faint tiles show positioned mosaic context, not a complete grid. The central coordinate example applies to both outputs: t = (84, 3) pixels maps the paired local fiducial (10, 18) to (94, 21). Masks use the same record; their unknown shapes are omitted. Different stain intensities are not interchangeable feature maps. Shared placement does not remove residual B-only optical shifts or guarantee correct global placement after fallback.'
ALT='A blue A tile at upper left and an ochre B tile at upper right share tile ID T5. Downward resample arrows place them into separate mosaic fragments below. One central immutable record t=(84,3) pixels connects to each operation through a plain link labelled read t. Between the two output mosaics, p→p+t[T5] and the numerical example (10,18)→(94,21) express the mapping common to both. Faint neighboring tiles provide positioned context, and crosses are illustrative paired fiducials. The top rule uses phase correlation of A against positioned overlap, accepting its estimate at score≥0.8 and using stage-grid translation otherwise. Constructed DEMO, not to scale.'

def preview(out,pdftoppm):
    for dpi,name in [(300,'figure'),(96,'target-160x100mm')]:
        subprocess.run([str(pdftoppm),'-singlefile','-png','-r',str(dpi),str(out/'figure.pdf'),str(out/name)],check=True,capture_output=True)
    arr=np.asarray(Image.open(out/'figure.png').convert('RGB'))/255.
    lin=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    def encode(v):return np.uint8(np.rint(np.clip(np.where(v<=.0031308,v*12.92,1.055*np.maximum(v,0)**(1/2.4)-.055),0,1)*255))
    lum=lin@np.array([.2126,.7152,.0722]);gray=encode(np.repeat(lum[:,:,None],3,axis=2))
    mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    cvd=encode(np.clip(lin@mat.T,0,1))
    for name,array in [('gray',gray),('deuteranopia',cvd)]:
        img=Image.fromarray(array);img.save(out/f'figure-{name}.png',dpi=(300,300));img.resize((605,378),Image.Resampling.LANCZOS).save(out/f'target-{name}.png',dpi=(96,96))

def check(out,d,a):
    root=ET.parse(out/'figure.svg').getroot();ns={'s':'http://www.w3.org/2000/svg'}
    ids=[e.get('id') for e in root if e.get('id')];pdf=PdfReader(str(out/'figure.pdf'));p=pdf.pages[0];text=p.extract_text()
    scientific={}
    scientific['one_record']=len(root.findall("s:rect[@data-role='single-immutable-record']",ns))==1
    scientific['two_inputs_two_placed']=all(root.find(f"s:rect[@id='{state}-{ch}']",ns) is not None for state in ('input','placed') for ch in ('A','B'))
    scientific['shared_reference_no_arrows']=all(root.find(f"s:polyline[@id='reference-{ch}']",ns) is not None and root.find(f"s:polygon[@id='reference-{ch}-arrow']",ns) is None for ch in ('A','B'))
    scientific['coordinate_example']= [10+84,18+3]==[94,21]
    offsets={}
    for ch in ('A','B'):
        old=root.find(f"s:rect[@id='context-{ch}']",ns);new=root.find(f"s:rect[@id='placed-{ch}']",ns)
        unit=float(new.get('width'))/96
        offsets[ch]=[(float(new.get(k))-float(old.get(k)))/unit for k in ('x','y')]
    scientific['drawn_pair_offsets_equal_t']=all(abs(v-t)<1e-10 for xy in offsets.values() for v,t in zip(xy,[84,3]))
    scientific['offsets_px']=offsets
    facts=list(csv.DictReader((a.inputs/'results.csv').open(encoding='utf-8-sig')))
    technical={'unique_ids':len(ids)==len(set(ids)),'page_count':len(pdf.pages),'size_mm':[float(p.mediabox.width)*25.4/72,float(p.mediabox.height)*25.4/72],
      'all_text_in_pdf':all(l['text'] in text for l in d.labels),'minimum_font_pt':min(l['font_pt'] for l in d.labels),'external_images':len(root.findall('.//s:image',ns)),
      'text_outside_canvas':[l['id'] for l in d.labels if l['bounds'][0]<0 or l['bounds'][1]<0 or l['bounds'][2]>W or l['bounds'][3]>H],
      'input_results_rows':len(facts),'input_results_sha256':sha(a.inputs/'results.csv'),'source_sha256':sha(__file__),'svg_sha256':sha(out/'figure.svg')}
    ok=technical['unique_ids'] and technical['page_count']==1 and technical['all_text_in_pdf'] and not technical['text_outside_canvas'] and all(v for v in scientific.values() if isinstance(v,bool))
    js(out/'checks.json',{'technical_status':'PASS' if ok else 'FAIL','overall_status':'REVIEW_REQUIRED','technical':technical,'scientific_exact_checks':scientific,
      'limits':['No independent human or author acceptance','No physical experiment','This representative scene does not enumerate all 96 pairs','No inferred mask geometry','No publication-page integration','PDF/SVG cross-render comparison separate'],
      'rendering':'Native SVG and vector PDF; editable text and objects; no embedded raster','qa_views':{'gray':'linear-sRGB luminance','CVD':'Machado 2009 deuteranomaly severity 100 matrix; one condition only'}})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,default=Path(__file__).parent/'inputs');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True)
    p.add_argument('--variant',choices=['vertical','lanes'],required=True);p.add_argument('--skeleton',action='store_true');a=p.parse_args()
    if a.out.exists():p.error('Refusing to overwrite an existing output directory')
    a.out.mkdir(parents=True);pdfmetrics.registerFont(TTFont('Arial',str(a.font)));pdfmetrics.registerFont(TTFont('ArialBold',str(a.bold_font)))
    d=Drawing(a.out,a.variant,a.skeleton);{'vertical':draw_vertical,'lanes':draw_lanes}[a.variant](d);d.finish();preview(a.out,a.pdftoppm);check(a.out,d,a)
    (a.out/'caption.txt').write_text(CAPTION+'\n',encoding='utf-8');(a.out/'alt_text.txt').write_text(ALT+'\n',encoding='utf-8')
    js(a.out/'asset-hashes.json',{f.name:sha(f) for f in a.out.iterdir() if f.is_file()})
    print(json.dumps({'out':str(a.out),'variant':a.variant,'skeleton':a.skeleton}))
if __name__=='__main__':main()
