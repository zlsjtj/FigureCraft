"""Fixed-source development: two layouts of one interface, not new experiments.
Run with explicit fonts and pdftoppm; all source paths resolve from this file.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, shutil
import drawing_backend as d

P=argparse.ArgumentParser()
P.add_argument('--out',type=Path,required=True)
P.add_argument('--font',required=True); P.add_argument('--bold-font',required=True)
P.add_argument('--pdftoppm',required=True)
P.add_argument('--revision',choices=['first','selected'],default='first')
A=P.parse_args()
if A.out.exists(): raise SystemExit('Choose a new output directory.')
A.out.mkdir(parents=True)
d.configure(A.font,A.bold_font,A.pdftoppm)
C=d.C
C.update(ink='#263D49',muted='#566D79',line='#C4D2DA',G='#356FA0',pale='#E7EFF7',bg='#F5F8FA',U='#A55D34')
BLUE='#356FA0'; PALE='#DCEAF4'; GOLD='#E3BD70'; PURPLE='#75688E'

def t(s,x,y,v,z=10,b=False,c=None,a='start'): s.text(x,y,v,z,c,b,a)
def path(s,pts,c=BLUE,dash=None,sw=1):
    for a,b in zip(pts[:-2],pts[1:-1]):s.line(*a,*b,c,sw,dash)
    s.arrow(*pts[-2],*pts[-1],c,sw,dash)
def cells(s,x,y,w,h,fill=PALE,stroke=BLUE,vertical=True):
    s.rect(x,y,w,h,fill,stroke,.8)
    for j in range(1,4):
        if vertical:s.line(x,y+h*j/4,x+w,y+h*j/4,stroke,.5)
        else:s.line(x+w*j/4,y,x+w*j/4,y+h,stroke,.5)
def grid(s,x,y,w,h,edge):
    s.rect(x,y,w,h,C['bg'],C['line'],.7)
    for j in range(1,4):
        s.line(x+w*j/4,y,x+w*j/4,y+h,C['line'],.5)
        s.line(x,y+h*j/4,x+w,y+h*j/4,C['line'],.5)
    ex=x if edge=='left' else x+w-w/4
    cells(s,ex,y,w/4,h,GOLD,'#9A7538')
def topology(s,x,y,scale=1):
    # No diagonal exchange; exact notebook placement, shared selected interface.
    w=27*scale; h=20*scale
    for name,xx,yy in [('W0',x,y),('W1',x+w,y),('W2',x,y+h),('W3',x+w,y+h)]:
        s.rect(xx,yy,w,h,PALE if name in ('W0','W1') else C['bg'],C['line'],.65)
        t(s,xx+w/2,yy+h/2+3,name,8.5,True if name in ('W0','W1') else False,a='middle')
    s.line(x+w,y,x+w,y+h,BLUE,2.4)
def slot(s,x,y,w,ready=True):
    s.rect(x,y,w,43,'#FFFFFF',BLUE if ready else C['line'],1 if ready else .8)
    if ready:
        t(s,x+8,y+14,'(e, 17)  READY',10,True,BLUE)
        cells(s,x+8,y+22,w-16,13,PALE,BLUE,False)
    else:t(s,x+w/2,y+26,'free slot',10,c=C['muted'],a='middle')
def header(s):
    t(s,16,22,'G · retain the copy until boundary use ends',11.5,True)
    t(s,437,22,'DEMO',8.5,c=C['muted'],a='end')
def cross(s,x,y):
    s.line(x-3,y-3,x+3,y+3,C['U'],1.2)
    s.line(x-3,y+3,x+3,y-3,C['U'],1.2)

def spatial():
    s=d.Scene('spatial');header(s)
    t(s,16,48,'Neighbour layout',10.5,True)
    topology(s,360,36)
    t(s,24,87,'W0 needs (e, 17)',10.5,True)
    t(s,366,87,'W1',10.5,True)
    s.rect(16,96,284,147,'#F7F9FA',C['line'],.75)
    grid(s,25,120,68,65,'right');cells(s,99,120,12,65,PALE,PURPLE)
    t(s,59,112,'boundary',9.5,a='middle');t(s,107,201,'ghost',9.5,a='middle')
    t(s,59,218,'update 17',10,True,a='middle')
    path(s,[(99,163),(91,163)],PURPLE)
    t(s,212,112,'incoming slots',10,a='middle')
    slot(s,153,122,134);slot(s,153,181,134,False)
    grid(s,357,120,76,65,'left');cells(s,357,120,19,65)
    t(s,395,201,'source edge · 17',9.5,a='middle')
    s.arrow(351,143,291,143,BLUE,1.1);t(s,320,131,'copy 17',9.5,c=BLUE,a='middle')
    s.arrow(149,143,114,143,BLUE,1.1);t(s,132,131,'match',9.5,c=BLUE,a='middle')
    path(s,[(59,184),(59,230),(145,230),(145,157),(153,157)],PURPLE,[3,2])
    t(s,99,242,'release 17',9.5,c=PURPLE,a='middle')
    t(s,366,223,'preparing 18',9.5,a='middle')
    path(s,[(365,228),(365,239),(305,239),(305,203),(291,203)],C['muted'],[3,2])
    t(s,305,254,'write 18 when ready',9,c=C['muted'],a='middle')
    # The rejected tag is attached to the match entrance, not a free-floating note.
    t(s,122,73,'queued (e, 16)',9,c=C['U'])
    path(s,[(139,79),(139,103),(131,103),(131,139)],C['U'],[2,2]);cross(s,131,142)
    t(s,182,91,'no match',9,c=C['U'])
    t(s,16,274,'If both slots are live, W1 waits.',10,True)
    return s

def unfolded(revised):
    s=d.Scene('unfolded');header(s)
    topology(s,17,38)
    t(s,84,50,'Selected W1 → W0 interface',10.5,True)
    t(s,84,66,'Unfolded by use; W0 detail rotated 180°',9.5,c=C['muted'])
    # A clear enclosing boundary owns slots and the consumer detail only.
    s.rect(143,90,294,143,'#F7F9FA',C['line'],.7)
    t(s,157,106,'W0 needs (e, 17)',10.5,True)
    t(s,23,106,'W1 source',10.5,True)
    t(s,23,123,'west edge · 17',9.5)
    cells(s,35,134,25,63)
    t(s,158,125,'incoming slots',9.5)
    slot(s,157,135,124);slot(s,157,185,124,False)
    s.arrow(65,153,152,153,BLUE,1.15)
    t(s,104,145,'copy 17',9.5,c=BLUE,a='middle')
    # Same values remain visible in a container; ghost has its own dashed extent.
    gx=336 if revised else 330
    cells(s,gx,135,12,63,PALE,PURPLE)
    grid(s,gx+18,135,68,63,'left')
    t(s,gx+6,124,'ghost',9.5,c=PURPLE,a='middle')
    s.rect(gx+36,151,47,32,'#FFFFFF')
    t(s,gx+58,164,'east edge' if revised else 'boundary',9,True,a='middle')
    t(s,gx+58,176,'update 17',9,True,a='middle')
    s.arrow(gx+12,183,gx+20,183,PURPLE,1.05)
    s.arrow(286,153,gx-5,153,BLUE,1.15)
    t(s,307,141,'match',9.5,c=BLUE,a='middle')
    # The queued stale tag visibly reaches and stops at the same selection check.
    tx=311 if revised else 296; ty=191 if revised else 208
    t(s,tx,ty,'(e, 16)',9,c=C['U'],a='middle')
    s.line(tx,ty-12,tx,166,C['U'],.8,[2,2]);cross(s,tx,161)
    t(s,tx if revised else tx+15,ty+12,'no match',9,c=C['U'],a='middle')
    # Short release loop into the occupied slot, separate from future writing.
    path(s,[(gx+55,199),(gx+55,240),(286,240),(286,174),(281,174)],PURPLE,[3,2],.9)
    t(s,351,252,'release 17 after use',9.5,c=PURPLE,a='middle')
    t(s,23,223,'preparing 18',9.5)
    path(s,[(60,228),(60,246),(139,246),(139,207),(152,207)],C['muted'],[3,2],.85)
    t(s,100,260,'write 18 when ready',9,c=C['muted'],a='middle')
    t(s,16,278,'If both slots are live, W1 waits.',10,True)
    return s

for name,fn in ([('candidate-spatial',spatial),('candidate-unfolded',lambda:unfolded(False))] if A.revision=='first' else [('selected',lambda:unfolded(True))]):
    scene=fn(); out=A.out/name;d.render(scene,out)
    subprocess.run([A.pdftoppm,'-r','96','-png','-singlefile',str(out/'figure.pdf'),str(out/'figure-96dpi')],check=True)
    # Correct colour-vision simulation uses linear RGB rather than compressed RGB.
    from PIL import Image
    import numpy as np
    arr=np.asarray(Image.open(out/'figure.png').convert('RGB'),dtype=float)/255
    linear=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    cv=np.clip(linear@mat.T,0,1)
    srgb=np.where(cv<=.0031308,12.92*cv,1.055*cv**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(out/'qa-deuteranopia.png')
    checks=json.loads((out/'technical-checks.json').read_text())
    checks.update(input_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/'input/notes.md').read_bytes()).hexdigest(),development=True,revision=A.revision)
    (out/'technical-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    if A.revision=='selected':
        for name in ['caption.md','alt_text.md','figure_spec.json']:
            source=Path(__file__).resolve().parents[1]/'input'/name
            if source.exists():shutil.copy2(source,out/name)
print(A.out.resolve())
