"""Conservative solid-paint contrast screening for measured SVG labels.

Not a general SVG renderer. Requires an explicit canvas; understands opaque
rectangle interiors. Other intersecting paint, partial coverage, CSS, transforms,
opacity and later paint keep the affected label under review.
"""
import re,math
from collections import Counter
from palette_tools import contrast,rgb

def color(s):
 s={'white':'#FFFFFF','black':'#000000'}.get(s,s)
 if re.fullmatch(r'#[0-9a-fA-F]{3}',s or ''):s='#'+''.join(c*2 for c in s[1:])
 rgb(s);return s.upper()
def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
def contains(a,b):return a[0]<=b[0] and a[1]<=b[1] and a[2]>=b[2] and a[3]>=b[3]

def screen(root,texts,canvas=None):
 if canvas is None:return {'status':'NOT_RUN','reason':'No canvas background supplied','labels':[],'findings':[]}
 canvas=color(canvas);lookup={t['id']:t for t in texts};paints=[];labels=[];findings=[]
 ids=Counter(el.get('id') for el in root.iter() if el.get('id'))
 inherited={'fill','stroke','stroke-width','display','visibility','fill-opacity','stroke-opacity'}
 def walk(el,style,uncertain=False):
  tag=el.tag.rsplit('}',1)[-1];attrs=dict(style);attrs.update({k:v for k,v in el.attrib.items() if k in inherited});ident=el.get('id')
  if tag in ['defs','title','desc','metadata']:return
  if attrs.get('display')=='none':return
  # A hidden group can have an explicitly visible child; keep that case uncertain.
  uncertain=uncertain or attrs.get('visibility')=='hidden' or any(k in el.attrib for k in ['style','class','transform','opacity','filter','mask','clip-path'])
  if tag=='text' and ident in lookup and ids[ident]==1:
   t=lookup[ident];box=t['bounds'];bg=canvas;sources=['declared canvas'];unresolved=[]
   for paint in paints:
    if paint['bounds'] is not None and not intersects(paint['bounds'],box):continue
    if paint['interior'] is not None and contains(paint['interior'],box):
     bg=paint['fill'];sources=[paint['id']];unresolved=[]
    else:unresolved.append(paint['id'])
   row={'id':ident,'text':t['text'],'bounds':box,'paint_index':len(paints),'background':bg,'background_sources':sources,'status':'REVIEW_REQUIRED'}
   try:
    if uncertain or attrs.get('fill-opacity','1')!='1' or attrs.get('stroke','none')!='none':raise ValueError('Text has unsupported paint')
    row['foreground']=color(attrs.get('fill','black'))
    if unresolved:raise ValueError('Background intersects unsupported or partial paint: '+', '.join(unresolved))
    row['ratio']=contrast(row['foreground'],bg);row['status']='PASS' if row['ratio']>=4.5 else 'FAIL'
    row['threshold']=4.5
   except ValueError as e:row['reason']=str(e)
   labels.append(row)
  elif tag not in ['svg','g','text','tspan']:
   paint={'id':ident or tag,'bounds':None,'interior':None,'fill':None}
   try:
    if uncertain:raise ValueError('Unsupported inherited rendering feature')
    sw=float(attrs.get('stroke-width','1')) if attrs.get('stroke','none')!='none' else 0
    if attrs.get('fill-opacity','1')!='1' or attrs.get('stroke-opacity','1')!='1':raise ValueError('Transparent paint')
    if tag=='rect':
     x,y,w,h=[float(el.get(k,'0')) for k in ['x','y','width','height']]
     paint['bounds']=[x-sw/2,y-sw/2,x+w+sw/2,y+h+sw/2]
     if attrs.get('fill','black')!='none':
      fill=color(attrs.get('fill','black'));rx=float(el.get('rx','0'));ry=float(el.get('ry',str(rx)))
      paint['fill']=fill;paint['interior']=[x+max(sw/2,rx),y+max(sw/2,ry),x+w-max(sw/2,rx),y+h-max(sw/2,ry)]
    elif tag in ['polygon','polyline']:
     vs=list(map(float,re.split(r'[,\s]+',el.get('points','').strip())));assert len(vs)>=4 and len(vs)%2==0
     paint['bounds']=[min(vs[::2])-sw/2,min(vs[1::2])-sw/2,max(vs[::2])+sw/2,max(vs[1::2])+sw/2]
    elif tag=='line':
     x,y,u,v=[float(el.get(k,'0')) for k in ['x1','y1','x2','y2']];paint['bounds']=[min(x,u)-sw/2,min(y,v)-sw/2,max(x,u)+sw/2,max(y,v)+sw/2]
    elif tag in ['circle','ellipse']:
     x,y=float(el.get('cx','0')),float(el.get('cy','0'));rx=float(el.get('r',el.get('rx','0')));ry=float(el.get('r',el.get('ry','0')))
     paint['bounds']=[x-rx-sw/2,y-ry-sw/2,x+rx+sw/2,y+ry+sw/2]
    # General paths/use/images intentionally retain unknown bounds.
    if tag in ['rect','polygon','polyline','circle','ellipse'] and attrs.get('fill','black')=='none' and attrs.get('stroke','none')=='none':return
    if tag=='line' and attrs.get('stroke','none')=='none':return
    if paint['bounds'] is not None and not all(math.isfinite(v) for v in paint['bounds']):raise ValueError('Nonfinite paint geometry')
   except (ValueError,AssertionError):paint.update(bounds=None,interior=None,fill=None)
   paints.append(paint)
  for ch in el:walk(ch,attrs,uncertain)
 walk(root,{})
 for row in labels:
  later=[p['id'] for p in paints[row.pop('paint_index'):] if p['bounds'] is None or intersects(p['bounds'],row['bounds'])]
  if later:
   row['status']='REVIEW_REQUIRED';row['reason']='Later paint may cover text: '+', '.join(later);row.pop('ratio',None)
  if row['status']!='PASS':findings.append({'level':row['status'],'check':'painted_text_contrast','object':row['id'],'text':row['text'],'ratio':row.get('ratio'),'reason':row.get('reason','Below internal 4.5:1 screening threshold')})
 for t in texts:
  if t['id'] not in {r['id'] for r in labels}:
   labels.append({'id':t['id'],'text':t['text'],'status':'REVIEW_REQUIRED','reason':'No uniquely matched explicit SVG id'})
   findings.append({'level':'REVIEW_REQUIRED','check':'unmatched_contrast_label','object':t['id']})
 status='FAIL' if any(r['status']=='FAIL' for r in labels) else 'REVIEW_REQUIRED' if not labels or any(r['status']=='REVIEW_REQUIRED' for r in labels) else 'PASS'
 return {'status':status,'canvas':canvas,'labels':labels,'findings':findings,'scope':'Measured ID-bearing plain text; declared canvas plus supported opaque rect interiors. Unknown/partial/later paint is review, never assumed white. 4.5:1 is an internal screen, not aesthetic approval.'}
