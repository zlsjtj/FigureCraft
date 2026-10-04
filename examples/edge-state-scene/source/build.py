"""Two composition hypotheses and a merged revision, using frozen DEMO notes.
Requires reportlab, pypdf, Pillow, numpy and Poppler. See ../README.md.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess
import drawing_backend as d

P=argparse.ArgumentParser()
P.add_argument('--out', type=Path, required=True)
P.add_argument('--font',required=True)
P.add_argument('--bold-font',required=True)
P.add_argument('--pdftoppm',required=True)
A=P.parse_args()
if A.out.exists(): raise SystemExit('Output already exists; choose a new directory.')
A.out.mkdir(parents=True)
d.configure(A.font,A.bold_font,A.pdftoppm)
C=d.C
C.update(ink='#243841', muted='#61727A', line='#CFDADE', G='#087F82', pale='#E8F4F2', bg='#F4F7F8', U='#A9672E')

def text(s,x,y,v,z=10,b=False,color=None,anchor='start'):
    s.text(x,y,v,z,color,b,anchor)

def grid(s,x,y,w,h,edge='left'):
    s.rect(x,y,w,h,C['bg'],C['line'],.65)
    for j in range(1,4): s.line(x+j*w/4,y,x+j*w/4,y+h,C['line'],.55)
    for j in range(1,4): s.line(x,y+j*h/4,x+w,y+j*h/4,C['line'],.55)
    ex=x if edge=='left' else x+w-w/4
    s.rect(ex,y,w/4,h,C['pale'],C['G'],1)
    for j in range(1,4):s.line(ex,y+j*h/4,ex+w/4,y+j*h/4,C['G'],.55)

def strip(s,x,y,w,h):
    s.rect(x,y,w,h,C['pale'],C['G'],.95)
    for j in range(1,4):s.line(x,y+j*h/4,x+w,y+j*h/4,C['G'],.55)

def slot(s,x,y,w,ready=True):
    s.rect(x,y,w,35,C['pale'] if ready else C['white'],C['G'] if ready else C['muted'],1 if ready else .75)
    if ready:
        strip(s,x+5,y+5,9,25)
        text(s,x+22,y+22,'(e, 17) READY',10,True,'#096F72')
    else:text(s,x+w/2,y+22,'free slot',10,False,None,'middle')

def path(s,pts,color=None,dash=None):
    color=color or C['G']
    for a,b in zip(pts[:-2],pts[1:-1]):s.line(*a,*b,color,.9,dash)
    s.arrow(*pts[-2],*pts[-1],color,.9,dash)

def topology(s,x,y):
    for name,dx,dy in [('W0',0,0),('W1',27,0),('W2',0,22),('W3',27,22)]:
        s.rect(x+dx,y+dy,22,16,C['pale'] if name=='W0' else C['bg'],C['line'],.6)
        text(s,x+dx+11,y+dy+11,name,8.5,name=='W0',None,'middle')
    s.line(x+22,y+8,x+27,y+8,C['G'],1.2)
    s.line(x+22,y+30,x+27,y+30,C['muted'],.65)
    s.line(x+11,y+16,x+11,y+22,C['muted'],.65)
    s.line(x+38,y+16,x+38,y+22,C['muted'],.65)

def heading(s,subtitle):
    text(s,16,22,'G · '+subtitle,12,True)
    text(s,437,22,'DEMO',8.5,False,C['muted'],'end')

def reject(s,x,y):
    s.line(x,y-7,x+6,y,C['U'],1.2);s.line(x,y,x+6,y-7,C['U'],1.2)
    text(s,x+12,y,'(e, 16): no match',9.5,False,C['U'])

def candidate_a():
    s=d.Scene('A');heading(s,'neighbouring fields')
    text(s,18,53,'W0 requires (e, 17)',10.5,True)
    text(s,321,53,'W1',10.5,True)
    grid(s,18,77,108,81,'right');strip(s,138,77,10,81)
    grid(s,321,77,112,81,'left')
    s.rect(26,99,72,32,C['white'])
    text(s,62,110,'boundary',10,True,None,'middle');text(s,62,124,'update 17',10,True,None,'middle')
    s.rect(353,99,74,32,C['white']);text(s,390,110,'interior work',9.5,False,None,'middle');text(s,390,124,'step 18',10,True,None,'middle')
    slot(s,187,86,111);slot(s,187,143,111,False)
    text(s,242,72,'incoming slots',9.5,True,None,'middle')
    s.arrow(318,103,301,103,C['G']);s.arrow(183,103,151,103,C['G'])
    text(s,309,66,'copy 17',9,False,C['G'],'middle');text(s,165,66,'match',9,False,C['G'],'middle')
    s.arrow(141,149,121,149,C['G'])
    text(s,125,179,'ghost copy',9.5,False,None,'middle');text(s,377,179,'source edge · 17',9.5,False,None,'middle')
    path(s,[(43,161),(43,202),(175,202),(175,113),(184,113)],dash=[3,2])
    text(s,85,217,'release 17',9.5,False,C['G'])
    path(s,[(334,160),(334,191),(271,191),(271,181)],C['muted'],[3,2])
    text(s,304,207,'write 18 when ready',9.5,False,None,'middle')
    topology(s,18,235);reject(s,283,243)
    text(s,100,270,'Both slots live: W1 waits.',10,True)
    return s

def candidate_b():
    s=d.Scene('B');heading(s,'follow the copied values')
    text(s,22,57,'W1',11,True);text(s,307,57,'W0 requires (e, 17)',10.5,True)
    text(s,24,83,'source edge · 17',10)
    strip(s,53,96,19,65)
    slot(s,153,96,116);slot(s,153,150,116,False)
    text(s,211,83,'incoming slots',10,True,None,'middle')
    strip(s,317,96,13,65)
    grid(s,343,96,88,65,'left')
    s.rect(361,107,64,33,C['white']);text(s,393,119,'boundary',9.5,True,None,'middle');text(s,393,133,'update 17',9.5,True,None,'middle')
    s.arrow(77,112,149,112,C['G'],1.2);text(s,112,102,'copy 17',9.5,False,C['G'],'middle')
    s.arrow(273,112,313,112,C['G'],1.2);text(s,293,101,'match',9.5,False,C['G'],'middle')
    s.arrow(328,152,348,152,C['G'],1.1);text(s,326,178,'ghost',10,False,None,'middle')
    text(s,24,197,'preparing 18',10)
    path(s,[(63,202),(63,215),(212,215),(212,188)],C['muted'],[3,2])
    text(s,113,230,'write 18 when ready',9.5,False,C['muted'])
    path(s,[(406,164),(406,201),(281,201),(281,126),(272,126)],dash=[3,2])
    text(s,357,216,'release 17',9.5,False,C['G'],'middle')
    topology(s,22,238);reject(s,96,254);text(s,236,276,'Both slots live: W1 waits.',10,True)
    return s

def selected():
    s=d.Scene('selected')
    # One scene. W0 ownership contains its two incoming slots,
    # distinct ghost storage and boundary cells; no processor/link geometry implied.
    text(s,21,53,'W1',11,True)
    text(s,149,53,'W0 requires (e, 17)',11,True)
    s.rect(144,64,293,141,'#F9FBFB',C['line'],.75)
    text(s,98,82,'source edge',10,False,None,'end')
    grid(s,21,97,77,67,'right')
    text(s,157,82,'incoming slots',10)
    slot(s,157,95,111);slot(s,157,152,111,False)
    text(s,320,82,'ghost',10,False,None,'middle')
    strip(s,314,97,12,67)
    grid(s,339,97,86,67,'left')
    s.rect(355,108,65,32,C['white'])
    text(s,388,120,'boundary',9.5,True,None,'middle')
    text(s,388,134,'update 17',9.5,True,None,'middle')
    s.arrow(101,112,153,112,C['G'],1.2);text(s,126,103,'copy 17',9.5,False,C['G'],'middle')
    s.arrow(271,112,310,112,C['G'],1.2);text(s,291,102,'match',9.5,False,C['G'],'middle')
    s.arrow(324,151,344,151,C['G'],1.1)
    text(s,21,188,'preparing 18',10)
    path(s,[(60,192),(60,220),(217,220),(217,191)],C['muted'],[3,2])
    text(s,109,236,'write 18 when ready',9.5,False,C['muted'])
    # Release enters the occupied slot's right edge at a distinct port.
    path(s,[(397,168),(397,191),(281,191),(281,124),(271,124)],dash=[3,2])
    text(s,361,184,'release 17',9.5,False,C['G'],'middle')
    reject(s,292,229)
    # Restore the notebook's W0-left / W1-right topology. Candidate B's easy
    # left-to-right reading must not silently reverse the side of a field edge.
    for item in s.items:
        kind=item['type']
        if kind=='text':
            item['x']=d.W-item['x']
            item['anchor']={'start':'end','middle':'middle','end':'start'}[item['anchor']]
        elif kind=='rect':item['x']=d.W-item['x']-item['w']
        elif kind=='line':
            item['x1']=d.W-item['x1'];item['x2']=d.W-item['x2']
        elif kind=='polygon':item['points']=[(d.W-x,y) for x,y in item['points']]
        else:raise ValueError('Unhandled mirrored object: '+kind)
    heading(s,'edge values stay live until release')
    topology(s,21,241)
    text(s,106,272,'Both slots live: W1 waits.',10,True)
    return s

for name,fn in [('candidate-A',candidate_a),('candidate-B',candidate_b),('selected',selected)]:
    scene=fn(); dest=A.out/name; d.render(scene,dest)
    subprocess.run([A.pdftoppm,'-r','96','-png','-singlefile',str(dest/'figure.pdf'),str(dest/'figure-96dpi')],check=True)
    checks=json.loads((dest/'technical-checks.json').read_text())
    checks['rendered_at_96dpi']=True
    checks['input_sha256']=hashlib.sha256((Path(__file__).parent.parent/'input/notes.md').read_bytes()).hexdigest()
    (dest/'technical-checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(A.out.resolve())
