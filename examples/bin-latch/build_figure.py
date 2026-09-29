"""Rebuild the invented mechanism with editable vectors. No external services.

python build_figure.py --out OUT --font FONT.ttf --bold-font BOLD.ttf --pdftoppm EXE
OUT must not exist. Inputs default to resources beside this script.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, re, shutil, subprocess
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W,H=160*72/25.4,102*72/25.4
P={'ink':'#203442','tab':'#CEE1F1','tabline':'#456784','shoe':'#A6D5CE','shoeline':'#24675E',
   'housing':'#DDE2E5','hline':'#66747C','sled':'#F0D7A4','sledline':'#88602E','ghost':'#89949C','rule':'#BCC7CD','white':'#FFFFFF'}
ITEMS=[]
def add(kind,id,**kw): ITEMS.append(dict(kind=kind,id=id,**kw))
def rect(id,x,y,w,h,fill,stroke,sw=.8,**kw):add('rect',id,x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,**kw)
def line(id,x1,y1,x2,y2,stroke=P['ink'],sw=.8,dash=False,**kw):add('line',id,x1=x1,y1=y1,x2=x2,y2=y2,stroke=stroke,sw=sw,dash=dash,**kw)
def poly(id,pts,fill,stroke,sw=.8,**kw):add('polygon',id,pts=pts,fill=fill,stroke=stroke,sw=sw,**kw)
def txt(id,x,y,s,size=10,bold=False,anchor='start'):add('text',id,x=x,y=y,text=s,size=size,bold=bold,anchor=anchor,fill=P['ink'])
def arrow(id,x1,y1,x2,y2,stroke=P['ink'],sw=1.1,meaning='motion'):
    line(id,x1,y1,x2,y2,stroke,sw,meaning=meaning)
    a=math.atan2(y2-y1,x2-x1);L=4.6;B=2.2
    pts=[(x2,y2),(x2-L*math.cos(a)+B*math.sin(a),y2-L*math.sin(a)-B*math.cos(a)),(x2-L*math.cos(a)-B*math.sin(a),y2-L*math.sin(a)+B*math.cos(a))]
    poly(id+'-head',pts,stroke,stroke,.1)

def scene(revision):
    txt('title',10,15,'D: stop-supported retention, transverse release',11,True)
    line('top-rule',10,23,W-10,23,P['rule'],.6)
    for state,ox,label in [('engaged',0,'a  Engaged: outward load'),('released',226,'b  Unloaded: tooth clear')]:
        txt(state+'-title',ox+10,39,label,10.5,True)
        dy=0 if state=='engaged' else -12
        # x-y cut at the locking window: tab plane x-z, thickness along y.
        rect(state+'-tab',ox+20,118,176,20,P['tab'],P['tabline'],entity='tab',state=state)
        rect(state+'-window',ox+117,118,23,20,P['white'],P['tabline'],entity='tab-window',state=state)
        rect(state+'-stop',ox+98,65,11,52,P['housing'],P['hline'],entity='stop',state=state)
        rect(state+'-guide',ox+162,65,7,52,P['housing'],P['hline'],entity='guide',state=state)
        poly(state+'-shoe',[(ox+109,83+dy),(ox+162,83+dy),(ox+162,118+dy),(ox+140,118+dy),(ox+140,128+dy),(ox+125,128+dy),(ox+125,118+dy),(ox+109,118+dy)],P['shoe'],P['shoeline'],1,entity='shoe',state=state)
        txt(state+'-shoe-label',ox+135.5,102+dy,'Shoe',10,False,'middle')
        txt(state+'-tab-label',ox+52,131,'Tab',10)
        if state=='engaged':
            txt('stop-label',10,58,'Fixed stop',10)
            line('stop-leader',62,61,101,80,P['hline'],.65)
            txt('guide-label',153,58,'Guide',9.5)
            line('guide-leader',164,60,165,65,P['hline'],.65)
            arrow('pull',72,108,24,108,meaning='outward load -x')
            txt('pull-label',22,98,'Pull −x',10)
            txt('engagement-label',104,160,'1.0 mm overlap',9.5)
            line('engagement-leader',133,149,133,129,P['ink'],.6)
            txt('window-label',29,157,'Window',9.5)
            line('window-leader',68,154,120,136,P['tabline'],.6)
        else:
            arrow('shoe-retract',ox+181,110,ox+181,74,P['shoeline'],meaning='shoe translation +y')
            txt('shoe-y',ox+188,84,'+y',10)
            txt('gap-label',ox+98,160,'0.2 mm nominal gap',9.5)
            line('gap-leader',ox+134,149,ox+134,116.9,P['ink'],.6)
            txt('preload-label',ox+11,59,'Wall preload < 2 N',9.5)
        arrow(state+'-x-axis',ox+25,176,ox+48,176,P['hline'],.7)
        arrow(state+'-y-axis',ox+25,176,ox+25,159,P['hline'],.7)
        txt(state+'-x-label',ox+52,179,'+x',9)
        txt(state+'-y-label',ox+11,154,'+y',9)
    line('panel-split',10,187,W-10,187,P['rule'],.6)
    txt('ramp-title',10,202,'c  Ramp action (y–z view)',10.5,True)
    # Two separate views keep the complete initial shoe visible. Their local
    # origins differ by 221 pt; dimensions and the 0.4 displacement ratio match.
    for name,ox,rise in [('initial',0,0),('lifted',221,30)]:
        rx=105+ox; top=220-rise; bottom=280-rise
        contact_y=245; contact_x=rx+0.4*(contact_y-top)
        # Filled wedge and shoe meet exactly. Break only the ramp outline
        # around their shared point so two finite-width strokes do not double
        # paint the shoe corner. This is graphic treatment, not a clearance.
        poly('ramp-'+name,[(rx,top),(rx+24,bottom),(rx,bottom)],P['sled'],P['sled'],0,entity='sled',state=name)
        line('ramp-back-'+name,rx,top,rx,bottom,P['sledline'],.9)
        line('ramp-base-'+name,rx,bottom,rx+24,bottom,P['sledline'],.9)
        line('ramp-face-upper-'+name,rx,top,contact_x-.6,contact_y-1.5,P['sledline'],.9)
        line('ramp-face-lower-'+name,contact_x+.6,contact_y+1.5,rx+24,bottom,P['sledline'],.9)
        rect('shoe-'+name,contact_x,225,45,20,P['shoe'],P['shoeline'],.9,entity='shoe',state=name)
        txt('shoe-label-'+name,contact_x+22.5,239,'Shoe',10,False,'middle')
        txt('state-label-'+name,contact_x+22.5,263,'Initial' if name=='initial' else 'After lift',9.5,False,'middle')
    txt('sled-label',60,249,'Sled',10)
    line('sled-leader',84,246,109,253,P['sledline'],.65)
    arrow('sled-up',306,280,306,234,P['sledline'],1.1,meaning='sled translation +z')
    txt('sled-up-label',242,253,'+z  3.0 mm',10)
    arrow('shoe-right',352,219,393,219,P['shoeline'],1.1,meaning='shoe translation +y')
    txt('shoe-displacement',344,210,'+y  1.2 mm',10)
    arrow('return-left',390,271,360,271,P['shoeline'],.8,meaning='integral tongue bias -y')
    txt('return-label',326,285,'Tongue biases −y',9.5)
    txt('status',10,285,'DEMO FICTION',9,True)
    return ITEMS

def svg(items,p):
    ET.register_namespace('','http://www.w3.org/2000/svg')
    root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width='160mm',height='102mm',viewBox=f'0 0 {W} {H}')
    for a in items:
        d={'id':a['id']}
        for key in ['entity','state','meaning']:
            if key in a:d['data-'+key]=a[key]
        if a['kind']=='text':
            d.update(x=str(a['x']),y=str(a['y']),fill=a['fill'],**{'font-family':'Arial','font-size':str(a['size']),'font-weight':'bold' if a['bold'] else 'normal','text-anchor':a['anchor']})
            e=ET.SubElement(root,'text',d);e.text=a['text'];continue
        d.update(fill=a.get('fill','none'),stroke=a['stroke'],**{'stroke-width':str(a['sw'])})
        if a.get('dash'):d['stroke-dasharray']='3 2'
        if a['kind']=='rect':d.update(x=str(a['x']),y=str(a['y']),width=str(a['w']),height=str(a['h']))
        elif a['kind']=='line':d.update({k:str(a[k]) for k in ['x1','y1','x2','y2']})
        elif a['kind']=='polygon':d['points']=' '.join(f'{x},{y}' for x,y in a['pts'])
        ET.SubElement(root,a['kind'],d)
    ET.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)

def pdf(items,p,font,bold):
    pdfmetrics.registerFont(TTFont('Body',str(font)))
    pdfmetrics.registerFont(TTFont('Bold',str(bold)))
    c=canvas.Canvas(str(p),pagesize=(W,H),pageCompression=0,invariant=1)
    c.setTitle('DEMO FICTION: sliding shoe mechanism')
    def color(s):return tuple(int(s[i:i+2],16)/255 for i in (1,3,5))
    for a in items:
        c.saveState()
        if a['kind']=='text':
            c.setFillColorRGB(*color(a['fill']));c.setFont('Bold' if a['bold'] else 'Body',a['size'])
            f={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[a['anchor']]
            f(a['x'],H-a['y'],a['text']);c.restoreState();continue
        c.setLineWidth(a['sw']);c.setStrokeColorRGB(*color(a['stroke']))
        if a.get('dash'):c.setDash(3,2)
        fill=a.get('fill','none')!='none'
        if fill:c.setFillColorRGB(*color(a['fill']))
        if a['kind']=='rect':c.rect(a['x'],H-a['y']-a['h'],a['w'],a['h'],fill=int(fill),stroke=1)
        elif a['kind']=='line':c.line(a['x1'],H-a['y1'],a['x2'],H-a['y2'])
        else:
            q=c.beginPath();q.moveTo(a['pts'][0][0],H-a['pts'][0][1])
            for x,y in a['pts'][1:]:q.lineTo(x,H-y)
            q.close();c.drawPath(q,fill=int(fill),stroke=1)
        c.restoreState()
    c.showPage();c.save()

def main():
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--font',type=Path,required=True);a.add_argument('--bold-font',type=Path,required=True);a.add_argument('--pdftoppm',type=Path,required=True);a.add_argument('--revision',choices=['first','final'],default='final');a.add_argument('--csv',type=Path,default=Path(__file__).with_name('results.csv'));a.add_argument('--manuscript',type=Path,default=Path(__file__).with_name('manuscript.md'));args=a.parse_args()
    if args.out.exists():a.error('Output exists; first and revision artifacts must be preserved')
    args.out.mkdir(parents=True)
    items=scene(args.revision);svg(items,args.out/'figure.svg');pdf(items,args.out/'figure.pdf',args.font,args.bold_font)
    subprocess.run([str(args.pdftoppm),'-png','-r','300','-singlefile',str(args.out/'figure.pdf'),str(args.out/'figure')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    im=Image.open(args.out/'figure.png').convert('RGB');im.save(args.out/'figure.png',dpi=(300,300))
    im.convert('L').save(args.out/'figure_grayscale.png',dpi=(300,300))
    # Explicit approximate deuteranopia screen, not a medical or all-CVD certification.
    arr=np.asarray(im)/255.;lin=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    sim=np.clip(lin@matrix.T,0,1);srgb=np.where(sim<=.0031308,sim*12.92,1.055*sim**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb,0,1)*255)).save(args.out/'figure_deuteranopia.png',dpi=(300,300))
    # 96 px/in display proxy: width 605 px corresponds to 160 mm in CSS at 100%.
    im.resize((round(160/25.4*96),round(102/25.4*96)),Image.Resampling.LANCZOS).save(args.out/'preview_160mm_96dpi.png',dpi=(96,96))
    (args.out/'preview_160mm.html').write_text('<!doctype html><meta charset="utf-8"><title>160 mm review</title><style>body{margin:15mm;background:#eee}img{width:160mm;height:102mm;background:white}</style><img src="figure.svg" alt="DEMO FICTION sliding shoe mechanism"><p>160 × 102 mm at 100% CSS zoom; physical screen size depends on display settings.</p>',encoding='utf-8')
    shutil.copy2(args.csv,args.out/'results.csv');shutil.copy2(args.manuscript,args.out/'manuscript.md')
    rows=list(csv.DictReader(args.csv.open(encoding='utf-8-sig',newline='')))
    text=(args.out/'manuscript.md').read_text(encoding='utf-8')
    words=re.findall(r"[A-Za-z0-9]+(?:[’'−–.-][A-Za-z0-9]+)*",re.sub(r'!\[[^]]*\]\([^)]*\)','',text))
    assert len(rows)==8 and all(r['evidence_status']=='DEMO_FICTION_PRESET' for r in rows)
    assert len(words)<=1800,(len(words),'words exceed limit')
    for r in rows:
        expected=f"{r['retention_median_N']} [{r['retention_min_N']}–{r['retention_max_N']}] | {r['release_success_n']}/{r['release_attempts_n']} | {r['release_peak_force_success_only_median_N']} | {r['hardware_mass_g']} | {r['discrete_hardware_parts_n']}"
        assert expected in text,expected
    spec={'evidence_status':'DEMO_FICTION_PRESET','main_message':'A fixed x-facing stop reacts outward tab loading while an unloaded sled ramp retracts the same shoe along y.','representation':'D0 orthographic sections, schematic not to scale; same logical objects across views','output':{'width_mm':160,'height_mm':102,'placement_width_mm':160,'dpi':300},'roles':P,'locked_values':{'tooth_overlap_mm':1.0,'shoe_retraction_mm':1.2,'sled_travel_mm':3.0,'nominal_gap_mm':.2,'release_wall_preload_N':'<2'},'items':items,'omitted_geometry':['complete housing','integral return tongue','underside relief slot'],'caption_location':'manuscript.md, Figure 1','input_csv_sha256':hashlib.sha256(args.csv.read_bytes()).hexdigest()}
    (args.out/'figure_spec.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    reader=PdfReader(args.out/'figure.pdf');page=reader.pages[0]
    checks={'word_count_including_captions_and_tables':len(words),'word_count_method':'regex English/numeric tokens; markdown syntax and image alt excluded','csv_rows':len(rows),'table_rows_match_csv':True,'fixtures':sum(int(r['retention_n'])+int(r['release_attempts_n']) for r in rows),'figure_mm':[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72],'png_pixels':list(im.size),'png_dpi':300,'svg_text_nodes':sum(a['kind']=='text' for a in items),'font_pt_range':[min(a['size'] for a in items if a['kind']=='text'),max(a['size'] for a in items if a['kind']=='text')],'svg_embedded_images':0,'pdf_images':len(page.images),'pdf_searchable_text':len(page.extract_text())>100,'native_figure_api_used':False,'scientific_review':'REVIEW_REQUIRED','visual_review':'REVIEW_REQUIRED','author_acceptance':False}
    (args.out/'build_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    (args.out/'alt_text.txt').write_text('DEMO FICTION. In two aligned x-y views, the same tab window engages a shoe tooth and then clears it when the shoe moves +y while remaining alongside the fixed x-facing stop. A y-z detail shows an upward sled ramp moving the shoe transversely. The diagram labels 1.0 mm overlap, 1.2 mm retraction, 3.0 mm sled travel, 0.2 mm nominal clearance, and unloaded release below 2 N. Separate initial and lifted views show the same parts at the same scale and shoe height. The ramp outline is interrupted at the shared contact point solely to avoid doubled strokes; fills still meet.',encoding='utf-8')
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
