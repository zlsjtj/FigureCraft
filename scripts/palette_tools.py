"""Source-preserving swatches, Oklab-derived roles and bounded CVD screening."""
from __future__ import annotations
import argparse,copy,hashlib,json,math
from pathlib import Path

VERSION='1.1.0'
# Oklab equations: Bjorn Ottosson, public-domain implementation, 2021 matrices.
# CVD matrix: Machado et al. 2009, deuteranomaly severity 100, supplementary data.
CVD=((.367322,.860646,-.227968),(.280085,.672501,.047413),(-.011820,.042940,.968881))
def rgb(value):
    if not isinstance(value,str) or len(value)!=7 or value[0]!='#':raise ValueError('Use #RRGGBB')
    return tuple(int(value[i:i+2],16)/255 for i in (1,3,5))
def hx(v):return '#'+''.join(f'{round(max(0,min(1,x))*255):02X}' for x in v)
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def encoded(v):return 12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055
def luminance(v):return sum(a*linear(b) for a,b in zip((.2126,.7152,.0722),rgb(v)))
def contrast(fg,bg):
    a,b=sorted((luminance(fg),luminance(bg)));return (b+.05)/(a+.05)
def composite(fg,bg,alpha):
    if not 0<=alpha<=1:raise ValueError('alpha must be in [0,1]')
    return hx([a*alpha+b*(1-alpha) for a,b in zip(rgb(fg),rgb(bg))])
def to_oklab(color):
    r,g,b=map(linear,rgb(color))
    l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3)
    m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3)
    s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
    return (.2104542553*l+.793617785*m-.0040720468*s,
       1.9779984951*l-2.428592205*m+.4505937099*s,
       .0259040371*l+.7827717662*m-.808675766*s)
def from_oklab(L,a,b):
    l=(L+.3963377774*a+.2158037573*b)**3
    m=(L-.1055613458*a-.0638541728*b)**3
    s=(L-.0894841775*a-1.291485548*b)**3
    return (4.0767416621*l-3.3077115913*m+.2309699292*s,
      -1.2684380046*l+2.6097574011*m-.3413193965*s,
      -.0041960863*l-.7034186147*m+1.707614701*s)
def gamut(L,a,b):
    """Reduce chroma at fixed lightness/hue until within sRGB; no hue rotation."""
    for _ in range(100):
        v=from_oklab(L,a,b)
        if min(v)>=-1e-8 and max(v)<=1+1e-8:return hx([encoded(max(0,x)) for x in v])
        a*=.95;b*=.95
    raise ValueError('Gamut mapping failed')
def derive(base):
    L,a,b=to_oklab(base)
    fill=gamut(min(.92,L+.035),a*.85,b*.85)
    stroke=gamut(min(.43,L*.65),a*.65,b*.65)
    light=gamut(min(.97,L+(1-L)*.73),a*.38,b*.38)
    shadow=gamut(max(.22,L-.15),a*.8,b*.8)
    text=max(('#24323B','#FFFFFF'),key=lambda c:contrast(c,fill))
    return dict(base=base.upper(),fill=fill,stroke=stroke,highlight=light,shadow=shadow,marker=stroke,text=text)
def view_color(color,view):
    if color=='none' or view=='normal':return color
    v=list(map(linear,rgb(color)))
    if view=='grayscale':v=[sum(x*y for x,y in zip(v,(.2126,.7152,.0722)))]*3
    elif view=='deuteranopia':v=[sum(x*y for x,y in zip(row,v)) for row in CVD]
    else:raise ValueError(f'Unsupported view {view}')
    return hx([encoded(max(0,min(1,x))) for x in v])
def validate_library(lib):
    records=[]
    for p in lib['palettes']:
        for c in p['colors']:
            vals=c['rgb']
            okay=len(vals)==3 and all(isinstance(v,int) and 0<=v<=255 for v in vals)
            expected='#'+''.join(f'{v:02X}' for v in vals) if okay else None
            records.append({'palette':p['id'],'color':c['id'],'expected':expected,'given':c['hex'],
                'status':'PASS' if expected==c['hex'].upper() else 'FAIL'})
    return {'status':'FAIL' if any(r['status']=='FAIL' for r in records) else 'PASS',
        'scope':'RGB/HEX annotation arithmetic only','count':len(records),'records':records}
def resolve_roles(spec,library):
    palette=next((p for p in library['palettes'] if p['id']==spec['reference_palette']),None)
    if palette is None:raise ValueError('Unknown reference_palette')
    colors={c['id']:c['hex'] for c in palette['colors']}
    result={}
    for role,entry in spec['role_map'].items():
        base=entry.get('base') or colors.get(entry.get('swatch'))
        if not base:raise ValueError(f'Unresolved color role {role}')
        result[role]=derive(base)
    return result
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def semantic_payload(spec):
    result={k:spec.get(k) for k in ('scientific_message','evidence_status','source_refs','forbidden_implications',
       'entities','relations','exact_labels','locked_values','count_constraints','data','data_source','data_sha256','caption','alt_text')}
    # Preserve old-scene hashes; new binding contracts participate when present.
    for key in ('component_constraints','occlusion_constraints'):
        if key in spec:result[key]=spec[key]
    return result
def recolor(spec,theme):
    out=copy.deepcopy(spec)
    if set(theme)!={'reference_palette','role_map'}:raise ValueError('A recolor theme may only contain reference_palette and role_map')
    if set(theme['role_map'])!=set(spec['role_map']):raise ValueError('Color-only edits must preserve every semantic role')
    out.update(copy.deepcopy(theme))
    assert semantic_payload(out)==semantic_payload(spec)
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('validate');q.add_argument('library',type=Path);q.add_argument('--out',type=Path)
    q=sub.add_parser('derive');q.add_argument('spec',type=Path);q.add_argument('--library',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
    q=sub.add_parser('recolor');q.add_argument('spec',type=Path);q.add_argument('theme',type=Path);q.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.command=='validate':result=validate_library(json.loads(a.library.read_text(encoding='utf-8')))
        elif a.command=='derive':result={'derivation':'Oklab; chroma reduction for sRGB gamut; newly designed tokens','roles':resolve_roles(json.loads(a.spec.read_text(encoding='utf-8')),json.loads(a.library.read_text(encoding='utf-8')))}
        else:result=recolor(json.loads(a.spec.read_text(encoding='utf-8')),json.loads(a.theme.read_text(encoding='utf-8')))
        if a.out:
            if a.out.exists():raise ValueError('Output exists; preserve previous version')
            a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'output':str(a.out),'status':result.get('status','WRITTEN')} if a.out else result,ensure_ascii=False,indent=2))
        return 1 if result.get('status')=='FAIL' else 0
    except (ValueError,KeyError,OSError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
