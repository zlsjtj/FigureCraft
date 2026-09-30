"""Original co-wound laminate DEMO. Shared mesh, editable source, hybrid output.
No field simulation. Millimetres refer only to publication size.
"""
from pathlib import Path
import argparse, base64, hashlib, io, json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

COLORS=['#549DB7','#E6C574','#D88478']; INK='#273B47'
W,H=160*72/25.4,95*72/25.4

def face(p,n,role,color,vn=None):
    d=dict(p=np.array(p,dtype=float),n=np.array(n,dtype=float),role=role,color=color)
    if vn is not None:d['vertex_normals']=np.array(vn,dtype=float)
    return d

def mesh(tail=18):
    faces=[]; pitch=1.8/(2*np.pi); nt=360; zz=[0,28]
    # Each sheet follows the same spiral; adjacent radii differ by thickness.
    th=np.linspace(0,4*np.pi,nt+1)
    for k,col in enumerate(COLORS):
        r=6+k*.6+pitch*th
        ci=np.column_stack([r*np.cos(th),r*np.sin(th)])
        co=np.column_stack([(r+.6)*np.cos(th),(r+.6)*np.sin(th)])
        # Continuous tangent at final angle. Radial thickness is defined by input.
        tangent=np.array([pitch, r[-1]])
        tangent/=np.linalg.norm(tangent)
        ci=np.vstack([ci,ci[-1]+tail*tangent]);co=np.vstack([co,co[-1]+tail*tangent])
        role='layer-'+chr(65+k)
        for a in range(len(ci)-1):
            for curve,sgn in [(ci,-1),(co,1)]:
                d=curve[a+1]-curve[a]; n=sgn*np.array([d[1],-d[0],0.]); n/=np.linalg.norm(n)
                p=[[*curve[a],0],[*curve[a+1],0],[*curve[a+1],28],[*curve[a],28]]
                vn=[]
                for idx in [a,a+1,a+1,a]:
                    j=min(idx,nt); ang=th[j]; rr=r[j]+(.6 if sgn==1 else 0)
                    tang=np.array([pitch*np.cos(ang)-rr*np.sin(ang),pitch*np.sin(ang)+rr*np.cos(ang)])
                    nn=sgn*np.array([tang[1],-tang[0],0]);nn/=np.linalg.norm(nn)
                    vn.append(nn if a<nt else n)
                faces.append(face(p,n,role,col,vn))
            for z,normal in [(0,[0,0,-1]),(28,[0,0,1])]:
                faces.append(face([[*ci[a],z],[*co[a],z],[*co[a+1],z],[*ci[a+1],z]],normal,role,col))
        for j,n in [(0,[0,-1,0]),(-1,[0,1,0])]:
            faces.append(face([[*ci[j],0],[*co[j],0],[*co[j],28],[*ci[j],28]],n,role,col))
    # Hollow support. The hole is never capped with a decorative disk.
    th=np.linspace(0,2*np.pi,181)
    for a,b in zip(th,th[1:]):
        for radius,sgn in [(5.8,1),(4.4,-1)]:
            n=sgn*np.array([math.cos((a+b)/2),math.sin((a+b)/2),0])
            p=[[radius*math.cos(q),radius*math.sin(q),z] for q,z in [(a,-1),(b,-1),(b,29),(a,29)]]
            vn=[sgn*np.array([math.cos(q),math.sin(q),0]) for q in [a,b,b,a]]
            faces.append(face(p,n,'support','#BDCAD1',vn))
        for z,normal in [(-1,[0,0,-1]),(29,[0,0,1])]:
            p=[[r*math.cos(q),r*math.sin(q),z] for r,q in [(4.4,a),(5.8,a),(5.8,b),(4.4,b)]]
            faces.append(face(p,normal,'support','#D0DADE'))
    return faces

class Drawing:
    def __init__(self,out,font,bold):
        self.out=out;self.svg=[];self.labels=[];self.views=[]
        pdfmetrics.registerFont(TTFont('Label',str(font)));pdfmetrics.registerFont(TTFont('LabelBold',str(bold)))
        self.c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(W,H),invariant=1)
        self.c.setTitle('Co-wound laminate | Original structural DEMO')
    def text(self,text,x,y,size=10,bold=False,color=INK):
        name='LabelBold' if bold else 'Label';self.c.setFillColor(HexColor(color));self.c.setFont(name,size);self.c.drawString(x,H-y,text)
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}">{escape(text)}</text>')
        self.labels.append(dict(text=text,size_pt=size,bounds=[x,y-size,x+pdfmetrics.stringWidth(text,name,size),y+2]))
    def line(self,pts,color='#7A8B94',width=.6,dash=False):
        self.c.saveState();self.c.setStrokeColor(HexColor(color));self.c.setLineWidth(width)
        if dash:self.c.setDash(2,2)
        p=self.c.beginPath();p.moveTo(pts[0][0],H-pts[0][1])
        for x,y in pts[1:]:p.lineTo(x,H-y)
        self.c.drawPath(p);self.c.restoreState()
        d='M '+' L '.join(f'{x},{y}' for x,y in pts)
        self.svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="2 2"' if dash else '')+'/>')
    def view(self,faces,view,box,name,px=32):
        v=np.array(view,dtype=float);v/=np.linalg.norm(v)
        r=np.cross([0,0,1],v);r/=np.linalg.norm(r);u=np.cross(v,r)
        im,mask,lo,hi,record=render(faces,r,u,v,px_per_unit=px,light=(-.3,-.55,1),ambient=.55)
        x,y,bw,bh=box;scale=min(bw/(hi[0]-lo[0]),bh/(hi[1]-lo[1]));wh=(hi-lo)*scale
        x+=(bw-wh[0])/2;y+=(bh-wh[1])/2
        im.save(self.out/(name+'.png'));mask.save(self.out/(name+'-roles.png'))
        self.c.drawImage(ImageReader(im),x,H-y-wh[1],width=wh[0],height=wh[1],mask='auto')
        data=io.BytesIO();im.save(data,format='PNG')
        self.svg.append(f'<image id="{name}" x="{x}" y="{y}" width="{wh[0]}" height="{wh[1]}" href="data:image/png;base64,{base64.b64encode(data.getvalue()).decode()}"/>')
        def project(p):
            p=np.array(p);return np.array([x,y])+(np.array([p@r,-p@u])-lo)*scale
        record.update(name=name,publication_box_pt=[x,y,*wh],dpi=im.width/(wh[0]/72),camera=dict(right=r.tolist(),up=u.tolist(),view=v.tolist()))
        self.views.append(record);return project
    def finish(self):
        self.c.showPage();self.c.save()
        (self.out/'figure.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="95mm" viewBox="0 0 {W} {H}"><title>Co-wound laminate</title><desc>Three layers and one hollow support. A single static geometry; inset is a repeated view, not new material. Hybrid raster surface and editable vector annotations.</desc>'+''.join(self.svg)+'</svg>',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--skill',type=Path,required=True)
    ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True)
    ap.add_argument('--variant',choices=['continuous','section'],default='continuous');a=ap.parse_args()
    if a.out.exists():raise SystemExit('Use a new output directory')
    a.out.mkdir(parents=True);sys.path.insert(0,str(a.skill/'scripts'));global render;from surface_renderer import render
    f=Drawing(a.out,a.font,a.bold_font);faces=mesh();f.text('Three layers, one continuous winding',14,20,11,True)
    if a.variant=='continuous':
        p=f.view(faces,(.80,.60,.75),(32,35,304,220),'assembly')
        f.text('Hollow support',14,43,10);f.line([(89,40),p([0,0,29])])
        # A zoom uses the same final tail geometry, cropped in world coordinates.
        local=[]
        for face_ in faces:
            if face_['role'].startswith('layer') and np.min(face_['p'][:,1])>=-1e-7 and np.max(face_['p'][:,1])>17:
                local.append(face_)
        q=f.view(local,(1,.5,.6),(343,93,87,118),'tail-detail',40)
        f.text('Same tail',346,72,10,True)
        for k in range(3):
            x=6+k*.6+1.8*2+.3
            tangent=np.array([1.8/(2*np.pi),6+k*.6+1.8*2]);tangent/=np.linalg.norm(tangent)
            pt=[x+18*tangent[0],18*tangent[1],28]
            f.text(chr(65+k),389+16*(k-1),86,10,True,color=COLORS[k]);f.line([(392+16*(k-1),89),q(pt)],COLORS[k],.65)
        f.line([p([10.5,18,28]),(331,79),(340,79)],dash=True)
        f.text('A / B / C stay together',293,243,10)
    else:
        p=f.view(faces,(.80,.60,.75),(16,45,224,188),'assembly')
        # Direct transverse section at z=28, viewed along the axis.
        f.text('a  Complete winding',14,42,10,True)
        f.text('b  Layer order at the end face',244,42,10,True)
        cx,cy=325,140;s=6.0
        # Vector face boundaries preserve actual spiral pitch; no exploded layers.
        for k,col in enumerate(COLORS):
            pts=[]
            for th in np.linspace(0,4*np.pi,500):
                rad=6+k*.6+.3+1.8*th/(2*np.pi);pts.append((cx+s*rad*np.cos(th),cy-s*rad*np.sin(th)))
            tang=np.array([1.8/(2*np.pi),6+k*.6+3.6]);tang/=np.linalg.norm(tang)
            pts.append((pts[-1][0]+s*18*tang[0],pts[-1][1]-s*18*tang[1]));f.line(pts,col,.6*s)
        for k in range(3):f.text(chr(65+k),385+18*(k-1),236,10,True,color=COLORS[k])
        f.text('Hollow support',22,243,10);f.line([(100,240),p([0,0,29])])
    f.finish();subprocess.run([str(a.pdftoppm),'-png','-singlefile','-r','180',str(a.out/'figure.pdf'),str(a.out/'figure')],check=True,capture_output=True)
    im=Image.open(a.out/'figure.png').convert('RGB');ImageOps.grayscale(im).save(a.out/'grayscale.png')
    arr=np.asarray(im,dtype=float)/255;mat=np.array([[.625,.375,0],[.7,.3,0],[0,.3,.7]])
    Image.fromarray(np.uint8(np.clip(arr@mat.T,0,1)*255)).save(a.out/'deuteranopia-approx.png')
    record={'variant':a.variant,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'surface_sha256':hashlib.sha256((a.skill/'scripts/surface_renderer.py').read_bytes()).hexdigest(),'canvas_mm':[160,95],'labels':f.labels,'views':f.views,'objects':{'actual':['layer-A','layer-B','layer-C','support'],'repeat_view':'same tail, not extra layers'},'limits':['original structural DEMO; no measured properties','hybrid surface raster and vector labels','approximate color-vision preview, not comprehensive accessibility test']}
    (a.out/'record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
if __name__=='__main__':main()
