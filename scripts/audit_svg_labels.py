"""Bounded typography and straight-guide audit for existing SVG; never a scientific approval."""
import argparse,hashlib,json,math,re,xml.etree.ElementTree as E
from pathlib import Path
from PIL import ImageFont
from reportlab.pdfbase.ttfonts import TTFont
from svg_text_contrast import screen as screen_contrast

NUM=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def finite(v):
    v=float(v)
    if not math.isfinite(v):raise ValueError('Nonfinite geometry')
    return v
def number(v):
    if not re.fullmatch(NUM,str(v)):raise ValueError('Unsupported unit or position list: '+str(v))
    return finite(v)
def straight(d):
    toks=re.findall('[A-Za-z]|'+NUM,d)
    if re.sub('[\\s,]','',d)!=''.join(toks):raise ValueError('Unsupported path syntax')
    if any(t.isalpha() and t not in 'MLHV' for t in toks):raise ValueError('Only absolute straight paths are audited')
    i=0;cmd=None;xy=None;segments=[]
    while i<len(toks):
        if toks[i] in 'MLHV':cmd=toks[i];i+=1
        if cmd is None:raise ValueError('Path command missing')
        count=2 if cmd in 'ML' else 1
        vals=list(map(finite,toks[i:i+count]));i+=count
        if len(vals)!=count:raise ValueError('Incomplete path')
        if cmd in 'ML':dest=tuple(vals)
        elif xy is None:raise ValueError('Path must start with M')
        else:dest=(vals[0],xy[1]) if cmd=='H' else (xy[0],vals[0])
        if cmd!='M':segments.append((xy,dest))
        xy=dest
        if cmd=='M':cmd='L'
    return segments
def hit(a,b,r):
    x,y=a;dx=b[0]-x;dy=b[1]-y;lo,hi=0.,1.
    for p,q in [(-dx,x-r[0]),(dx,r[2]-x),(-dy,y-r[1]),(dy,r[3]-y)]:
        if p==0:
            if q<0:return False
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
        if lo>hi:return False
    return True

def audit(svg,font,bold_font,placement_width_mm,regions=None,canvas_background=None):
    placement_width_mm=finite(placement_width_mm)
    if placement_width_mm<=0:raise ValueError('Positive placement width required')
    root=E.parse(svg).getroot();view=list(map(finite,root.get('viewBox','').split()))
    if len(view)!=4 or view[2]<=0 or view[3]<=0:raise ValueError('Positive SVG viewBox required')
    scale=placement_width_mm*72/25.4/view[2];findings=[];texts=[];segments=[]
    def add(level,check,**kw):findings.append(dict(level=level,check=check,**kw))
    if re.search(r'<[A-Za-z_][\w.-]*:svg\b',Path(svg).read_text(encoding='utf-8-sig')):
        add('REVIEW_REQUIRED','prefixed_svg_root_compatibility',reason='Valid XML can still fail in document SVG importers; inspect the actual embedded rendering or serialize with the default SVG namespace')
    loaded={}
    for weight,path in [('normal',font),('bold',bold_font)]:
        if path is not None:
            path=Path(path)
            if not path.is_file():raise ValueError('Font file missing: '+str(path))
            face=TTFont('Audit_'+weight,str(path)).face
            family=face.familyName.decode('utf-8') if isinstance(face.familyName,bytes) else face.familyName
            loaded[weight]=(ImageFont.truetype(str(path),1024),face,family,sha(path))
    inheritable={'font-family','font-size','font-weight','text-anchor','fill','stroke','stroke-width','display','visibility'}
    def walk(el,style,bad=False):
        tag=el.tag.rsplit('}',1)[-1];attrs=dict(style);attrs.update({k:v for k,v in el.attrib.items() if k in inheritable})
        identifier=el.get('id') or f'{tag}-{len(texts)}-{len(segments)}'
        if attrs.get('display')=='none' or attrs.get('visibility')=='hidden':return
        uncertain=any(k in el.attrib for k in ('transform','style','class','clip-path','mask','opacity','filter')) or tag in ('style','use','foreignObject','image','symbol','defs','textPath')
        if uncertain:add('REVIEW_REQUIRED','unsupported_svg_feature',object=identifier,tag=tag)
        bad=bad or uncertain
        if tag=='text' and not bad:
            value=''.join(el.itertext())
            try:
                if len(el) or any(k in el.attrib for k in ('dx','dy','rotate','textLength','lengthAdjust','dominant-baseline','alignment-baseline','letter-spacing','word-spacing')):raise ValueError('Complex text layout')
                size=number(attrs['font-size']);x=number(el.get('x','0'));y=number(el.get('y','0'))
                if size<=0:raise ValueError('Positive font size required')
                weight=attrs.get('font-weight','normal');weight={'400':'normal','700':'bold'}.get(weight,weight)
                if weight not in loaded:raise ValueError('Font weight not provided: '+weight)
                f,face,family,_=loaded[weight]
                if attrs.get('font-family','').strip('"\'').lower()!=family.lower():raise ValueError('Font family does not match supplied file')
                missing=[c for c in value if ord(c) not in face.charToGlyph]
                if missing:add('FAIL','missing_glyph',object=identifier,characters=sorted(set(missing)))
                anchor=attrs.get('text-anchor','start')
                if anchor not in ('start','middle','end'):raise ValueError('Unknown text anchor')
                advance=f.getlength(value)*size/1024;x-=advance*{'start':0,'middle':.5,'end':1}[anchor]
                b=f.getbbox(value,anchor='ls');box=[x+b[0]*size/1024,y+b[1]*size/1024,x+b[2]*size/1024,y+b[3]*size/1024]
                pt=size*scale
                item={'id':identifier,'text':value,'bounds':box,'font_pt':pt};texts.append(item)
                if pt<8:add('FAIL','placement_font_floor_8pt',object=identifier,text=value,pt=pt)
                if box[0]<view[0] or box[1]<view[1] or box[2]>view[0]+view[2] or box[3]>view[1]+view[3]:add('FAIL','text_outside_view',object=identifier,text=value)
            except (ValueError,KeyError) as e:add('REVIEW_REQUIRED','unmeasured_text',object=identifier,text=value,reason=str(e))
        if tag in ('path','line','polyline') and not bad and attrs.get('stroke','none')!='none':
            try:
                if tag=='path':
                    # Filled shapes/arrow heads are outside the guide-line scope.
                    if attrs.get('fill','black')!='none':return
                    spans=straight(el.get('d',''))
                elif tag=='line':spans=[((number(el.get('x1','0')),number(el.get('y1','0'))),(number(el.get('x2','0')),number(el.get('y2','0'))))]
                else:
                    values=list(map(finite,re.split('[,\\s]+',el.get('points','').strip())))
                    if len(values)%2:raise ValueError('Odd polyline coordinate count')
                    pts=list(zip(values[::2],values[1::2]));spans=list(zip(pts,pts[1:]))
                width=number(attrs.get('stroke-width','1'))
                for a,b in spans:segments.append({'id':identifier,'from':a,'to':b,'width':width})
            except ValueError as e:add('REVIEW_REQUIRED','unmeasured_guide',object=identifier,reason=str(e))
        for child in el:walk(child,attrs,bad)
    walk(root,{})
    for line in segments:
        for t in texts:
            b=t['bounds'];pad=line['width']/2
            if hit(line['from'],line['to'],[b[0]-pad,b[1]-pad,b[2]+pad,b[3]+pad]):
                add('REVIEW_REQUIRED','guide_text_contact',object=line['id'],text=t['text'],label=t['id'],reason='Ink bounds and guide overlap; inspect actual stacking/dashes before deciding repair')
    for i,a in enumerate(texts):
        for b in texts[i+1:]:
            if min(a['bounds'][2],b['bounds'][2])>max(a['bounds'][0],b['bounds'][0]) and min(a['bounds'][3],b['bounds'][3])>max(a['bounds'][1],b['bounds'][1]):add('REVIEW_REQUIRED','text_text_contact',labels=[a['id'],b['id']])
    region_results=[]
    if regions is not None:
        if regions.get('svg_sha256')!=sha(svg):raise ValueError('Region specification is not bound to this SVG')
        for rule in regions.get('labels',[]):
            matches=[t for t in texts if t['text']==rule['text']]
            b=list(map(finite,rule['bounds']))
            if len(b)!=4 or b[2]<=b[0] or b[3]<=b[1]:raise ValueError('Invalid owner-region bounds')
            ok=len(matches)==1 and all([matches[0]['bounds'][0]>=b[0],matches[0]['bounds'][1]>=b[1],matches[0]['bounds'][2]<=b[2],matches[0]['bounds'][3]<=b[3]])
            region_results.append({'text':rule['text'],'owner':rule['owner'],'status':'PASS' if ok else 'FAIL'})
            if not ok:add('FAIL','label_outside_declared_owner_region',text=rule['text'],owner=rule['owner'])
    painted=screen_contrast(root,texts,canvas_background)
    findings.extend(painted['findings'])
    status='FAIL' if any(f['level']=='FAIL' for f in findings) else 'REVIEW_REQUIRED' if findings or not texts else 'PASS'
    return {'status':status,'technical_status':status,'overall_status':'FAIL' if status=='FAIL' else 'REVIEW_REQUIRED',
        'svg_sha256':sha(svg),'placement_width_mm':placement_width_mm,'minimum_font_pt':min((t['font_pt'] for t in texts),default=None),
        'text':texts,'guide_segments':segments,'findings':findings,'owner_regions':region_results,'painted_text_contrast':painted,
        'fonts':{k:{'family':v[2],'sha256':v[3]} for k,v in loaded.items()},
        'scientific_review':'NOT_RUN','visual_review':'NOT_RUN','author_acceptance':False,
        'limits':['Measures explicit untransformed text using the supplied matching font.',
                  'Only unfilled straight guides are checked, including auxiliary/dashed lines.',
                  'Dash gaps, z-order, painted backgrounds, curves and arbitrary SVG/CSS need visual review.',
                  'Owner regions are supplied by an editor; containment cannot establish scientific meaning.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('svg',type=Path);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path);p.add_argument('--placement-width-mm',type=float,required=True);p.add_argument('--regions',type=Path);p.add_argument('--canvas-background',help='Explicit #RRGGBB canvas; optional solid-paint contrast screen');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('Output exists; use a new receipt')
        r=audit(a.svg,a.font,a.bold_font,a.placement_width_mm,json.loads(a.regions.read_text(encoding='utf-8')) if a.regions else None,a.canvas_background)
        a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:r[k] for k in ('technical_status','overall_status','minimum_font_pt')},ensure_ascii=False));return 1 if r['status']=='FAIL' else 2 if r['status']=='REVIEW_REQUIRED' else 0
    except (OSError,ValueError,KeyError,E.ParseError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
