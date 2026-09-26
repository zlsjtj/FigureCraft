"""Editable primitive exporter for this constructed selector demonstration.

SVG and vector PDF use the same explicit primitive geometry. No experimental
measurements are produced. New output directories are required.
"""
from pathlib import Path
import argparse, hashlib, json, math, platform, re, subprocess, sys
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
from PIL import Image
import numpy as np

NS='http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
C={'ink':'#253B44','quiet':'#5A6D75','shared_fill':'#E3EFF3','shared_edge':'#3E7B8F',
   'shared_side':'#B9D2DC','address_fill':'#F5EBD5','address_edge':'#9C773F',
   'base':'#955D73','line':'#567580','rule':'#D7E1E5','white':'#FFFFFF'}
WIDTH=160*72/25.4
HEIGHT=194

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

class Figure:
    def __init__(self,out,name,title,width=WIDTH,height=HEIGHT):
        self.out=out;self.name=name;self.W=width;self.H=height
        out.mkdir(parents=True,exist_ok=False)
        self.root=ET.Element('{'+NS+'}svg',width=f'{width*25.4/72:.9f}mm',height=f'{height*25.4/72:.9f}mm',viewBox=f'0 0 {width} {height}')
        ET.SubElement(self.root,'{'+NS+'}title').text=title
        self.pdf=canvas.Canvas(str(out/(name+'.pdf')),pagesize=(width,height),pageCompression=0,invariant=1)
        self.pdf.setTitle(title)
        self.items=[];self.texts=[]
    def node(self,tag,attrs,entity,role,part='primary',text=None):
        ident=f'{entity}-{len(self.items)+1}'
        attrs={str(k):str(v) for k,v in attrs.items()}
        attrs.update({'id':ident,'data-entity':entity,'data-role':role,'data-object-part':part})
        e=ET.SubElement(self.root,'{'+NS+'}'+tag,attrs)
        if text is not None:e.text=text
        self.items.append({'id':ident,'type':tag,'entity':entity,'role':role,'part':part,'attributes':attrs,'text':text})
        return e
    def rect(self,x,y,w,h,fill,stroke,entity,role,sw=.75):
        self.node('rect',dict(x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,**{'stroke-width':sw}),entity,role)
        self.pdf.setFillColor(HexColor(fill));self.pdf.setStrokeColor(HexColor(stroke));self.pdf.setLineWidth(sw)
        self.pdf.rect(x,self.H-y-h,w,h,fill=1,stroke=bool(sw))
    def line(self,x1,y1,x2,y2,entity,role='reuse',color=None,sw=.9,dash=None):
        color=color or C['line'];attrs=dict(x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,**{'stroke-width':sw})
        if dash:attrs['stroke-dasharray']=' '.join(map(str,dash))
        self.node('line',attrs,entity,role)
        self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(sw);self.pdf.setDash(dash or [])
        self.pdf.line(x1,self.H-y1,x2,self.H-y2);self.pdf.setDash([])
    def polygon(self,pts,fill,entity,role,part='decoration',stroke=None,sw=.4):
        self.node('polygon',dict(points=' '.join(f'{x},{y}' for x,y in pts),fill=fill,stroke=stroke or fill,**{'stroke-width':sw}),entity,role,part)
        p=self.pdf.beginPath();p.moveTo(pts[0][0],self.H-pts[0][1])
        for x,y in pts[1:]:p.lineTo(x,self.H-y)
        p.close();self.pdf.setFillColor(HexColor(fill));self.pdf.setStrokeColor(HexColor(stroke or fill));self.pdf.setLineWidth(sw)
        self.pdf.drawPath(p,fill=1,stroke=bool(sw))
    def text(self,x,y,s,size=10.5,bold=False,anchor='middle',color=None,entity='label',role='label'):
        color=color or C['ink'];font='ArialB' if bold else 'Arial'
        self.node('text',dict(x=x,y=y,fill=color,**{'font-family':'Arial','font-size':size,'font-weight':'bold' if bold else 'normal','text-anchor':anchor}),entity,role,'label',s)
        self.pdf.setFont(font,size);self.pdf.setFillColor(HexColor(color))
        {'middle':self.pdf.drawCentredString,'start':self.pdf.drawString,'end':self.pdf.drawRightString}[anchor](x,self.H-y,s)
        w=pdfmetrics.stringWidth(s,font,size)
        left=x-w/2 if anchor=='middle' else x-w if anchor=='end' else x
        self.texts.append({'text':s,'size_pt':size,'bbox':[left,y-size*.75,left+w,y+size*.24],'entity':entity,'role':role})
    def arrow(self,x1,y1,x2,y2,entity,role='reuse',color=None,sw=.9,head=4):
        color=color or C['line'];self.line(x1,y1,x2,y2,entity,role,color,sw)
        a=math.atan2(y2-y1,x2-x1);ux,uy=math.cos(a),math.sin(a);vx,vy=-uy,ux
        self.polygon([(x2,y2),(x2-head*ux+head*.42*vx,y2-head*uy+head*.42*vy),(x2-head*ux-head*.42*vx,y2-head*uy-head*.42*vy)],color,entity,role)
    def plus(self,x,y,entity,r=9.5):
        self.node('circle',dict(cx=x,cy=y,r=r,fill='white',stroke=C['line'],**{'stroke-width':.9}),entity,'addition')
        self.pdf.setFillColor(HexColor('#FFFFFF'));self.pdf.setStrokeColor(HexColor(C['line']));self.pdf.setLineWidth(.9)
        self.pdf.circle(x,self.H-y,r,fill=1,stroke=1)
        self.text(x,y+3.5,'+',13,entity=entity,role='addition')
    def row(self,x,y,values,role,prefix,cell_w=52,cell_h=28,ellipsis=True):
        fill,edge=(C['shared_fill'],C['shared_edge']) if role=='shared_offset' else (C['address_fill'],C['address_edge'])
        for i,v in enumerate(values):
            self.rect(x+i*cell_w,y,cell_w,cell_h,fill,edge,f'{prefix}-{i}',role)
            self.text(x+(i+.5)*cell_w,y+cell_h*.68,str(v),11.25,entity=f'{prefix}-{i}',role=role)
        if ellipsis:
            self.text(x+len(values)*cell_w+19,y+cell_h*.68,'…',11.25,entity=f'{prefix}-omitted',role='omitted_entries')
    def finish(self,args,spec,caption,alt):
        ET.SubElement(self.root,'{'+NS+'}desc').text=alt
        self.pdf.showPage();self.pdf.save()
        ET.ElementTree(self.root).write(self.out/(self.name+'.svg'),encoding='utf-8',xml_declaration=True)
        spec.update({'width_mm':self.W*25.4/72,'height_mm':self.H*25.4/72,'items':self.items,'text_records':self.texts,'palette':C})
        dump(self.out/'figure_spec.json',spec)
        (self.out/'caption.txt').write_text(caption+'\n',encoding='utf-8')
        (self.out/'alt_text.txt').write_text(alt+'\n',encoding='utf-8')
        command=[str(args.pdftoppm),'-png','-r','300','-singlefile',str(self.out/(self.name+'.pdf')),str(self.out/self.name)]
        proc=subprocess.run(command,capture_output=True,text=True)
        if proc.returncode:raise RuntimeError(proc.stderr)
        with Image.open(self.out/(self.name+'.png')) as im:
            rgb=np.asarray(im.convert('RGB'),dtype=float)/255
            linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
            luma=linear@np.array([.2126,.7152,.0722])
            gray=np.where(luma<=.0031308,luma*12.92,1.055*np.maximum(luma,0)**(1/2.4)-.055)
            Image.fromarray((np.clip(gray,0,1)*255).astype('uint8')).save(self.out/'grayscale.png')
            matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
            cvd=np.clip(linear@matrix.T,0,1)
            cvd=np.where(cvd<=.0031308,cvd*12.92,1.055*np.maximum(cvd,0)**(1/2.4)-.055)
            Image.fromarray((np.clip(cvd,0,1)*255).astype('uint8')).save(self.out/'deuteranomaly100.png')
        reader=PdfReader(self.out/(self.name+'.pdf'));page=reader.pages[0]
        outside=[t for t in self.texts if t['bbox'][0]<0 or t['bbox'][1]<0 or t['bbox'][2]>self.W or t['bbox'][3]>self.H]
        overlaps=[]
        for i,a in enumerate(self.texts):
            for b in self.texts[i+1:]:
                x,y,z,w=a['bbox'];u,v,s,t=b['bbox']
                if min(z,s)>max(x,u) and min(w,t)>max(y,v):overlaps.append([a['text'],b['text']])
        receipt={'command':command,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'python':sys.executable,
            'pdf_size_mm':[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72],
            'pdf_page_count':len(reader.pages),'pdf_images':len(page.images),'pdf_text':page.extract_text(),
            'minimum_font_pt':min(t['size_pt'] for t in self.texts),'text_bbox_outside':outside,'text_bbox_overlaps':overlaps,
            'limits':'Text boxes are bounded ReportLab width/ascent estimates. Source line/shape collision and visual meaning reviewed separately.',
            'grayscale':'linear-sRGB luminance, encoded back to sRGB','cvd':'Machado 2009 deuteranomaly severity 100, linear RGB; one condition only',
            'technical_status':'FAIL' if outside or overlaps else 'PASS','visual_status':'REVIEW_REQUIRED','author_acceptance':'PENDING',
            'hashes':{p.name:sha(p) for p in self.out.iterdir() if p.is_file()}}
        dump(self.out/'export.json',receipt)
