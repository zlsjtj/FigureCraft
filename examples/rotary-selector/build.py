"""Original three-port selector DEMO, explicit flow vs rotation and same-device views."""
from pathlib import Path
import sys,argparse,json,math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from vector_export import Figure,C,sha
ap=argparse.ArgumentParser()
for k in ['font','bold-font','pdftoppm','out']:ap.add_argument('--'+k,type=Path,required=True)
a=ap.parse_args()
for n,p in [('Arial',a.font),('ArialB',a.bold_font)]:pdfmetrics.registerFont(TTFont(n,str(p)))
f=Figure(a.out,'selector','One measurement chamber with selectable inlets',height=242)
flow='#246D86';closed='#69757C';gold='#C7A467';light='#F3E9D4'
def circle(x,y,r,fill,stroke,ent,sw=1):
 f.node('circle',{'cx':x,'cy':y,'r':r,'fill':fill,'stroke':stroke,'stroke-width':sw},ent,'valve')
 f.pdf.setFillColor(HexColor(fill));f.pdf.setStrokeColor(HexColor(stroke));f.pdf.setLineWidth(sw);f.pdf.circle(x,f.H-y,r,fill=1,stroke=1)
f.text(14,21,'One chamber, selectable inlet',13,bold=True,anchor='start')
f.text(f.W-14,21,'DEMO',10.5,anchor='end',color=closed)
for state,cx in [('A',100),('B',324)]:
 cy=132
 f.text(cx-64,48,'State '+state,11.25,bold=True,anchor='start')
 # Same three external ports and same device coordinates in both views.
 for name,yy in [('A',66),('B',182)]:
  f.rect(cx-17,yy,34,24,'#F0F5F7',flow,'reservoir-'+state+name,'reservoir')
  f.text(cx,yy+17,name,11.25,bold=True,entity='reservoir-'+state+name)
 f.line(cx,90,cx,182,'vertical-port-'+state,color=closed,sw=6)
 f.line(cx,90,cx,182,'vertical-lumen-'+state,color='#FFFFFF',sw=3.8)
 f.line(cx,cy,cx+72,cy,'output-port-'+state,color=closed,sw=6)
 f.line(cx,cy,cx+72,cy,'output-lumen-'+state,color='#FFFFFF',sw=3.8)
 # A rim describes a single valve housing, not a second valve.
 circle(cx+1,cy+2,26,'#D7DEE1','#A2ADB3','housing-shadow-'+state,.5)
 circle(cx,cy,26,light,'#9C773F','housing-'+state,1)
 circle(cx,cy,22,'#F8F2E7','#C7A467','rotor-'+state,.6)
 active=-1 if state=='A' else 1
 f.line(cx,cy+active*26,cx,cy,'bore-vertical-'+state,color='#FFFFFF',sw=9)
 f.line(cx,cy,cx+26,cy,'bore-horizontal-'+state,color='#FFFFFF',sw=9)
 f.line(cx,cy+active*39,cx,cy,'selected-inlet-'+state,color=flow,sw=2)
 f.arrow(cx,cy,cx+65,cy,'liquid-flow-'+state,role='flow',color=flow,sw=2,head=5)
 f.arrow(cx,cy+active*39,cx,cy+active*10,'liquid-inlet-'+state,role='flow',color=flow,sw=2,head=4)
 yy=cy-active*24
 f.line(cx-7,yy,cx+7,yy,'closed-port-'+state,color=closed,sw=2.6)
 f.text(cx-24,yy+3,'closed',10.5,anchor='end',color=closed,entity='closed-label-'+state)
 f.rect(cx+69,cy-17,30,34,'#E5F0F2',flow,'chamber-'+state,'measurement_chamber')
 f.text(cx+84,cy+3,'M',11.25,bold=True,entity='chamber-'+state)
 f.text(cx+81,cy+37,'chamber',10.5,entity='chamber-label-'+state)
# Mechanical rotation is curved; it does not connect a fluid source to the chamber.
points=[]
for degree in range(-90,1,5):
 t=math.radians(degree);points.append((218+17*math.cos(t),115+17*math.sin(t)))
for p,q in zip(points,points[1:]):f.line(*p,*q,'rotation',role='motion',color='#8E5E72',sw=1.2)
f.arrow(*points[-2],*points[-1],'rotation-tip',role='motion',color='#8E5E72',head=4)
f.text(221,85,'90°',11.25,color='#8E5E72',entity='rotation-label')
f.text(221,145,'rotate',10.5,color='#8E5E72',entity='rotation-label')
f.text(14,228,'Switch only with flow stopped',10.5,bold=True,anchor='start')
caption=('DEMO. Two alternative states of the same three-port L-bore selector and chamber M. '
 'A is connected in the left view; B is connected after a 90-degree clockwise rotation in the right view. '
 'The other inlet is closed in each state. Blue straight arrows indicate liquid flow in a selected state; '
 'the rose curved arrow indicates valve rotation with flow stopped. Placement and dimensions are schematic, '
 'not measurements. No leakage, carryover or switching-performance result is implied.')
spec={'demo':True,'input_sha256':sha(Path(__file__).parent/'source.md'),'main_message':'Select the inlet while retaining one chamber','locked_values':{'states':['A','B'],'rotation_degrees':90,'chambers_per_device':1,'devices':1,'stop_flow_before_switching':True},'encoding':{'container':'reservoir or valve housing, with names','position':'same schematic port topology in both alternative states','distance':'none; schematic','blue_straight_arrow':'liquid flow','rose_curved_arrow':'mechanical rotation','closed_bar':'sealed inactive inlet','depth':'housing rim only'},'gain_and_loss':'Direct active and closed paths plus explicit motion; extra state view repeats the device but caption and State labels identify alternatives','scope':'model-authored transfer demonstration, not a blind independent generation test'}
f.finish(a,spec,caption,'Same valve and measurement chamber in two alternative states. Left: A flows down and right to M, B is closed. Right: B flows up and right to M, A is closed. A separate curved arrow marks 90-degree clockwise valve rotation. Switching occurs with flow stopped.')
print(a.out)
