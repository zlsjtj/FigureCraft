"""Editable two-bed DEMO figure. Geometry is schematic, never a CAD model.

Requires reportlab, numpy, Pillow and Poppler. No network or skill runtime.
SVG and PDF share the same explicit vector primitives; every text stays text.
"""
from pathlib import Path
import argparse, json, math, hashlib, subprocess
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import numpy as np

NS='http://www.w3.org/2000/svg'; ET.register_namespace('',NS)
W,H=160*72/25.4,100*72/25.4

def transformed(hexcolor,mode):
    if hexcolor is None:return None
    rgb=np.array([int(hexcolor[i:i+2],16)/255 for i in (1,3,5)])
    lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    if mode=='gray':lin[:]=float(lin@np.array([.2126,.7152,.0722]))
    elif mode=='deuteranomaly100':
        lin=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])@lin
    lin=np.clip(lin,0,1)
    rgb=np.where(lin<=.0031308,12.92*lin,1.055*lin**(1/2.4)-.055)
    return '#'+''.join(f'{round(float(v)*255):02X}' for v in rgb)

class Draw:
    def __init__(self,out,stem,palette,mode):
        self.p={k:transformed(v,mode) for k,v in palette.items()}
        self.root=ET.Element('{'+NS+'}svg',{'width':'160mm','height':'100mm','viewBox':f'0 0 {W} {H}'})
        ET.SubElement(self.root,'{'+NS+'}title').text='Constructed DEMO: sealed removable trays and service state'
        self.c=canvas.Canvas(str(out/(stem+'.pdf')),pagesize=(W,H),invariant=1,pageCompression=1)
        self.c.setTitle('Two-bed interface and service — constructed DEMO')
        self.out=out;self.stem=stem;self.mode=mode;self.elements=[];self.labels=[];self.n=0
    def el(self,tag,atts,ident=None,entity=None,role=None):
        self.n+=1;atts={k:str(v) for k,v in atts.items()};atts['id']=ident or f'e{self.n:03d}'
        if entity:atts['data-entity']=entity
        if role:atts['data-role']=role
        self.elements.append({'tag':tag,**atts})
        return ET.SubElement(self.root,'{'+NS+'}'+tag,atts)
    def color(self,token):return self.p.get(token,token) if token else None
    def style(self,fill,stroke,sw,dash=None):
        fill=self.color(fill);stroke=self.color(stroke)
        if fill:self.c.setFillColor(HexColor(fill))
        if stroke:self.c.setStrokeColor(HexColor(stroke))
        self.c.setLineWidth(sw);self.c.setDash(dash or []);self.c.setLineJoin(1);self.c.setLineCap(0)
        return fill,stroke
    def rect(self,x,y,w,h,fill='white',stroke=None,sw=.7,ident=None,entity=None,role=None):
        f,s=self.style(fill,stroke,sw)
        self.el('rect',{'x':x,'y':y,'width':w,'height':h,'fill':f or 'none','stroke':s or 'none','stroke-width':sw},ident,entity,role)
        self.c.rect(x,H-y-h,w,h,stroke=bool(s),fill=bool(f))
    def poly(self,pts,fill=None,stroke=None,sw=.7,close=True,ident=None,entity=None,role=None,dash=None):
        f,s=self.style(fill,stroke,sw,dash)
        at={'points':' '.join(f'{x},{y}' for x,y in pts),'fill':f or 'none','stroke':s or 'none','stroke-width':sw,'stroke-linejoin':'round'}
        if dash:at['stroke-dasharray']=','.join(str(v) for v in dash)
        self.el('polygon' if close else 'polyline',at,ident,entity,role)
        p=self.c.beginPath();p.moveTo(pts[0][0],H-pts[0][1])
        for x,y in pts[1:]:p.lineTo(x,H-y)
        if close:p.close()
        self.c.drawPath(p,stroke=bool(s),fill=bool(f))
    def line(self,x1,y1,x2,y2,color='ink',sw=.7,ident=None,entity=None,role=None,dash=None):
        f,s=self.style(None,color,sw,dash)
        at={'x1':x1,'y1':y1,'x2':x2,'y2':y2,'stroke':s,'stroke-width':sw}
        if dash:at['stroke-dasharray']=','.join(str(v) for v in dash)
        self.el('line',at,ident,entity,role);self.c.line(x1,H-y1,x2,H-y2)
    def circle(self,x,y,r,fill='white',stroke='ink',sw=.8,ident=None,entity=None,role=None):
        f,s=self.style(fill,stroke,sw)
        self.el('circle',{'cx':x,'cy':y,'r':r,'fill':f or 'none','stroke':s or 'none','stroke-width':sw},ident,entity,role)
        self.c.circle(x,H-y,r,stroke=bool(s),fill=bool(f))
    def text(self,x,y,text,size=10,color='ink',bold=False,anchor='start',ident=None,entity=None,role=None):
        col=self.color(color);font='ArialBold' if bold else 'Arial';width=pdfmetrics.stringWidth(text,font,size)
        left=x if anchor=='start' else x-width/2 if anchor=='middle' else x-width
        self.c.setFillColor(HexColor(col));self.c.setFont(font,size);self.c.drawString(left,H-y,text)
        e=self.el('text',{'x':x,'y':y,'fill':col,'font-family':'Arial','font-size':size,'font-weight':'700' if bold else '400','text-anchor':anchor},ident,entity,role);e.text=text
        self.labels.append({'id':e.get('id'),'text':text,'size_pt':size,'bbox':[left,y-size*.77,left+width,y+size*.21],'owner':entity or role,'color':col})
    def arrow(self,pts,color='flow',sw=1.3,head=4.3,ident=None,entity=None,role='flow'):
        self.poly(pts,None,color,sw,False,ident,entity,role)
        x,y=pts[-1];px,py=pts[-2];dx=x-px;dy=y-py;n=math.hypot(dx,dy);ux=dx/n;uy=dy/n
        self.poly([(x,y),(x-head*ux+head*.43*uy,y-head*uy-head*.43*ux),(x-head*ux-head*.43*uy,y-head*uy+head*.43*ux)],color,None,0,True,(ident+'-head') if ident else None,entity,role)
    def save(self):
        ET.ElementTree(self.root).write(self.out/(self.stem+'.svg'),encoding='utf-8',xml_declaration=True)
        self.c.showPage();self.c.save()

def mesh(d,x,y,w,entity,depth=False):
    d.line(x,y,x+w,y,'edge',.75,entity=entity,role='mesh-bottom')
    for a in np.arange(x+3,x+w-1,6):d.line(float(a),y-1.9,float(a)+2,y+1.5,'mesh',.42,entity=entity,role='mesh-texture')

def bed(d,x,y,w,h,label,entity,fill,fontsize=10.2,full=True):
    d.rect(x+1.2,y+3,w-2.4,h-5,fill,None,0,entity=entity,role='granular-bed')
    # Sparse surface marks identify granules, without purporting to enumerate them.
    for a in np.arange(x+7,x+w-3,12):
        for b in (y+7,y+h-8):d.circle(float(a),float(b),.55,'grain',None,0,entity=entity,role='texture')
    if full:d.line(x,y,x,y+h,'edge',1,entity=entity,role='tray-side')
    d.line(x+w,y,x+w,y+h,'edge',1,entity=entity,role='tray-side')
    mesh(d,x,y+h,w,entity)
    d.text(x+8,y+h*.64,label,fontsize,bold=True,entity=entity,role='object-label')

def operating(d,x,top,w,bottom,version,compact=False):
    e=f'{version}-operation';wall=4;innerx=x+wall;right=x+w-wall
    d.rect(x,top,wall,bottom-top,'shell','edge',.65,entity=e,role='housing-section')
    d.rect(x+w-wall,top,wall,bottom-top-23,'shell','edge',.65,entity=e,role='housing-section')
    d.rect(x+w-wall,bottom-11,wall,11,'shell','edge',.65,entity=e,role='housing-section')
    d.rect(x,bottom,w,4,'shell','edge',.65,entity=e,role='housing-section')
    # One lid feed port; gasket appears only on lid/wall contact sections.
    cx=x+w*.5;port=8
    d.rect(x-2,top-5,cx-port/2-(x-2),5,'lid','edge',.6,entity=e,role='lid')
    d.rect(cx+port/2,top-5,x+w+2-cx-port/2,5,'lid','edge',.6,entity=e,role='lid')
    d.line(cx-port/2,top-13,cx-port/2,top+3,'edge',.75,entity=e)
    d.line(cx+port/2,top-13,cx+port/2,top+3,'edge',.75,entity=e)
    for sx in (x,right):d.rect(sx,top,wall,2,'seal',None,0,entity=e,role='lid-wall-seal')
    d.text(cx,top-18,'Feed',9.2,anchor='middle',entity=e)
    d.arrow([(cx,top-10),(cx,top+21)],'flow',1.1,3.8,entity=e)
    d.line(x+w,bottom-23,x+w+13,bottom-23,'edge',.65,entity=e,role='outlet')
    d.line(x+w,bottom-11,x+w+13,bottom-11,'edge',.65,entity=e,role='outlet')
    by1=top+(bottom-top)*.27;by2=top+(bottom-top)*.66;bh=(bottom-top)*.175
    bx=x+14;bw=w-28
    for yy,lab,col,name in ((by1,'A  12 g','bedA','upper'),(by2,'B  8 g','bedB','lower')):
        bed(d,bx,yy,bw,bh,lab,e+'-'+name+'-tray',col,9.3 if compact else 10.4)
        if version=='S':
            for sx,sw in ((innerx,bx-innerx),(bx+bw,right-bx-bw)):
                d.rect(sx,yy+3,sw,3,'seal',None,0,entity=e+'-'+name+'-tray',role='continuous-rim-seal-section')
                d.rect(sx,yy+6,sw,3,'ledge','edge',.4,entity=e,role='ledge-contact')
    fx=x+w*.73
    for yy in (by1,by2):d.arrow([(fx,yy-13),(fx,yy+bh+6)],'flow',1.25,4,entity=e)
    d.arrow([(fx,by2+bh+12),(fx,bottom-17),(x+w+10,bottom-17)],'flow',1.25,4,entity=e)
    if version=='R':
        rx=right-5
        d.arrow([(rx-12,top+23),(rx,top+23),(rx,bottom-17)],'bypass',1.25,4,entity=e,role='bypass-both-beds')
    return {'x':x,'right':right,'by1':by1,'by2':by2,'bx':bx,'bw':bw,'bottom':bottom,'entity':e}

def side_crop(d,x,top,w,bottom):
    e='R-wall-side-crop';wallx=x+w-4;trayright=wallx-16
    d.rect(wallx,top,4,bottom-top,'shell','edge',.65,entity=e,role='wall-section')
    for yy,lab,col in ((105,'A','bedA'),(173,'B','bedB')):
        bed(d,x,yy,trayright-x,30,lab,e+'-'+lab,col,10,False)
        # Conventional crop break at the inner edge, not a new serrated part.
        d.line(x-1,yy+8,x+3,yy+3,'white',2.3,entity=e,role='crop-break')
        d.line(x-2,yy+9,x+2,yy+4,'edge',.7,entity=e,role='crop-break')
        d.line(x+1,yy+10,x+5,yy+5,'edge',.7,entity=e,role='crop-break')
    rx=wallx-8
    d.arrow([(rx-10,top+4),(rx,top+4),(rx,bottom-5)],'bypass',1.4,4.5,entity=e,role='bypass-both-beds')
    d.text(x,top-6,'Inlet plenum',8.8,entity=e)
    d.text(x,bottom+10,'Collector',8.8,entity=e)

def empty_tray(d,x,y,w,entity,depth=6):
    # Shallow rectangular tray identification only; no fitted guide geometry.
    dep=depth;ht=5
    floor=[(x,y),(x+w,y),(x+w+dep,y-dep*.55),(x+dep,y-dep*.55)]
    d.poly(floor,'meshfill','edge',.7,True,entity=entity,role='mesh-bottom')
    for a in np.arange(x+4,x+w-2,7):d.line(float(a),y,float(a)+dep,y-dep*.55,'mesh',.4,entity=entity,role='mesh-texture')
    d.poly([(x,y),(x,y-ht),(x+dep,y-ht-dep*.55),(x+dep,y-dep*.55)],'shell','edge',.55,True,entity=entity,role='tray-side')
    d.poly([(x+w,y),(x+w,y-ht),(x+w+dep,y-ht-dep*.55),(x+w+dep,y-dep*.55)],'ledge','edge',.55,True,entity=entity,role='tray-side')
    d.line(x+dep,y-ht-dep*.55,x+w+dep,y-ht-dep*.55,'edge',.75,entity=entity,role='rear-rim')
    return (x+w+dep,y-ht-dep*.55)

def service(d,x,lid_y,w,bottom,hero=False):
    e='S-service';dep=6;bodytop=lid_y+80;seat=bodytop+21;tray_y=lid_y+43
    # Detached lid and port are the same lid, under stopped/drained conditions.
    cx=x+w/2
    d.rect(x-2,lid_y,w/2-3,4,'lid','edge',.6,entity=e,role='lifted-lid')
    d.rect(cx+3,lid_y,w/2-1,4,'lid','edge',.6,entity=e,role='lifted-lid')
    d.text(cx,lid_y+17,'Lid lifted',9,anchor='middle',entity=e)
    tab=empty_tray(d,x+9,tray_y,w-23,e+'-upper-tray',dep)
    d.text(x+6,tray_y+15,'Same upper tray · empty',8.8 if not hero else 10,entity=e+'-upper-tray')
    d.rect(x,bodytop,4,bottom-bodytop,'shell','edge',.65,entity=e,role='housing-section')
    d.rect(x+w-4,bodytop,4,bottom-bodytop,'shell','edge',.65,entity=e,role='housing-section')
    d.rect(x,bottom,w,4,'shell','edge',.65,entity=e,role='housing-section')
    for sx in (x+4,x+w-13):d.rect(sx,seat,9,3,'ledge',None,0,entity=e,role='vacant-upper-seat')
    d.text(cx,seat+24,'Empty upper seat',9.2 if not hero else 10,anchor='middle',entity=e)
    low_y=bottom-12;empty_tray(d,x+9,low_y,w-23,e+'-lower-tray',dep)
    d.text(cx,low_y-17,'Lower tray stays',9.2 if not hero else 10,anchor='middle',entity=e+'-lower-tray')
    ax=x+w*.42
    d.arrow([(ax,seat-3),(ax,tray_y+22)],'motion',1.25,4.3,entity=e+'-upper-tray',role='upward-removal')
    d.text(ax+6,(seat+tray_y+22)/2+1,'Lift',9.4,entity=e+'-upper-tray')
    # Small circular markers mean interface locations, not actual circular tabs.
    d.circle(tab[0],tab[1],2.3,'white','ink',.85,entity=e+'-upper-tray',role='tab-interface-marker')
    d.text(tab[0]-3,tab[1]-10,'Tray tab',8.5,anchor='end',entity=e+'-upper-tray')
    d.line(tab[0]-3,tab[1]-7,tab[0],tab[1]-2.5,'ink',.55,entity=e+'-upper-tray',role='label-leader')
    gx=x+w-9;gy=seat
    d.circle(gx,gy,2.3,'white','ink',.85,entity=e,role='guide-interface-marker')
    d.text(x+8,seat+11,'Guide',8.5,entity=e)
    d.line(x+35,seat+7,gx-2.3,gy,'ink',.55,entity=e,role='label-leader')

def build_scene(d,p):
    layout=p['layout'];d.rect(0,0,W,H,'white')
    if layout=='operation-focus':
        d.text(16,20,'R · side section',10.5,'bypass',True,entity='R-wall-side-crop')
        d.text(141,20,'S · in operation',11.8,'ink',True,entity='S-operation')
        d.text(321,20,'Same S · service',10.5,'ink',True,entity='S-service')
        d.text(321,36,'Feed off · drained',9.3,entity='S-service')
        side_crop(d,20,79,69,225)
        g=operating(d,142,66,135,233,'S')
        d.text(256,77,'Rim seal',9.2,entity='S-operation-upper-tray')
        d.text(256,89,'on ledge',9.2,entity='S-operation')
        d.line(265,92,268,g['by1']+6,'ink',.65,entity='S-operation',role='label-leader')
        d.text(274,254,'Outlet',9.1,entity='S-operation')
        service(d,326,55,106,233)
        d.text(20,256,'Bypasses A + B',9,'bypass',entity='R-wall-side-crop')
    elif layout=='service-focus':
        d.text(17,20,'R · open rims',10.4,'bypass',True,entity='R-operation')
        d.text(138,20,'S · sealed rims',10.4,'ink',True,entity='S-operation')
        d.text(276,20,'Same S · service',11.8,'ink',True,entity='S-service')
        d.text(276,36,'Feed off · drained',9.4,entity='S-service')
        operating(d,22,70,92,221,'R',True)
        g=operating(d,145,70,92,221,'S',True)
        d.text(151,249,'Seal on ledge',9.1,entity='S-operation')
        d.line(188,238,229,g['by2']+6,'ink',.6,entity='S-operation',role='label-leader')
        d.text(18,249,'Bypasses both beds',9,'bypass',entity='R-operation')
        service(d,283,55,143,233,True)
    else:raise ValueError(layout)
    d.text(16,274,'Schematic sections; interface markers are not shapes.',8.5,'muted',role='scope')
    d.text(W-15,274,'DEMO',8.5,'muted',anchor='end',role='evidence-status')

def main():
    a=argparse.ArgumentParser();a.add_argument('--params',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a.add_argument('--font',type=Path,required=True);a.add_argument('--bold-font',type=Path,required=True);a.add_argument('--pdftoppm',type=Path,required=True)
    args=a.parse_args()
    if args.out.exists() and any(args.out.iterdir()):raise SystemExit('Output is not empty; choose a new directory.')
    args.out.mkdir(parents=True,exist_ok=True)
    p=json.loads(args.params.read_text(encoding='utf-8'));pdfmetrics.registerFont(TTFont('Arial',str(args.font)));pdfmetrics.registerFont(TTFont('ArialBold',str(args.bold_font)))
    records={}
    for mode in ('normal','gray','deuteranomaly100'):
        stem='figure' if mode=='normal' else 'figure-'+mode
        d=Draw(args.out,stem,p['palette'],mode);build_scene(d,p);d.save()
        subprocess.run([str(args.pdftoppm),'-r','96','-singlefile','-png',str(args.out/(stem+'.pdf')),str(args.out/(stem+'-96dpi'))],check=True,capture_output=True)
        if mode=='normal':
            subprocess.run([str(args.pdftoppm),'-r','300','-singlefile','-png',str(args.out/(stem+'.pdf')),str(args.out/stem)],check=True,capture_output=True)
            records['labels']=d.labels;records['elements']=d.elements
    records.update({'evidence':'Constructed DEMO; developer self-review, not independent validation','layout':p['layout'],'size_mm':[160,100],'mode':'D0 sections plus schematic D1 empty-tray identification','font':str(args.font),'bold_font':str(args.bold_font),'cvd':'Machado 2009 deuteranomaly severity 100 linear-sRGB matrix; one simulation only','params_sha256':hashlib.sha256(args.params.read_bytes()).hexdigest()})
    records['files']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.out.iterdir() if f.is_file()}
    (args.out/'render-record.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(args.out),'layout':p['layout'],'labels':len(d.labels),'min_font_pt':min(x['size_pt'] for x in d.labels)},ensure_ascii=True))
if __name__=='__main__':main()
