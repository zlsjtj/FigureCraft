"""从公开教学记录重建机制图与完整结果图，不生成或拟合实验数据。"""
from pathlib import Path
import argparse, csv, hashlib, json, math, subprocess
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

INK='#233A45'; MUTED='#576D75'; LIGHT='#DDE4E6'; TEAL='#377F86'; CORAL='#AC503D'
COLORS={'E':'#647680','F':TEAL,'L':CORAL}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Drawing:
    def __init__(self,path,height,width=1000):
        self.path=path; self.w=width; self.h=height; self.scale=160/25.4*72/width
        self.pdf=canvas.Canvas(str(path.with_suffix('.pdf')),pagesize=(width*self.scale,height*self.scale),invariant=1)
        self.pdf.scale(self.scale,self.scale)
        self.svg=[]; self.labels=[]
    def poly(self,points,fill,stroke=None,sw=1.5):
        p=self.pdf.beginPath();p.moveTo(points[0][0],self.h-points[0][1])
        for x,y in points[1:]:p.lineTo(x,self.h-y)
        p.close();self.pdf.setFillColor(HexColor(fill));self.pdf.setStrokeColor(HexColor(stroke or fill));self.pdf.setLineWidth(sw)
        self.pdf.drawPath(p,fill=1,stroke=int(stroke is not None))
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
    def rect(self,x,y,w,h,fill,stroke=None,sw=1.5):self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],fill,stroke,sw)
    def line(self,points,color=INK,sw=1.5,dash=False):
        p=self.pdf.beginPath();p.moveTo(points[0][0],self.h-points[0][1])
        for x,y in points[1:]:p.lineTo(x,self.h-y)
        self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(sw);self.pdf.setDash([5,5] if dash else [])
        self.pdf.drawPath(p);self.pdf.setDash([])
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{sw}"'+(' stroke-dasharray="5 5"' if dash else '')+'/>')
    def circle(self,x,y,r,fill,stroke=INK,sw=1.5):
        self.pdf.setFillColor(HexColor(fill));self.pdf.setStrokeColor(HexColor(stroke));self.pdf.setLineWidth(sw);self.pdf.circle(x,self.h-y,r,fill=1,stroke=1)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(self,x,y,t,size=22,color=INK,bold=False,anchor='start'):
        font='bold' if bold else 'regular';w=pdfmetrics.stringWidth(t,font,size)
        left=x-w/2 if anchor=='middle' else x-w if anchor=='end' else x
        if left<0 or left+w>self.w+0.01:raise ValueError(('text outside canvas',t,left,w))
        self.pdf.setFont(font,size);self.pdf.setFillColor(HexColor(color));self.pdf.drawString(left,self.h-y,t)
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(t)}</text>')
        self.labels.append({'text':t,'point_size':round(size*self.scale,3),'x':x,'y':y})
    def arrow(self,x,y,x2,y2,color=INK,sw=2):
        self.line([(x,y),(x2,y2)],color,sw)
        a=math.atan2(y2-y,x2-x);l=9
        self.poly([(x2,y2),(x2-l*math.cos(a-.4),y2-l*math.sin(a-.4)),(x2-l*math.cos(a+.4),y2-l*math.sin(a+.4))],color)
    def finish(self,pdftoppm):
        self.pdf.save()
        self.path.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="{160*self.h/self.w}mm" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/>'+''.join(self.svg)+'</svg>',encoding='utf-8')
        subprocess.run([str(pdftoppm),'-r','220','-png','-singlefile',str(self.path.with_suffix('.pdf')),str(self.path)],check=True,capture_output=True)
        subprocess.run([str(pdftoppm),'-r','96','-png','-singlefile',str(self.path.with_suffix('.pdf')),str(self.path)+'-160mm'],check=True,capture_output=True)
        return {'labels':self.labels,'minimum_font_pt':min(x['point_size'] for x in self.labels),'width_mm':160,'height_mm':160*self.h/self.w}

def lock(d,x,y,closed):
    # 符号绑定销轴，未提供的夹具内部结构不在这里虚构。
    d.line([(x-10,y),(x-10,y-14),(x-5,y-22),(x+5,y-22),(x+10,y-14),(x+10,y if closed else y-7)],CORAL if closed else TEAL,2.8)
    d.rect(x-15,y,30,23,CORAL if closed else '#FFFFFF',CORAL if closed else TEAL,2)

def fixture(d,x,closed):
    # 单个横向销轴；两幅为同一夹具的操作状态。深度仅用于辨别表面。
    y=298; dx=35;dy=-23
    d.poly([(x-24,y),(x+247,y),(x+282,y-23),(x+11,y-23)],'#E9EDEE', '#ADBCC2')
    d.rect(x-24,y,271,19,'#C5D0D4','#879BA4')
    d.poly([(x+247,y),(x+282,y-23),(x+282,y-4),(x+247,y+19)],'#9DB0B9','#879BA4')
    # 试样上平面有坡度，侧视坡度放大。底面与固定下压板接触。
    top=[(x,y-51),(x+220,y-75)]
    d.poly([top[0],top[1],(x+255,y-98),(x+35,y-74)],'#EED7A6','#B29867')
    d.poly([top[0],top[1],(x+220,y),(x,y)],'#DDBD79','#B29867')
    d.poly([top[1],(x+255,y-98),(x+255,y-23),(x+220,y)],'#B29356','#A48A5A')
    # 横梁和携带销轴的支承，放在接触垫后面。
    d.rect(x+101,151,25,76,'#CBD5D9','#9EAFB7')
    d.poly([(x+49,125),(x+178,125),(x+206,107),(x+77,107)],'#F0F3F4','#A6B6BE')
    d.rect(x+49,125,129,29,'#D5DFE2','#A6B6BE')
    d.poly([(x+178,125),(x+206,107),(x+206,136),(x+178,154)],'#B4C5CC','#A6B6BE')
    # pad 的下表面与示意试样上表面相同，不能出现悬空贴合。
    a,b=top
    d.poly([(a[0],a[1]-25),(b[0],b[1]-25),(b[0]+dx,b[1]-25+dy),(a[0]+dx,a[1]-25+dy)],'#BDD8D9','#5C8C92')
    d.poly([(a[0],a[1]-25),(b[0],b[1]-25),b,a],'#77ADB2','#4F8289')
    d.poly([(b[0],b[1]-25),(b[0]+dx,b[1]-25+dy),(b[0]+dx,b[1]+dy),b],'#4F8289','#4F8289')
    pin=(x+113,y-76)
    d.circle(*pin,14,'#F8FAFA','#526E7B',2)
    d.circle(*pin,4,'#526E7B','#526E7B')
    lock(d,x+291,193,closed)
    d.line([(x+276,203),(x+260,214),(pin[0]+14,pin[1])],MUTED,1.4)
    d.arrow(x+115,78,x+115,103,INK)
    if not closed:
        # 转动标记绑定一个销轴，不画第二自由度。
        d.line([(x+55,209),(x+68,194),(x+85,187)],TEAL,2)
        d.poly([(x+85,187),(x+76,184),(x+80,195)],TEAL)
    return pin

def mechanism(out,poppler):
    d=Drawing(out/'mechanism',535)
    d.text(35,33,'a',25,bold=True);d.text(75,33,'Seat freely',27,bold=True)
    d.text(535,33,'b',25,bold=True);d.text(575,33,'Hold contact, then lock',27,bold=True)
    fixture(d,60,False);fixture(d,560,True)
    d.text(175,65,'10 N preload',22,MUTED,anchor='middle')
    d.text(675,65,'0.20 mm ramp after locking',22,MUTED,anchor='middle')
    d.arrow(435,236,500,236,MUTED,2)
    d.text(363,168,'Open',21,TEAL,anchor='middle')
    d.text(863,168,'Closed',21,CORAL,anchor='middle')
    # 标签只在首次对象上出现，位置与颜色不替代归属线。
    d.text(36,345,'Pad',22);d.line([(81,338),(60,302),(60,248),(73,233)],MUTED,1.2)
    d.text(148,345,'Coupon',22);d.line([(192,328),(192,276)],MUTED,1.2)
    d.text(287,345,'Fixed platen',22);d.line([(300,328),(300,308)],MUTED,1.2)
    d.text(595,345,'One pitch axis; no roll adjustment',22,MUTED)
    d.line([(35,371),(963,371)],LIGHT)
    d.text(35,400,'Lock timing',22,bold=True)
    d.text(470,400,'Approach',21,MUTED,anchor='middle');d.text(695,400,'Ramp',21,MUTED,anchor='middle')
    labels=[('E','Lock before approach',True,True),('F','Remain free',False,False),('L','Seat then lock',False,True)]
    for i,(m,label,seat,ramp) in enumerate(labels):
        y=433+i*38
        d.text(36,y,m,22,COLORS[m],True);d.text(75,y,label,22)
        d.line([(470,y-8),(695,y-8)],'#C7D2D5',2)
        for x,closed in [(470,seat),(695,ramp)]:d.circle(x,y-8,7,CORAL if closed else '#FFFFFF',CORAL if closed else TEAL,2)
        if m=='L':d.text(584,y-14,'lock',19,CORAL,anchor='middle')
    d.circle(805,432,7,'#FFFFFF',TEAL,2);d.text(823,439,'free',21,MUTED)
    d.circle(805,470,7,CORAL,CORAL,2);d.text(823,477,'locked',21,MUTED)
    return d.finish(poppler)

def results(out,rows,poppler):
    d=Drawing(out/'results',445)
    panels=[('F_cv_percent','Endpoint force CV (%)',8,2),('Drift_um','Lateral drift (µm)',140,35),('Seat_s','Preparation time (s)',35,7)]
    ybase=[132,239,346]; origins=[205,484,763];plotw=206;points=[]
    d.text(32,33,'All conditions, the same three modes',26,bold=True)
    for j,m in enumerate(['E','F','L']):
        x=671+j*99
        if m=='E':d.rect(x-4,22,8,8,'#FFFFFF',COLORS[m],1.8)
        elif m=='F':d.circle(x,26,5,'#FFFFFF',COLORS[m],1.8)
        else:d.poly([(x,20),(x+5,30),(x-5,30)],COLORS[m])
        d.text(x+13,33,m,22,COLORS[m],True)
    for i,lab in enumerate(['Flat','Pitch 1°','Roll 1°']):d.text(32,ybase[i]+6,lab,23,bold=True)
    for pi,(key,title,maxv,tick) in enumerate(panels):
        x=origins[pi]
        # 两行标题有固定归属，不缩小标签迁就长单行。
        titles={'F_cv_percent':['Endpoint force','CV (%)'],'Drift_um':['Lateral drift','(µm)'],'Seat_s':['Preparation time','(s)']}
        for k,t in enumerate(titles[key]):d.text(x+plotw/2,73+k*25,t,22,bold=k==0,anchor='middle')
        for val in range(0,maxv+1,tick):
            xx=x+plotw*val/maxv
            d.line([(xx,115),(xx,378)],LIGHT,1)
            d.text(xx,410,str(val),19,MUTED,anchor='middle')
        for ci,condition in enumerate(['flat','pitch_1deg','roll_1deg']):
            for mi,m in enumerate(['E','F','L']):
                row=next(r for r in rows if r['condition']==condition and r['mode']==m)
                v=float(row[key]);xx=x+plotw*v/maxv; yy=ybase[ci]+(mi-1)*22
                if m=='E':d.rect(xx-4,yy-4,8,8,'#FFFFFF',COLORS[m],1.8)
                elif m=='F':d.circle(xx,yy,5,'#FFFFFF',COLORS[m],1.8)
                else:d.poly([(xx,yy-6),(xx+5,yy+4),(xx-5,yy+4)],COLORS[m])
                points.append({'condition':condition,'mode':m,'field':key,'value':v,'x':xx,'y':yy})
    result=d.finish(poppler);result['points']=points
    assert len(points)==27
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('输出目录必须不存在')
    a.out.mkdir(parents=True)
    pdfmetrics.registerFont(TTFont('regular',str(a.font)));pdfmetrics.registerFont(TTFont('bold',str(a.bold_font)))
    source=Path(__file__).resolve().parent/'input/results.csv';rows=list(csv.DictReader(source.open(encoding='utf-8-sig')))
    assert len(rows)==9 and all(r['n_reseatings']=='8' for r in rows)
    rec={'data_sha256':sha(source),'source_sha256':sha(__file__),'demo':True,'mechanism':mechanism(a.out,a.pdftoppm),'results':results(a.out,rows,a.pdftoppm),'visual_review':'PENDING','human_approval':False}
    rec['files']={p.name:sha(p) for p in a.out.iterdir() if p.is_file()}
    (a.out/'build.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(a.out),'points':27,'minimum_font_pt':min(rec['mechanism']['minimum_font_pt'],rec['results']['minimum_font_pt'])}))

if __name__=='__main__':main()
