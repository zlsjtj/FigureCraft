"""Editable object-based figure; one primitive list produces native SVG and vector PDF."""
from pathlib import Path
import argparse,json,html,subprocess,hashlib
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image,ImageOps
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--font',required=True);ap.add_argument('--bold-font',required=True);ap.add_argument('--pdftoppm',required=True);a=ap.parse_args()
O=Path(a.out);O.mkdir(parents=True,exist_ok=False)
W,H=160/25.4*72,96/25.4*72
pdfmetrics.registerFont(TTFont('FigureArial',a.font));pdfmetrics.registerFont(TTFont('FigureArialBold',a.bold_font))
items=[]
def add(kind,id,**kw):items.append(dict(kind=kind,id=id,**kw))
def rect(id,x,y,w,h,fill,stroke='#213547',sw=.9):add('rect',id,x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw)
def poly(id,pts,fill,stroke='#213547',sw=.9):add('polygon',id,points=pts,fill=fill,stroke=stroke,sw=sw)
def line(id,x1,y1,x2,y2,color='#526572',sw=1.1,dash=False):add('line',id,x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,sw=sw,dash=dash)
def text(id,txt,x,y,bold=False,size=10.5,color='#213547'):add('text',id,text=txt,x=x,y=y,bold=bold,size=size,fill=color)
# One passive checkerboard object, with a small side face to identify a physical board.
poly('Board-side',[(265,17),(270,12),(270,73),(265,78)],'#A0ABB3')
poly('Board-top',[(185,17),(190,12),(270,12),(265,17)],'#E3E9ED')
rect('Board',185,17,80,61,'#FFFFFF',sw=1.1)
for r in range(5):
 for c in range(7):rect(f'Board-square-{r}-{c}',190+c*10,22+r*10,10,10,'#344857' if (r+c)%2==0 else '#FFFFFF','none',0)
text('Board-label','Board',225,94,True)
# Optical observations have no arrowheads; no digital flow originates at the board.
line('observe-C1',104,117,184,58,dash=True)
line('observe-C2',346,117,271,58,dash=True)
text('observe-C1-label','observe',110,83,size=10)
text('observe-C2-label','observe',342,83,size=10)
for ident,cx,record in [('C1',96,'L1'),('C2',354,'L2')]:
 poly(ident+'-top',[(cx-38,127),(cx-32,121),(cx+44,121),(cx+38,127)],'#C4DCEB')
 poly(ident+'-side',[(cx+38,127),(cx+44,121),(cx+44,157),(cx+38,163)],'#6790AA')
 rect(ident,cx-38,127,76,36,'#DDEBF4','#355F7C',1)
 poly(ident+'-lens',[(cx-10,127),(cx-10,116),(cx-6,111),(cx+6,111),(cx+10,116),(cx+10,127)],'#A4BDCC','#355F7C')
 text(ident+'-label',ident,cx,150,True)
 text(ident+'-residual','corner residuals',cx,180,size=10)
 line(ident+'-write',cx,186,cx,211,'#287069',1.4)
 poly(ident+'-arrow',[(cx-3.5,206),(cx,213),(cx+3.5,206)],'#287069','none',0)
 text(ident+'-write-label','write',cx+27,201,size=10,color='#245F5A')
 poly(record,[(cx-36,216),(cx+24,216),(cx+36,228),(cx+36,261),(cx-36,261)],'#EBF5F1','#287069',1)
 poly(record+'-fold',[(cx+24,216),(cx+24,228),(cx+36,228)],'#BBD9D0','#287069',.7)
 text(record+'-label',record,cx,243,True)
# Emit the same geometry to both vector formats.
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="96mm" viewBox="0 0 {W} {H}">', '<title>Two cameras observe one board and write separate records</title>']
c=canvas.Canvas(str(O/'figure.pdf'),pagesize=(W,H));c.setTitle('Shared passive board, independent camera records')
for d in items:
 k=d['kind'];attrs=f'id="{d["id"]}"';stroke=d.get('stroke','none');fill=d.get('fill','none');sw=d.get('sw',0)
 c.setLineWidth(sw);c.setStrokeColor(HexColor(stroke) if stroke!='none' else HexColor('#FFFFFF'));c.setFillColor(HexColor(fill) if fill!='none' else HexColor('#FFFFFF'))
 if k=='rect':
  s.append(f'<rect {attrs} x="{d["x"]}" y="{d["y"]}" width="{d["w"]}" height="{d["h"]}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>');c.rect(d['x'],H-d['y']-d['h'],d['w'],d['h'],stroke=stroke!='none',fill=fill!='none')
 elif k=='polygon':
  points=' '.join(f'{x},{y}' for x,y in d['points']);s.append(f'<polygon {attrs} points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>');p=c.beginPath()
  for n,(x,y) in enumerate(d['points']):(p.moveTo if n==0 else p.lineTo)(x,H-y)
  p.close();c.drawPath(p,stroke=stroke!='none',fill=fill!='none')
 elif k=='line':
  dash=' stroke-dasharray="4 3"' if d['dash'] else '';s.append(f'<line {attrs} x1="{d["x1"]}" y1="{d["y1"]}" x2="{d["x2"]}" y2="{d["y2"]}" stroke="{stroke}" stroke-width="{sw}"{dash}/>');c.setDash([4,3] if d['dash'] else []);c.line(d['x1'],H-d['y1'],d['x2'],H-d['y2']);c.setDash([])
 else:
  weight='bold' if d['bold'] else 'normal';s.append(f'<text {attrs} x="{d["x"]}" y="{d["y"]}" text-anchor="middle" font-family="Arial" font-size="{d["size"]}" font-weight="{weight}" fill="{fill}">{html.escape(d["text"])}</text>');c.setFont('FigureArialBold' if d['bold'] else 'FigureArial',d['size']);c.drawCentredString(d['x'],H-d['y'],d['text'])
s.append('</svg>');(O/'figure.svg').write_text('\n'.join(s),encoding='utf-8');c.showPage();c.save()
cmd=[a.pdftoppm,'-png','-r','300','-singlefile',str(O/'figure.pdf'),str(O/'figure')];r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stderr)
im=Image.open(O/'figure.png');im.save(O/'figure.png',dpi=(300,300));ImageOps.grayscale(im).save(O/'figure-gray.png',dpi=(300,300))
x=np.asarray(im.convert('RGB'),dtype=float)/255;mat=np.array([[.367,.861,-.228],[.280,.673,.047],[-.012,.043,.969]]);sim=np.clip(x@mat.T,0,1);Image.fromarray(np.uint8(sim*255)).save(O/'figure-deuteranopia.png',dpi=(300,300))
caption='Two fixed cameras observe the same passive checkerboard Board. Dashed, undirected lines denote observation, not digital transmission. Each camera independently computes its observed corner residuals and writes them to its own record, C1 to L1 and C2 to L2. The cameras do not communicate, and the records are not merged. Positions and board pattern are schematic; no optical dimensions or performance are encoded. This is a constructed teaching diagram.'
(O/'caption.txt').write_text(caption,encoding='utf-8');(O/'alt-text.txt').write_text('A single checkerboard at the top is connected by two dashed lines without arrowheads to cameras C1 and C2. Each camera has its own downward write arrow to a separate folded-page record, L1 or L2.',encoding='utf-8')
spec={'evidence':'DEMO','size_mm':[160,96],'depth':'D1 vector 2.5D','main_message':'One common physical reference; two independent camera records.','entities':['Board','C1','C2','L1','L2'],'primary_objects':{'Board':1,'camera':2,'record':2},'relations':[{'kind':'optical-observation','endpoints':['C1','Board'],'arrow':False},{'kind':'optical-observation','endpoints':['C2','Board'],'arrow':False},{'kind':'digital-write','source':'C1','target':'L1'},{'kind':'digital-write','source':'C2','target':'L2'}],'locked_values':['One passive board','No board data output','No camera-to-camera communication','No merged record','No distances, focal lengths, angles, performance or reconstruction'],'role_colors':{'camera':'#DDEBF4','record':'#EBF5F1','board_dark':'#344857','observation':'#526572','digital_write':'#287069'},'fonts':{'regular':a.font,'bold':a.bold_font},'min_font_pt':10,'svg_editability':'Independent native shapes and text; requires Arial or equivalent font.','primitives':items}
(O/'figure_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(O/'export.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'png_size':im.size,'dpi':[300,300],'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file()}},indent=2),encoding='utf-8')
print(str(O))
