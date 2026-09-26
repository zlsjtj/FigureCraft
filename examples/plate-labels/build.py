"""Editable layered-label DEMO; before/after differ in text paint only."""
from pathlib import Path
import argparse,json,subprocess,xml.etree.ElementTree as E
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
ap=argparse.ArgumentParser()
for k in ['font','bold-font','pdftoppm','out']:ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
for n,p in [('Arial',a.font),('ArialB',a.bold_font)]:pdfmetrics.registerFont(TTFont(n,str(p)))
NS='http://www.w3.org/2000/svg';E.register_namespace('',NS);W=160*72/25.4;H=218
caption='DEMO. Three schematic plates are ordered L1, L2 and L3. Their names and order are the only content; plate dimensions and side depth are illustrative. The paired versions preserve geometry and labels. This is a typography and painted-background check, not a material or device performance result.'
for mode in ['before','after']:
 d=a.out/mode;d.mkdir();root=E.Element('{'+NS+'}svg',width='160mm',height=f'{H*25.4/72}mm',viewBox=f'0 0 {W} {H}')
 c=canvas.Canvas(str(d/'figure.pdf'),pagesize=(W,H),invariant=1)
 def node(tag,ident,**attrs):return E.SubElement(root,'{'+NS+'}'+tag,{'id':ident,**{k:str(v) for k,v in attrs.items()}})
 def rect(ident,x,y,w,h,fill):
  node('rect',ident,x=x,y=y,width=w,height=h,fill=fill,stroke='none');c.setFillColor(HexColor(fill));c.rect(x,H-y-h,w,h,fill=1,stroke=0)
 def poly(ident,points,fill):
  node('polygon',ident,points=' '.join(f'{x},{y}' for x,y in points),fill=fill,stroke='none');p=c.beginPath();p.moveTo(points[0][0],H-points[0][1])
  for x,y in points[1:]:p.lineTo(x,H-y)
  p.close();c.setFillColor(HexColor(fill));c.drawPath(p,fill=1,stroke=0)
 def text(ident,s,x,y,size=11.25,fill='#253B44',bold=False):
  node('text',ident,x=x,y=y,fill=fill,**{'font-family':'Arial','font-size':size,'font-weight':'bold' if bold else 'normal'}).text=s
  c.setFillColor(HexColor(fill));c.setFont('ArialB' if bold else 'Arial',size);c.drawString(x,H-y,s)
 text('title','Three named layers',18,24,13,bold=True);text('demo','DEMO',391,24,10.5,fill='#5A6D75')
 specs=[('L1','Active layer',53,'#F5EBD5','#C7AB77','#9C773F','#88632F'),('L2','Spacer',104,'#253B44','#10272F','#FFFFFF','#FFFFFF'),('L3','Carrier',155,'#EDF0F2','#CBD2D6','#929CA2','#465B65')]
 for ident,label,y,fill,side,old,new in specs:
  x=78;w=302;h=32
  poly(ident+'-side',[(x+w,y),(x+w+6,y-5),(x+w+6,y+h-5),(x+w,y+h)],side)
  poly(ident+'-top',[(x,y),(x+6,y-5),(x+w+6,y-5),(x+w,y)],side)
  rect(ident+'-face',x,y,w,h,fill);text(ident,ident,26,y+22,bold=True)
  text(ident+'-name',label,x+18,y+22,fill=old if mode=='before' else new)
 text('scope','Layer order only; dimensions are schematic',18,210,10.5,fill='#5A6D75')
 E.SubElement(root,'{'+NS+'}desc').text=caption;E.ElementTree(root).write(d/'figure.svg',encoding='utf8',xml_declaration=True)
 c.save();(d/'caption.txt').write_text(caption,encoding='utf8')
 cmd=[str(a.pdftoppm),'-png','-r','300','-singlefile',str(d/'figure.pdf'),str(d/'figure')]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (d/'export.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'mode':mode,'geometry_same_by_construction':True,'visual_review':'NOT_RUN'},indent=2),encoding='utf8')
print(a.out)
