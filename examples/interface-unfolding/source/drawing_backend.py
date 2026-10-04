from pathlib import Path
import html,json,math,subprocess
from types import SimpleNamespace
import numpy as np
from PIL import Image,ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
W,H=160*72/25.4,100*72/25.4
C={'ink':'#23343D','muted':'#52636B','line':'#CCD5D9','B':'#667580','U':'#AA6018','G':'#087F82','pale':'#E6F3F1','bg':'#F4F7F8','white':'#FFFFFF'}
def js(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8')
def configure(font,bold_font,pdftoppm):
 global a
 a=SimpleNamespace(pdftoppm=pdftoppm)
 pdfmetrics.registerFont(TTFont('Arial',font)); pdfmetrics.registerFont(TTFont('Arial-Bold',bold_font))
class Scene:
 def __init__(self,number): self.number=number; self.items=[]
 def add(self,t,**kw): self.items.append(dict(type=t,id=f'f{self.number}-{len(self.items):03d}',**kw))
 def rect(self,x,y,w,h,fill=None,stroke=None,sw=.7): self.add('rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw)
 def line(self,x1,y1,x2,y2,color=None,sw=.8,dash=None): self.add('line',x1=x1,y1=y1,x2=x2,y2=y2,color=color or C['line'],sw=sw,dash=dash)
 def text(self,x,y,s,size=10,color=None,bold=False,anchor='start'): self.add('text',x=x,y=y,text=s,size=size,color=color or C['ink'],bold=bold,anchor=anchor)
 def poly(self,points,fill,stroke=None,sw=.8): self.add('polygon',points=points,fill=fill,stroke=stroke,sw=sw)
 def circle(self,x,y,r,fill,stroke=None,sw=.8): self.add('circle',x=x,y=y,r=r,fill=fill,stroke=stroke,sw=sw)
 def arrow(self,x1,y1,x2,y2,color=None,sw=1,dash=None):
  color=color or C['G']; self.line(x1,y1,x2,y2,color,sw,dash)
  dx,dy=x2-x1,y2-y1; ll=math.hypot(dx,dy); ux,uy=dx/ll,dy/ll
  self.poly([(x2,y2),(x2-5*ux+2.4*uy,y2-5*uy-2.4*ux),(x2-5*ux-2.4*uy,y2-5*uy+2.4*ux)],color)
 def mark(self,x,y,mode):
  if mode=='B': self.circle(x,y,2.7,C['white'],C['B'],1.2)
  elif mode=='G': self.rect(x-3,y-3,6,6,C['G'],C['G'])
  else: self.poly([(x,y-3.6),(x-3.5,y+3),(x+3.5,y+3)],C['white'],C['U'],1.2)

def render(s,d):
 d.mkdir()
 js(d/'scene.json',{'width_mm':160,'height_mm':100,'viewBox':[0,0,W,H],'font':'Arial','evidence':'CONSTRUCTED DEMO','items':s.items})
 pdf=canvas.Canvas(str(d/'figure.pdf'),pagesize=(W,H),pageCompression=1)
 pdf.setTitle(f'Constructed DEMO - Figure {s.number}'); pdf.setAuthor('Codex: synthetic writing trial')
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="100mm" viewBox="0 0 {W} {H}">','<title>Constructed DEMO</title>']
 def col(v): return v if v else 'none'
 for z in s.items:
  t=z['type']; ident=z['id']; pdf.saveState()
  if t=='text':
   x,y=z['x'],z['y']; font='Arial-Bold' if z['bold'] else 'Arial'; pdf.setFont(font,z['size']); pdf.setFillColor(HexColor(z['color']))
   {'start':pdf.drawString,'middle':pdf.drawCentredString,'end':pdf.drawRightString}[z['anchor']](x,H-y,z['text'])
   svg.append(f'<text id="{ident}" x="{x}" y="{y}" font-family="Arial" font-size="{z["size"]}" font-weight="{"bold" if z["bold"] else "normal"}" fill="{z["color"]}" text-anchor="{z["anchor"]}">{html.escape(z["text"])}</text>')
  elif t=='line':
   pdf.setStrokeColor(HexColor(z['color']));pdf.setLineWidth(z['sw'])
   if z.get('dash'): pdf.setDash(z['dash'])
   pdf.line(z['x1'],H-z['y1'],z['x2'],H-z['y2'])
   dash=' stroke-dasharray="'+','.join(map(str,z['dash']))+'"' if z.get('dash') else ''
   svg.append(f'<line id="{ident}" x1="{z["x1"]}" y1="{z["y1"]}" x2="{z["x2"]}" y2="{z["y2"]}" stroke="{z["color"]}" stroke-width="{z["sw"]}"{dash}/>')
  else:
   if z.get('fill'): pdf.setFillColor(HexColor(z['fill']))
   if z.get('stroke'): pdf.setStrokeColor(HexColor(z['stroke']))
   pdf.setLineWidth(z['sw']); style=f'id="{ident}" fill="{col(z.get("fill"))}" stroke="{col(z.get("stroke"))}" stroke-width="{z["sw"]}"'
   if t=='rect':
    pdf.rect(z['x'],H-z['y']-z['h'],z['w'],z['h'],fill=bool(z['fill']),stroke=bool(z['stroke']))
    svg.append(f'<rect {style} x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}"/>')
   elif t=='circle':
    pdf.circle(z['x'],H-z['y'],z['r'],fill=bool(z['fill']),stroke=bool(z['stroke']))
    svg.append(f'<circle {style} cx="{z["x"]}" cy="{z["y"]}" r="{z["r"]}"/>')
   else:
    p=pdf.beginPath(); p.moveTo(z['points'][0][0],H-z['points'][0][1])
    for x,y in z['points'][1:]: p.lineTo(x,H-y)
    p.close(); pdf.drawPath(p,fill=bool(z['fill']),stroke=bool(z['stroke']))
    svg.append(f'<polygon {style} points="'+ ' '.join(f'{x},{y}' for x,y in z['points'])+'"/>')
  pdf.restoreState()
 svg.append('</svg>'); (d/'figure.svg').write_text('\n'.join(svg),encoding='utf-8'); pdf.showPage(); pdf.save()
 cmd=[a.pdftoppm,'-png','-r','200','-singlefile',str(d/'figure.pdf'),str(d/'figure')]
 r=subprocess.run(cmd,capture_output=True,text=True); (d/'render.log').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf-8'); r.check_returncode()
 im=Image.open(d/'figure.png').convert('RGB'); ImageOps.grayscale(im).save(d/'qa-gray.png')
 # A single approximate deuteranopia simulation (not universal certification).
 arr=np.array(im)/255.; mat=np.array([[.367,.861,-.228],[.280,.673,.047],[-.012,.043,.969]])
 cv=np.clip(arr@mat.T,0,1);Image.fromarray((cv*255).astype('uint8')).save(d/'qa-deuteranopia.png')
 p=PdfReader(d/'figure.pdf').pages[0]
 textitems=[z for z in s.items if z['type']=='text']
 checks={'evidence':'DEMO','pdf_mm':[float(p.mediabox.width)*25.4/72,float(p.mediabox.height)*25.4/72], 'png_pixels':list(im.size),'min_font_pt':min(z['size'] for z in textitems),'svg_text_nodes':len(textitems),'pdf_text':p.extract_text(),'all_vector':True,'visual_review':'NOT_YET_VIEWED','author_acceptance':'NOT_REQUESTED','checks_scope':'format, dimensions and text presence only'}
 js(d/'technical-checks.json',checks)
