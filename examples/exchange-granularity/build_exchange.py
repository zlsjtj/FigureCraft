"""Hydrogel teaching DEMO: two fact-equivalent representations, not two experiments.

python build_exchange.py --inputs inputs --out NEW --font FONT.ttf --bold BOLD.ttf --pdftoppm EXE
Units are mm; text sizes are physical pt. SVG and PDF share the same primitives.
"""
import argparse, csv, hashlib, json, math, subprocess
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

INK='#24363F'; MUTED='#536871'; CA='#B8522C'; NA='#267D9D'; LINE='#849AA4'
FILL=['#EDF1EA','#D5DED1','#B5C6AE']; EDGE=['#849A7B','#778F6D','#6F8665']
W,H,S=160,124,72/25.4

class Drawing:
    def __init__(self,out,regular,bold):
        self.out=out;out.mkdir(parents=True,exist_ok=False)
        pdfmetrics.registerFont(TTFont('Regular',str(regular)))
        pdfmetrics.registerFont(TTFont('Bold',str(bold)))
        self.family=pdfmetrics.getFont('Regular').face.familyName.decode('utf8')
        self.c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(W*S,H*S),invariant=1)
        self.c.setTitle('Shared binding sites in one hydrogel bead — teaching DEMO')
        self.c.scale(S,S)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
                  '<title>Two-site calcium exchange and exact regional populations</title>']
        self.items=[];self.n=0
        self.rect(0,0,W,H,'#FFFFFF')
    def attrs(self,ident,meta):
        self.n+=1; ident=ident or f'element-{self.n}'
        return ' '.join(f'{k}="{escape(str(v))}"' for k,v in {'id':ident,**meta}.items())
    def style(self,fill,stroke,sw):
        def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
        if fill:self.c.setFillColorRGB(*rgb(fill))
        if stroke:self.c.setStrokeColorRGB(*rgb(stroke))
        self.c.setLineWidth(sw)
    def rect(self,x,y,w,h,fill=None,stroke=None,sw=.25,ident=None,**meta):
        self.svg.append(f'<rect {self.attrs(ident,meta)} x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
        self.style(fill,stroke,sw);self.c.rect(x,H-y-h,w,h,fill=bool(fill),stroke=bool(stroke))
    def circle(self,x,y,r,fill=None,stroke=None,sw=.25,ident=None,**meta):
        self.svg.append(f'<circle {self.attrs(ident,meta)} cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
        self.style(fill,stroke,sw);self.c.circle(x,H-y,r,fill=bool(fill),stroke=bool(stroke))
    def path(self,commands,fill=None,stroke=LINE,sw=.3,ident=None,**meta):
        p=self.c.beginPath();d=[]
        for cmd,pts in commands:
            d.append(cmd+' '+' '.join(str(v) for v in pts))
            if cmd=='M':p.moveTo(pts[0],H-pts[1])
            elif cmd=='L':p.lineTo(pts[0],H-pts[1])
            elif cmd=='C':p.curveTo(pts[0],H-pts[1],pts[2],H-pts[3],pts[4],H-pts[5])
            elif cmd=='Z':p.close()
        self.svg.append(f'<path {self.attrs(ident,meta)} d="{" ".join(d)}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}" stroke-linejoin="round"/>')
        self.style(fill,stroke,sw);self.c.drawPath(p,fill=bool(fill),stroke=bool(stroke))
    def line(self,x1,y1,x2,y2,color=LINE,sw=.3,ident=None,**meta):
        self.path([('M',[x1,y1]),('L',[x2,y2])],stroke=color,sw=sw,ident=ident,**meta)
    def arrow(self,x1,y1,x2,y2,color=INK,ident='arrow',meaning='state transition'):
        self.line(x1,y1,x2,y2,color,.48,ident=ident,**{'data-semantics':meaning})
        a=math.atan2(y2-y1,x2-x1);head=2
        pts=[x2,y2,x2-head*math.cos(a)+.85*math.sin(a),y2-head*math.sin(a)-.85*math.cos(a),x2-head*math.cos(a)-.85*math.sin(a),y2-head*math.sin(a)+.85*math.cos(a)]
        self.path([('M',pts[:2]),('L',pts[2:4]),('L',pts[4:]),('Z',[])],fill=color,stroke=None,ident=ident+'-head',**{'data-object-part':'decoration','data-owner':ident})
    def text(self,x,y,value,pt=9,bold=False,color=INK,anchor='start',ident=None,**meta):
        font='Bold' if bold else 'Regular';size=pt/S
        missing=[ch for ch in value if ord(ch) not in pdfmetrics.getFont(font).face.charToGlyph]
        assert not missing,(value,missing)
        width=pdfmetrics.stringWidth(value,font,size)
        left=x-({'start':0,'middle':width/2,'end':width}[anchor])
        assert left>=0 and left+width<=W,(value,left,width)
        assert pt>=8 and y-size>=0 and y<=H,(value,pt,y)
        self.svg.append(f'<text {self.attrs(ident,meta)} x="{x}" y="{y}" font-family="{self.family}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(value)}</text>')
        self.style(color,None,0);self.c.setFont(font,size)
        {'start':self.c.drawString,'middle':self.c.drawCentredString,'end':self.c.drawRightString}[anchor](x,H-y,value)
        self.items.append({'text':value,'font_pt':pt,'bbox_mm':[left,y-size,width,size]})
    def finish(self,pdftoppm):
        self.svg.append('</svg>');(self.out/'figure.svg').write_text('\n'.join(self.svg),encoding='utf8')
        self.c.showPage();self.c.save()
        p=subprocess.run([str(pdftoppm),'-png','-r','200','-singlefile',str(self.out/'figure.pdf'),str(self.out/'figure')],capture_output=True,text=True)
        assert p.returncode==0,p.stderr
        im=Image.open(self.out/'figure.png').convert('RGB');ImageOps.grayscale(im).save(self.out/'figure-gray.png')
        # One approximate deuteranopia projection, not all color-vision conditions.
        arr=np.asarray(im)/255; mat=np.array([[.367,.861,-.228],[.280,.673,.047],[-.012,.043,.969]])
        Image.fromarray((np.clip(arr@mat.T,0,1)*255).astype('uint8')).save(self.out/'figure-deuteranopia.png')
        page=PdfReader(self.out/'figure.pdf').pages[0]
        assert abs(float(page.mediabox.width)/S-W)<.01 and abs(float(page.mediabox.height)/S-H)<.01
        return {'width_mm':W,'height_mm':H,'min_font_pt':min(x['font_pt'] for x in self.items),'labels':self.items,'visual_review':'PENDING','scientific_review':'PENDING'}

def local_pair(d,x0,y0,scale=1):
    """Same two sites at two times: schema exemplar, not enumerated populations."""
    def xy(x,y):return x0+x*scale,y0+y*scale
    d.text(*xy(23,0),'Before',9,anchor='middle')
    d.text(*xy(108,0),'After',9,anchor='middle')
    for state,xs in [('before',[15,31]),('after',[100,116])]:
        for k,x in enumerate(xs):
            cx,cy=xy(x,20)
            d.line(cx,cy+1.9,cx,y0+26*scale,EDGE[1],.45)
            d.circle(cx,cy,2.3*scale,'#FFFFFF',EDGE[1],.4,ident=f'exemplar-{state}-S{k}',**{'data-object-part':'representative','data-same-site-key':f'S{k}','data-region':'one unspecified common region'})
            d.text(cx,cy+1,'−',9.5,anchor='middle')
        xx,yy=xy(xs[0]-7,26)
        d.path([('M',[xx,yy]),('C',[xx+8*scale,yy-1*scale,xx+22*scale,yy+1*scale,xx+30*scale,yy])],stroke=EDGE[1],sw=1.0)
    for x in [15,31]:
        xx,yy=xy(x,10)
        d.line(xx,yy+3.8*scale,xx,y0+17.7*scale,NA,.5)
        d.circle(xx,yy,4.3*scale,'#E7F2F6',NA,.5)
        d.text(xx,yy+1.3,'Na⁺',9.5,color=NA,anchor='middle')
    xx,yy=xy(108,9)
    for x in [100,116]:d.line(xx,yy+4.5*scale,x0+x*scale,y0+17.7*scale,CA,.65)
    d.circle(xx,yy,5.4*scale,'#FAEBE2',CA,.55)
    d.text(xx,yy+1.3,'Ca²⁺',10,color=CA,anchor='middle')
    d.arrow(*xy(50,14),*xy(81,14),ident='pair-state-change')
    d.text(*xy(65.5,8),'Ca²⁺ in',9,color=CA,anchor='middle')
    d.text(*xy(65.5,22),'2 Na⁺ out',9,color=NA,anchor='middle')

def bead(d,cx,cy,r):
    # Concentric boundaries are the provided radii; no area-to-capacity mapping.
    for name,ratio,fill,edge in zip(['shell','middle','core'],[1,.8,.45],FILL,EDGE):
        d.circle(cx,cy,r*ratio,fill,edge,.4,ident=f'bead-{name}',**{'data-object-part':'region-of-single-bead','data-outer-radius-fraction':ratio})
    # One illustrative connected pore; no direction, diameter or diffusion claim.
    commands=[('M',[cx+.15*r,cy+.18*r]),('C',[cx+.6*r,cy+.32*r,cx+.6*r,cy-.05*r,cx+1.04*r,cy+.04*r])]
    d.path(commands,stroke='#FFFFFF',sw=1.8,ident='pore-open')
    d.path(commands,stroke='#8BABBA',sw=.34,ident='pore-water',**{'data-object-part':'schematic-pore'})

def exchange_led(d,rows):
    d.text(6,8,'One Ca²⁺ replaces two bound Na⁺',12,True)
    d.text(154,15,'Teaching DEMO',8.5,color=MUTED,anchor='end')
    local_pair(d,17,21)
    d.text(80,58,'Same two sites · one region',9,color=MUTED,anchor='middle')
    d.line(6,63,154,63,'#D6E0E4',.3)
    d.rect(4,67,58,47,'#F3F8FA')
    d.text(33,73,'One common bath',9.5,True,anchor='middle')
    bead(d,31,94,18)
    d.text(7,113,'Pores',8.5,color=MUTED)
    d.line(15,109,34,98,'#839FAF',.25)
    d.text(72,72,'Later bead',10.5,True)
    for x,t,col in [(113,'Ca²⁺',CA),(131,'Na⁺',NA),(149,'Sites',INK)]:d.text(x,79,t,9.5,True,col,anchor='middle')
    anchors=[(44.5,82.5),(43,93),(34,101)]
    for i,(r,anchor) in enumerate(zip(rows,anchors)):
        y=87+i*10
        d.line(*anchor,66,y-1,EDGE[i],.28,ident=f'region-map-{r["region"]}',**{'data-semantics':'undirected region correspondence'})
        d.circle(*anchor,.65,EDGE[i])
        d.text(70,y,r['region'].capitalize(),9.5)
        for x,v in [(113,r['later_bound_Ca']),(131,r['later_bound_Na']),(149,r['negative_groups'])]:d.text(x,y,v,10,anchor='middle')
    d.text(80,121,'Bath:  Ca²⁺ 40 → 24     Na⁺ 0 → 32     Cl⁻ 80 → 80',9,anchor='middle')

def region_led(d,rows):
    d.text(6,8,'Shared sites, different regional occupancy',12,True)
    d.text(154,15,'Teaching DEMO',8.5,color=MUTED,anchor='end')
    d.rect(4,20,61,60,'#F3F8FA')
    d.text(34.5,26,'One common bath',9.5,True,anchor='middle')
    bead(d,33,54,23)
    d.text(77,25,'Occupied sites · later bead',10,True)
    # Length encodes occupied groups, not ion count or physical region volume.
    for i,r in enumerate(rows):
        y=38+i*18;ca=int(r['later_bound_Ca']);na=int(r['later_bound_Na']);n=int(r['negative_groups']);u=2.05
        d.text(77,y-3,r['region'].capitalize(),9.5,True)
        d.rect(77,y,2*ca*u,3.5,'#D9825A',CA,.25,ident=f'{r["region"]}-Ca-sites',**{'data-site-count':2*ca,'data-aggregation':'not individual ions'})
        d.rect(77+2*ca*u,y,na*u,3.5,'#78B5C8',NA,.25,ident=f'{r["region"]}-Na-sites',**{'data-site-count':na,'data-aggregation':'not individual ions'})
        d.text(77,y+9,f'{ca} Ca²⁺ + {na} Na⁺   /   {n} sites',9)
    d.text(34,86,'Connected water-filled pores',8.5,color=MUTED,anchor='middle')
    d.line(6,90,154,90,'#D6E0E4',.3)
    local_pair(d,22,96,.9)
    d.text(80,123,'One representative pair',8.5,color=MUTED,anchor='middle')

CAPTION='''One Ca²⁺ exchanges for two Na⁺ on the same fixed negative groups. The local before/after pair is a representative mechanism view, not two extra populations: each Ca²⁺ binds two groups in a single region; each Na⁺ binds one. The single hydrated bead has connected permeable shell (0.80–1.00 R), middle (0.45–0.80 R), and core (0–0.45 R). The pore is schematic. All 80 sites are occupied initially by Na⁺ and later by 16 Ca²⁺ plus 48 Na⁺; regional counts are exact, not inferred from region volume. The one well-mixed bath changes from 40 Ca²⁺, 0 Na⁺, 80 Cl⁻ to 24 Ca²⁺, 32 Na⁺, 80 Cl⁻. Chloride remains outside as spectator. These are constructed teaching counts at a specified transient, not measurements or equilibrium/rate predictions. No mobile pore-water ions remain at either snapshot; H⁺, anion binding, precipitation, water and polymer mass are excluded from this count model.'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);p.add_argument('--candidate',choices=['exchange-led','region-led','both'],default='both');a=p.parse_args()
    rows=list(csv.DictReader((a.inputs/'region_populations.csv').open()));bal=list(csv.DictReader((a.inputs/'system_balance.csv').open()))
    for r in rows:
        assert 2*int(r['later_bound_Ca'])+int(r['later_bound_Na'])==int(r['negative_groups'])
        assert int(r['later_groups_used_by_Ca'])==2*int(r['later_bound_Ca'])
        assert int(r['later_groups_used_by_Na'])==int(r['later_bound_Na'])
    assert [(r['region'],r['negative_groups'],r['later_bound_Ca'],r['later_bound_Na']) for r in rows]==[('shell','24','8','8'),('middle','36','6','24'),('core','20','2','16')]
    assert sum(int(r['negative_groups']) for r in rows)==80
    assert sum(int(r['later_bound_Ca']) for r in rows)==16 and sum(int(r['later_bound_Na']) for r in rows)==48
    by={r['quantity']:r for r in bal}
    expected_balance={'bead_bound_Ca':(0,16),'bead_bound_Na':(80,48),'bead_fixed_negative_groups':(80,80),'bath_Ca':(40,24),'bath_Na':(0,32),'bath_Cl':(80,80),'system_Ca':(40,40),'system_Na':(80,80),'system_Cl':(80,80)}
    assert {k:(int(v['initial']),int(v['later'])) for k,v in by.items()}==expected_balance, 'This authored DEMO must be redesigned for different populations.'
    for ion in ['Ca','Na']:
        assert int(by['bead_bound_'+ion]['initial'])+int(by['bath_'+ion]['initial'])==int(by['bead_bound_'+ion]['later'])+int(by['bath_'+ion]['later'])
    a.out.mkdir(parents=True,exist_ok=False)
    for key,func in [('exchange-led',exchange_led),('region-led',region_led)]:
        if a.candidate not in ['both',key]:continue
        d=Drawing(a.out/key,a.font,a.bold);func(d,rows);checks=d.finish(a.pdftoppm)
        (d.out/'caption.txt').write_text(CAPTION+'\n',encoding='utf8')
        (d.out/'alt-text.txt').write_text('A representative pair shows two sodium ions replaced by one calcium on the same two negative groups. A single bead has three connected concentric regions. Shell has 8 calcium and 8 sodium on 24 sites; middle 6 and 24 on 36 sites; core 2 and 16 on 20 sites. There is one common bath, and chloride stays outside.\n',encoding='utf8')
        checks.update({'demo':True,'scientific_arithmetic':'PASS','all_input_rows':rows,'system_balance':bal,'representation':'Representative local pair plus complete regional/system counts; no full individual-site census in the graphic','input_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.inputs.iterdir() if f.is_file()},'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'not_run':['Human reading test','author aesthetics approval','physical printing','all color-vision conditions','cross-editor SVG rendering']})
        (d.out/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
        (d.out/'output-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in d.out.iterdir() if f.is_file()},indent=2))
        print(key,checks['min_font_pt'])
if __name__=='__main__':main()
