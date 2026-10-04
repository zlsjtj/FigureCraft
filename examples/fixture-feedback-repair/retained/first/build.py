"""Rebuild this fixed constructed DEMO. Requires matplotlib, numpy, Pillow, pypdf.
No experiment or scientific inference is performed. Paths resolve from this file.
"""
from pathlib import Path
import argparse, csv, hashlib, json, re, shutil, sys
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
from PIL import Image, ImageOps
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
INK = '#253544'
MUTED = '#566774'
STRIP = '#C9DAE8'
GOLD = '#C99738'
COLORS = {'A':'#62557C', 'B':'#33769B', 'C':'#217F73', 'D':'#A45835'}
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':9,
    'text.color':INK, 'axes.labelcolor':INK, 'xtick.color':INK, 'ytick.color':INK,
    'svg.fonttype':'none', 'svg.hashsalt':'repeat-holder-demo', 'pdf.fonttype':42,
    'axes.linewidth':.65, 'savefig.facecolor':'white'})

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(fig, out, stem, mm):
    for ext in ['svg','pdf','png']:
        kwargs = {'dpi':300} if ext=='png' else {}
        if ext == 'pdf': kwargs['metadata']={'CreationDate':None, 'ModDate':None,
            'Title':stem+' — constructed DEMO', 'Subject':'Fictional fixed-input illustration'}
        elif ext == 'svg': kwargs['metadata']={'Date':None, 'Description':'Constructed DEMO; no experiment was run.'}
        fig.savefig(out/f'{stem}.{ext}', **kwargs)
    plt.close(fig)
    im=Image.open(out/f'{stem}.png').convert('RGB')
    ImageOps.grayscale(im).save(out/f'{stem}_gray.png')
    # Simple declared deuteranopia simulation, not a clinical or print certification.
    rgb=np.asarray(im).astype(float)/255
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    matrix=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    cvd=np.clip(linear@matrix.T,0,1)
    srgb=np.where(cvd<=.0031308,12.92*cvd,1.055*cvd**(1/2.4)-.055)
    Image.fromarray(np.uint8(np.clip(srgb*255,0,255))).save(out/f'{stem}_deuteranopia.png')

def figure1(out, revision):
    fig=plt.figure(figsize=(160/25.4,100/25.4))
    ax=fig.add_axes([0,0,1,1]); ax.set(xlim=(0,160),ylim=(0,100)); ax.axis('off')
    def t(x,y,s,size=9,weight='normal',ha='left',color=INK):
        return ax.text(x,y,s,fontsize=size,weight=weight,ha=ha,va='center',color=color)
    def line(pts,color=MUTED,lw=.7,style='-'):
        ax.plot(*zip(*pts),color=color,lw=lw,ls=style,solid_capstyle='round')
    def poly(pts,fill,edge='#627585',lw=.65,gid=None):
        q=Polygon(pts,closed=True,facecolor=fill,edgecolor=edge,lw=lw); q.set_gid(gid); ax.add_patch(q)
    def p(x,y,z): return (17+1.80*x+.66*y,45+.84*y+1.28*z)
    def slab(x0,x1,y0,y1,z0,z1,top,front,side,gid):
        poly([p(x0,y0,z0),p(x1,y0,z0),p(x1,y0,z1),p(x0,y0,z1)],front,gid=gid+'-front')
        poly([p(x1,y0,z0),p(x1,y1,z0),p(x1,y1,z1),p(x1,y0,z1)],side,gid=gid+'-side')
        poly([p(x0,y0,z1),p(x1,y0,z1),p(x1,y1,z1),p(x0,y1,z1)],top,gid=gid+'-top')
    def disc(x,y,z,r,face,edge=INK,lw=.6,gid=None):
        theta=np.linspace(0,2*np.pi,60)
        poly([p(x+r*np.cos(a),y+r*np.sin(a),z) for a in theta],face,edge,lw,gid)
    def pin(x,y):
        bottom=p(x,y,7); top=p(x,y,10)
        ax.add_patch(Rectangle((bottom[0]-1.3,bottom[1]),2.6,top[1]-bottom[1],facecolor='#7B8A95',edgecolor=INK,lw=.55))
        ax.add_patch(Ellipse(top,2.6,1.3,facecolor='#E3E9ED',edgecolor=INK,lw=.55))
    t(7,94,'a  C: assembled holder',11,'bold')
    t(153,94,'DEMO',9,ha='right',color=MUTED)
    # One common base, two supports, then the single opaque specimen.
    slab(-3,63,-3,15,-1.6,0,'#EEF1F3','#D6DDE1','#C4CED5','base')
    for x in [8,52]: slab(x-1.6,x+1.6,-1.5,14,0,6,'#BBC7CE','#9CADB9','#879CA9',f'support-{x}')
    slab(0,60,0,10,6,7,STRIP,'#91ACC0','#7D9BAD','specimen')
    # Schematic hole and washer at the fixed datum.
    disc(8,5,7.05,1.6,'#D7DFE3',gid='left-washer')
    disc(8,5,7.09,.75,'#465D6C',gid='left-hole')
    pin(8,5)
    # Capsule-shaped opening is expressed in the plane of the strip.
    slot=[]
    for a in np.linspace(-np.pi/2,np.pi/2,24): slot.append(p(54+1.05*np.cos(a),5+1.05*np.sin(a),7.04))
    for a in np.linspace(np.pi/2,3*np.pi/2,24): slot.append(p(50+1.05*np.cos(a),5+1.05*np.sin(a),7.04))
    poly(slot,'#8599A7',INK,.8,'right-slot')
    pin(52,5)
    # Leaf fixed to right support, contacting the strip beside rather than through the slot.
    poly([p(50.9,13.5,6.1),p(53.1,13.5,6.1),p(53.1,11.0,10),p(50.9,11.0,10)],'#A97524','#78591E',.65,'leaf-rise')
    poly([p(50.9,11,10),p(53.1,11,10),p(53.1,8.0,7.12),p(50.9,8.0,7.12)],'#DEB76E','#78591E',.65,'leaf-contact')
    for x in [20,40]: disc(x,5,7.10,.62,INK,INK,.4,f'fiducial-{x}')
    t(9,81,'Round datum',10)
    t(9,76,'+ seating washer',9)
    line([(29,73),(29,69),p(8,5,10)])
    t(63,84,'Two surface fiducials',10,ha='center')
    line([(63,80),(63,73),(57,73),p(20,5,7.15)])
    line([(63,73),(92,73),p(40,5,7.15)])
    t(113,81,'Releasable leaf',10)
    t(113,76,'beside the slot',9)
    line([(137,73),(137,69),p(52,8.7,8.1)])
    t(63,65.5,'60 × 10 × 1 mm strip',9,ha='center')
    t(9,37.5,'Support at x = 8 mm',9)
    line([(32,40),(32,43),p(8,-1,2)])
    t(109,37.5,'x = 52 mm',9)
    line([(121,40),(121,43),p(52,-1,2)])
    t(79,44,'Unsupported span',9,ha='center')
    # Lower panel: preparation and an explicit repeated local view.
    line([(7,32.7),(153,32.7)],'#CBD3D9',.6)
    t(7,27.5,'b  Before heating',10.5,'bold')
    t(7,21.5,'Center pin → seat datum',9)
    t(7,16.5,'Apply leaf → remove jig',9)
    t(7,11.5,'Verify travel clearance',9)
    t(7,5.5,'Jig absent during cycling',9,color=MUTED)
    t(90,27.5,'c  Same right slot, top view',10.5,'bold')
    # Detail is not drawn to physical scale; the contact is visibly beside the opening.
    ax.add_patch(Rectangle((119,4),9,20,facecolor='#B5C3CD',edgecolor='#728A9A',lw=.6))
    ax.add_patch(Rectangle((90,6.5),63,14.0,facecolor=STRIP,edgecolor='#627585',lw=.65))
    ax.add_patch(FancyBboxPatch((112.5,10.2),22,5.4,boxstyle='round,pad=0,rounding_size=2.7',facecolor='#8599A7',edgecolor=INK,lw=.75))
    ax.add_patch(Ellipse((123.5,12.9),4,4,facecolor='#E3E9ED',edgecolor=INK,lw=.65))
    ax.add_patch(Rectangle((121.5,17.5),4,6.5,facecolor='#DEB76E',edgecolor='#78591E',lw=.65))
    t(92,23,'Leaf',9)
    line([(103,23),(116,23),(121.5,21.7)])
    ax.annotate('',xy=(135,8.0),xytext=(112,8.0),arrowprops={'arrowstyle':'<->','color':INK,'lw':.75,'mutation_scale':8})
    t(123.5,3,'±0.40 mm along x',9,ha='center')
    if revision=='final':
        # First self-review found the inset pin insufficiently identified.
        t(147,12.9,'Pin',9,ha='center')
        line([(141.5,12.9),(127,12.9)])
    save(fig,out,'figure1',(160,100))

def figure2(out, rows, revision):
    fig,axs=plt.subplots(1,2,figsize=(160/25.4,80/25.4))
    fig.subplots_adjust(left=.10,right=.985,bottom=.25,top=.79,wspace=.38)
    fig.text(.045,.945,'DEMO · six installations per configuration and schedule',fontsize=9,color=MUTED)
    handles=[Line2D([],[],marker='o',linestyle='none',markersize=4,markerfacecolor='white',markeredgecolor=INK,label='T1: 25–80–25 °C'),
             Line2D([],[],marker='D',linestyle='none',markersize=3.5,markerfacecolor=INK,markeredgecolor=INK,label='T2: 25–140–25 °C')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,.913),ncol=2,frameon=False,fontsize=9,columnspacing=1.6,handletextpad=.35)
    for ax,col,limit,ymax,label in zip(axs,['cooled_drift_max_um','hot_lift_max_um'],[30,8],[90,32],['a  Cooled drift (µm)','b  Hot lift (µm)']):
        ax.set_title(label,loc='left',fontsize=10,weight='bold',pad=8)
        ax.axhspan(0,limit,facecolor='#EDF3F2',zorder=0)
        ax.axhline(limit,color='#687881',lw=.8,ls=(0,(4,2)),zorder=1)
        ax.text(3.54,limit+(2 if ymax==90 else .8),f'Limit {limit}',ha='right',fontsize=8.5,color=MUTED)
        for i,cfg in enumerate('ABCD'):
            for schedule,offset,marker,face in [('T1',-.15,'o','white'),('T2',.15,'D',COLORS[cfg])]:
                rr=[r for r in rows if r['configuration']==cfg and r['schedule']==schedule]
                xx=i+offset+np.linspace(-.09,.09,6)
                ax.scatter(xx,[float(r[col]) for r in rr],s=15 if marker=='o' else 12,
                           marker=marker,facecolor=face,edgecolor=COLORS[cfg],linewidth=.8,zorder=3)
        ax.set(xlim=(-.48,3.55),ylim=(0,ymax),xticks=range(4),xticklabels=list('ABCD'))
        ax.set_yticks([0,30,60,90] if ymax==90 else [0,8,16,24,32])
        ax.tick_params(labelsize=9,length=3,pad=3)
        for tick,cfg in zip(ax.get_xticklabels(),'ABCD'): tick.set_color(COLORS[cfg]); tick.set_fontweight('bold')
        ax.spines[['top','right']].set_visible(False)
        ax.spines[['left','bottom']].set_color('#81909A')
    fig.text(.10,.12,'Both criteria + no fracture:',fontsize=9,weight='bold')
    fig.text(.10,.055,'T1  A 6/6 · B 0/6 · C 6/6 · D 6/6',fontsize=8.5)
    fig.text(.56,.055,'T2  A 0/6 · B 0/6 · C 6/6 · D 0/6',fontsize=8.5)
    save(fig,out,'figure2',(160,80))

def tables(out, rows):
    source=ROOT/'input'/'results.csv'; shutil.copy2(source,out/'results.csv')
    header=['Schedule','Configuration','Installation','Cooled drift max (µm)','Hot lift max (µm)','Hot axial travel median (mm)','Fractures']
    lines=['# Table 1. Complete fixed constructed DEMO results','',
      'One row per installation; maxima and medians summarize its three thermal cycles. Values are copied without rounding, subtraction or omission. No experiment was run.','',
      '| '+' | '.join(header)+' |','|---|---|---:|---:|---:|---:|---:|']
    for r in rows: lines.append('| '+' | '.join(r.values())+' |')
    (out/'results_table.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    summary=[]
    for schedule in ['T1','T2']:
        for cfg in 'ABCD':
            group=[r for r in rows if r['schedule']==schedule and r['configuration']==cfg]
            s={'schedule':schedule,'configuration':cfg,'installations':len(group),
                'qualifying_installations':sum(float(r['cooled_drift_max_um'])<=30 and float(r['hot_lift_max_um'])<=8 and int(r['fractures'])==0 for r in group)}
            for key in ['cooled_drift_max_um','hot_lift_max_um','hot_axial_travel_median_mm']:
                vals=[float(r[key]) for r in group]; s[key+'_range']=[min(vals),max(vals)]
            summary.append(s)
    (out/'computed_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')

def check(out,rows):
    records={'data_rows':len(rows),'unique_installations':len({(r['schedule'],r['configuration'],r['installation']) for r in rows}),
             'csv_preserved_byte_for_byte':sha(out/'results.csv')==sha(ROOT/'input'/'results.csv'),'figures':[]}
    text=(out/'article.md').read_text(encoding='utf-8')
    counted='\n'.join(x for x in text.splitlines() if not x.startswith('Figure ') and not x.startswith('!['))
    records['article_word_count']=len(re.findall(r"\b[\w]+(?:[’'−–-][\w]+)*\b",counted))
    records['word_count_rule']='All article text including headings and DEMO notice; excludes image markup and standalone Figure captions. Hyphenated or dash-linked tokens count as one.'
    for name,mm in [('figure1',(160,100)),('figure2',(160,80))]:
        root=ET.parse(out/(name+'.svg')).getroot(); ns={'s':'http://www.w3.org/2000/svg'}
        texts=root.findall('.//s:text',ns); imgs=root.findall('.//s:image',ns)
        pdf=PdfReader(str(out/(name+'.pdf'))); box=pdf.pages[0].mediabox
        png=Image.open(out/(name+'.png'))
        rec={'name':name,'svg_text_nodes':len(texts),'svg_embedded_images':len(imgs),
             'pdf_pages':len(pdf.pages),'pdf_size_mm':[round(float(box.width)*25.4/72,5),round(float(box.height)*25.4/72,5)],
             'pdf_extracted_text':pdf.pages[0].extract_text(), 'png_pixels':list(png.size),
             'expected_size_mm':list(mm)}
        assert rec['pdf_size_mm']==list(mm),rec
        assert not imgs and texts
        records['figures'].append(rec)
    assert len(rows)==48 and records['unique_installations']==48
    assert records['csv_preserved_byte_for_byte']
    (out/'technical_checks.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return records

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True,type=Path); ap.add_argument('--revision',choices=['first','final'],default='final')
    args=ap.parse_args(); out=args.out.resolve()
    if out.exists() and any(out.iterdir()): raise SystemExit('Refusing to overwrite a nonempty output directory: '+str(out))
    out.mkdir(parents=True,exist_ok=True)
    rows=list(csv.DictReader((ROOT/'input'/'results.csv').open(encoding='utf-8-sig',newline='')))
    article=ROOT/'source'/f'article_{args.revision}.md'
    shutil.copy2(article,out/'article.md')
    figure1(out,args.revision); figure2(out,rows,args.revision); tables(out,rows)
    captions=[line for line in article.read_text(encoding='utf-8').splitlines() if line.startswith('Figure ')]
    (out/'captions.md').write_text('\n\n'.join(captions)+'\n',encoding='utf-8')
    (out/'alt_text.md').write_text('Figure 1. One strip spans two narrow supports on a shared base. Its left round datum is seated by a washer; at the right, a visible longitudinal slot surrounds a centered pin, while a leaf presses beside it. A lower detail repeats the right contact in plan view.\n\nFigure 2. Two dot plots show cooled drift and hot lift for every installation, split by configuration and schedule. In T1, A, C and D satisfy both limits. In T2 only C does. B fails lift in both schedules; A and D fail cooled drift in T2.\n',encoding='utf-8')
    rec=check(out,rows)
    hashes={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'article_words':rec['article_word_count'],'rows':len(rows),'technical_checks':'completed'},ensure_ascii=False))

if __name__=='__main__': main()
