"""Rebuild the aperture DEMO with explicit paths; refuses existing output folders.
No experiments: all geometry and labels come from the companion JSON and brief.
"""
import argparse, hashlib, json, math, re, shutil, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

MM=72/25.4
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

class Drawing:
    def __init__(self,w,h): self.w=w; self.h=h; self.items=[]
    def add(self,typ,id,**kw): self.items.append(dict(type=typ,id=id,**kw))
    def text(self,id,text,x,y,size=10,bold=False,color='#243340',anchor='middle',**kw):
        self.add('text',id,text=text,x=x,y=y,size=size,bold=bold,fill=color,anchor=anchor,**kw)
    def line(self,id,x1,y1,x2,y2,color='#243340',width=.35,dash=None,**kw):
        self.add('line',id,x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,width=width,dash=dash,**kw)
    def arrow(self,id,x1,y1,x2,y2,color='#243340',width=.6,head=1.8,**kw):
        dx=x2-x1;dy=y2-y1;length=math.hypot(dx,dy);ux=dx/length;uy=dy/length
        self.line(id+'-shaft',x1,y1,x2-head*.8*ux,y2-head*.8*uy,color,width,**kw)
        self.add('polygon',id+'-head',points=[[x2,y2],[x2-head*ux-head*.5*uy,y2-head*uy+head*.5*ux],[x2-head*ux+head*.5*uy,y2-head*uy-head*.5*ux]],fill=color,stroke=color,width=.1,**kw)
    def export(self,out,font,bold,pdftoppm):
        pdfmetrics.registerFont(TTFont('TrialArial',str(font)))
        pdfmetrics.registerFont(TTFont('TrialArialBold',str(bold)))
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">', '<title>Ideal geometric aperture DEMO</title>', '<desc>Constructed schematic, not experimental measurements.</desc>']
        c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(self.w*MM,self.h*MM),invariant=1)
        c.setTitle('Ideal geometric aperture DEMO')
        def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
        for it in self.items:
            typ=it['type']; ident=it['id'];fill=it.get('fill','none');stroke=it.get('stroke','none');sw=it.get('width',0)
            meta=' '.join(f'data-{k.replace("_","-")}="{escape(str(it[k]))}"' for k in ('entity','object_part','logical_id','role','relation','state') if k in it)
            base=f'id="{ident}" {meta} fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
            c.setFillColorRGB(*rgb(fill if fill!='none' else '#FFFFFF')); c.setStrokeColorRGB(*rgb(stroke if stroke!='none' else '#FFFFFF'));c.setLineWidth(sw*MM);c.setDash([])
            if typ=='rect':
                x,y,w,h=[it[k] for k in ('x','y','w','h')]
                svg.append(f'<rect {base} x="{x}" y="{y}" width="{w}" height="{h}"/>')
                c.rect(x*MM,(self.h-y-h)*MM,w*MM,h*MM,stroke=int(stroke!='none'),fill=int(fill!='none'))
            elif typ=='circle':
                x,y,r=[it[k] for k in ('x','y','r')]
                svg.append(f'<circle {base} cx="{x}" cy="{y}" r="{r}"/>')
                c.circle(x*MM,(self.h-y)*MM,r*MM,stroke=int(stroke!='none'),fill=int(fill!='none'))
            elif typ=='polygon':
                pts=it['points'];p=c.beginPath();p.moveTo(pts[0][0]*MM,(self.h-pts[0][1])*MM)
                for x,y in pts[1:]:p.lineTo(x*MM,(self.h-y)*MM)
                p.close();c.drawPath(p,stroke=int(stroke!='none'),fill=int(fill!='none'))
                svg.append(f'<polygon {base} points="'+ ' '.join(f'{x},{y}' for x,y in pts)+'"/>')
            elif typ=='line':
                x1,y1,x2,y2=[it[k] for k in ('x1','y1','x2','y2')];dash=it.get('dash')
                da=f' stroke-dasharray="{dash}"' if dash else ''
                if dash:c.setDash([float(x)*MM for x in dash.split(',')])
                svg.append(f'<line {base} x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{da}/>')
                c.line(x1*MM,(self.h-y1)*MM,x2*MM,(self.h-y2)*MM)
            elif typ=='text':
                x,y,text,size=it['x'],it['y'],it['text'],it['size'];weight='bold' if it['bold'] else 'normal'
                svg.append(f'<text id="{ident}" {meta} x="{x}" y="{y}" fill="{fill}" font-family="Arial" font-size="{size/MM}" font-weight="{weight}" text-anchor="{it["anchor"]}">{escape(text)}</text>')
                c.setFont('TrialArialBold' if it['bold'] else 'TrialArial',size)
                {'middle':c.drawCentredString,'start':c.drawString,'end':c.drawRightString}[it['anchor']](x*MM,(self.h-y)*MM,text)
        svg.append('</svg>');(out/'figure.svg').write_text('\n'.join(svg),encoding='utf-8');c.showPage();c.save()
        cmd=[str(pdftoppm),'-r','200','-singlefile','-png',str(out/'figure.pdf'),str(out/'figure')]
        run=subprocess.run(cmd,capture_output=True,text=True,check=True)
        rgbarr=np.asarray(Image.open(out/'figure.png').convert('RGB'))/255
        linear=np.where(rgbarr<=.04045,rgbarr/12.92,((rgbarr+.055)/1.055)**2.4)
        enc=lambda a:np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)
        gray=linear@np.array([.2126,.7152,.0722]);g=np.repeat(enc(gray)[:,:,None],3,axis=2)
        # Machado et al. 2009, deuteranomaly severity 100; one condition only.
        matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
        cvd=enc(np.clip(linear@matrix.T,0,1))
        for name,arr in [('grayscale',g),('deuteranomaly100',cvd)]:Image.fromarray(np.uint8(np.round(np.clip(arr,0,1)*255))).save(out/f'figure_{name}.png')
        reader=PdfReader(out/'figure.pdf');page=reader.pages[0]
        checks={'svg_parse':ET.parse(out/'figure.svg').getroot().tag.endswith('svg'),'pdf_pages':len(reader.pages),'pdf_width_mm':float(page.mediabox.width)/MM,'pdf_height_mm':float(page.mediabox.height)/MM,'pdf_text':page.extract_text(),'svg_text_count':sum(it['type']=='text' for it in self.items),'minimum_label_pt':min(it['size'] for it in self.items if it['type']=='text'),'embedded_raster_count':len(ET.parse(out/'figure.svg').findall('.//{http://www.w3.org/2000/svg}image')),'svg_editability':'Native geometry and text nodes; SVG depends on Arial. PDF embeds font subsets. PNG is raster.','pdftoppm':{'command':['pdftoppm','-r','200','-singlefile','-png','figure.pdf','figure'],'exit_code':run.returncode},'qa_views':{'grayscale':'Linear sRGB luminance (.2126,.7152,.0722)','cvd':'Machado 2009 deuteranomaly severity 100; matrix in rebuild.py; not comprehensive certification'},'visual_review_status':'REVIEW_REQUIRED','author_acceptance':'NOT_REQUESTED'}
        write_json(out/'scene.json',self.items);write_json(out/'technical_checks.json',checks)

def scene(spec):
    d=Drawing(160,84);d.add('rect','background',x=0,y=0,w=160,h=84,fill='#FFFFFF')
    if spec['kind']=='reconstructed_baseline':
        labels=['Disks','Read diameter','Compare with','Move or stop','Record result']
        for i,l in enumerate(labels):
            x=4+i*31
            d.add('rect',f'box-{i}',x=x,y=13,w=28,h=18,fill='#F2F5F7',stroke='#657482',width=.3)
            d.text(f'box-label-{i}',l,x+14,22,9)
            if i==2:d.text('box-label-opening','opening',x+14,26,9)
            if i<4:d.arrow(f'flow-{i}',x+28.3,22,x+30.6,22,width=.3,head=1.1)
        for i,l in enumerate(['Opening width = 3','A: diameter 2; passes','B: diameter 4; blocked','Checks: 2, 2.5, 3, 4']):d.text(f'old-explanation-{i}',l,80,43+i*7,10)
        d.text('reconstruction-note','Reconstructed from the supplied description',80,79,9,color='#596774')
        return d
    u=spec['unit_mm']; wall=spec['wall_x']; cy=spec['center_y'];opening=spec['opening'];rb=spec['diameters']['B']/2*u;ra=spec['diameters']['A']/2*u
    top=cy-opening*u/2;bottom=cy+opening*u/2;xb=wall-math.sqrt(rb**2-(opening*u/2)**2);xa=spec['A_x']
    # One wall, represented by its two connected-to-exterior shoulders. No extra opening.
    d.add('rect','barrier-upper',x=wall,y=15,w=8,h=top-15,fill='#A9B6C0',stroke='#536572',width=.45,entity='barrier',object_part='primary',logical_id='wall',role='rigid_barrier')
    d.add('rect','barrier-lower',x=wall,y=bottom,w=8,h=76-bottom,fill='#A9B6C0',stroke='#536572',width=.45,entity='barrier',object_part='decoration',logical_id='wall',role='rigid_barrier')
    d.line('centerline-left',9,cy,xb-rb-1,cy,'#92A0AB',.25,'1.2,1.2',role='approach_centerline')
    d.line('centerline-right',wall+8,cy,151,cy,'#92A0AB',.25,'1.2,1.2',role='approach_centerline')
    d.arrow('B-approach',20,cy,xb-rb-2,cy,'#A64E24',.7,2.2,relation='B-approaches-right')
    d.arrow('A-through',wall+9.5,cy,xa-ra-2,cy,'#216B7A',.7,2.2,relation='A-exits-right')
    d.add('circle','disk-B',x=xb,y=cy,r=rb,fill='#F3C3A0',stroke='#A64E24',width=.65,entity='disk',object_part='primary',logical_id='B',role='disk_B',state='blocked_left')
    d.add('circle','disk-A',x=xa,y=cy,r=ra,fill='#A7D4DB',stroke='#216B7A',width=.65,entity='disk',object_part='primary',logical_id='A',role='disk_A',state='passed_right')
    # Opening dimension: extend only rightward; split vertical line around label.
    for name,yy in [('top',top),('bottom',bottom)]:d.line('opening-extension-'+name,wall+8.6,yy,110,yy,'#536572',.25)
    d.arrow('opening-dimension-top',107,cy-4,107,top,'#536572',.3,1.6)
    d.arrow('opening-dimension-bottom',107,cy+4,107,bottom,'#536572',.3,1.6)
    for it in spec['labels']:
        pos={'B':xb,'A':xa,'wall':wall+4}.get(it.get('position'),it.get('x',80))
        d.text(it['id'],it['text'],pos,it['y'],it.get('size',10),it.get('bold',False),it.get('color','#243340'),it.get('anchor','middle'),role=it.get('role','label'))
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError('Refusing existing output directory: '+str(a.out))
    a.out.mkdir(parents=True);spec=json.loads(a.input.read_text(encoding='utf-8'));d=scene(spec);d.export(a.out,a.font,a.bold_font,a.pdftoppm)
    shutil.copy2(a.input,a.out/'input.json')
    write_json(a.out/'run_manifest.json',{'entry_point':Path(__file__).name,'input_name':a.input.name,'output_name':a.out.name,'input_sha256':sha(a.input),'script_sha256':sha(__file__),'fonts':{'regular':{'name':a.font.name,'sha256':sha(a.font)},'bold':{'name':a.bold_font.name,'sha256':sha(a.bold_font)}},'source':spec.get('source'),'files':{f.name:sha(f) for f in a.out.iterdir() if f.is_file()},'scope':'Constructed DEMO; no measured data. External package label audit is separate.'})
    print(a.out)
if __name__=='__main__':main()
