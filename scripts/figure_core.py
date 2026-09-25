"""Small editable scene backend: SVG and matching vector PDF. No image service."""
from __future__ import annotations
import copy,hashlib,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from reportlab import rl_config
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from palette_tools import contrast,digest,resolve_roles,semantic_payload,view_color
from semantic_audit import audit_semantics

NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def tag(t):return '{'+NS+'}'+t
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fonts(latin,cjk=None):
    loaded={}
    for key,path in [('latin',latin),('cjk',cjk)]:
        if path:
            path=Path(path)
            if not path.is_file():raise ValueError(f'Font missing: {path}')
            name='Studio_'+key;f=TTFont(name,str(path));pdfmetrics.registerFont(f)
            family=f.face.familyName
            if isinstance(family,bytes):family=family.decode('utf-8','replace')
            loaded[key]={'name':name,'family':family,'path':str(path),'sha256':sha(path),'font':f}
    return loaded
def font_for(text,loaded):
    key='cjk' if any(ord(c)>0x2e7f for c in text) else 'latin'
    if key not in loaded:raise ValueError('Chinese label requires --cjk-font; no silent font fallback')
    return loaded[key]

def font_runs(text,loaded):
    """Explicit, glyph-checked Latin/CJK fallback; no tofu substitution."""
    runs=[]
    for ch in text:
        preferred=font_for(ch,loaded)
        candidates=[preferred]+[f for f in loaded.values() if f is not preferred]
        chosen=next((f for f in candidates if ord(ch) in f['font'].face.charToGlyph),None)
        if chosen is None:raise ValueError(f'No supplied font contains glyph {ch!r}')
        if runs and runs[-1][0]['name']==chosen['name']:runs[-1]=(chosen,runs[-1][1]+ch)
        else:runs.append((chosen,ch))
    return runs

def text_width(text,size,loaded):
    return sum(pdfmetrics.stringWidth(part,f['name'],size) for f,part in font_runs(text,loaded))
def wrap_text(text,max_width,size,loaded):
    """Font-metric wrapping; preserves all characters, never reduces font size."""
    lines=[]
    for paragraph in text.split('\n'):
        current=''
        for char in paragraph:
            if current and text_width(current+char,size,loaded)>max_width:
                # Prefer a recent space for English; Chinese can break between glyphs.
                last=current.rfind(' ')
                if last>len(current)*.5:
                    lines.append(current[:last]);current=current[last+1:]+char
                else:lines.append(current);current=char
            else:current+=char
        lines.append(current)
    return '\n'.join(lines)
def validate_spec(s):
    needed=('figure_id','scientific_message','evidence_status','entities','relations','exact_labels','locked_values','role_map','reference_palette','output','items')
    missing=[k for k in needed if k not in s]
    if missing:raise ValueError('Missing spec fields: '+', '.join(missing))
    ids=[e['id'] for e in s['entities']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate entity id')
    relations=[r['id'] for r in s['relations']]
    if len(relations)!=len(set(relations)):raise ValueError('Duplicate relation id')
    for r in s['relations']:
        if r['from'] not in ids or r['to'] not in ids:raise ValueError('Relation references an unknown entity')
        if r['kind'] not in ('flow','dependency','containment','inhibition','conditional','detail'):raise ValueError('Unspecified relation kind')
    itemids=[p['id'] for p in s['items']]
    if len(itemids)!=len(set(itemids)):raise ValueError('Duplicate drawing id')
    for rule in s.get('count_constraints',[]):
        selected=rule.get('item_ids');expected=rule['expected']
        if type(expected) is not int or expected<0 or (selected is not None and (len(selected)!=len(set(selected)) or len(selected)!=expected)):
            raise ValueError('Invalid count constraint: '+rule['name'])
        if selected is not None and any(id not in itemids for id in selected):raise ValueError('Count constraint missing objects: '+rule['name'])
        if selected is None and not rule.get('scope'):raise ValueError('Count constraint has neither item_ids nor an explicit scope')
    for p in s['items']:
        if p.get('entity') and p['entity'] not in ids:raise ValueError('Drawing references unknown entity')
        if p.get('relation') and p['relation'] not in relations:raise ValueError('Drawing references unknown relation')
        if p['type'] not in ('rect','ellipse','circle','polygon','path','line','text'):raise ValueError('Unsupported primitive '+p['type'])
        if 'fill_gradient' in p:
            g=p['fill_gradient'];stops=g.get('stops',[])
            if p['type'] in ('line','text') or g.get('kind') not in ('linear','radial'):raise ValueError('Gradient requires a filled shape and linear/radial kind')
            positions=[v[0] for v in stops]
            if len(stops)<2 or positions[0]!=0 or positions[-1]!=1 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in positions) or any(a>=b for a,b in zip(positions,positions[1:])):raise ValueError('Gradient stops must increase strictly from 0 to 1')
            keys=('cx','cy','r') if g['kind']=='radial' else ('x1','y1','x2','y2')
            if any(not isinstance(g.get(k),(int,float)) or not math.isfinite(g[k]) for k in keys):raise ValueError('Gradient coordinates must be finite')
            if g['kind']=='radial' and g['r']<=0:raise ValueError('Gradient radius must be positive')
    text='\n'.join(p.get('text','') for p in s['items'])
    for label in s['exact_labels']:
        if label not in text:raise ValueError('Locked label absent: '+label)
    if s.get('depth',{}).get('affects_quantitative_encoding',False):raise ValueError('Depth may not distort quantitative encoding')
    out=s['output']
    if not all(math.isfinite(out[k]) and out[k]>0 for k in ('width_mm','view_width','view_height')):raise ValueError('Invalid dimensions')
    if 'placement_width_mm' in out and (not math.isfinite(out['placement_width_mm']) or out['placement_width_mm']<=0):raise ValueError('Invalid placement width')
    semantic=audit_semantics(s)
    if semantic['status']=='FAIL':raise ValueError('Semantic constraint failed: '+json.dumps(semantic['findings'],ensure_ascii=False))
    return True
def geometry_payload(s):
    # Color-only edits cannot alter widths, shapes, labels, opacity, order or bindings.
    items=[]
    for p in s['items']:
        q={k:v for k,v in p.items() if k not in ('fill','stroke','background')}
        if 'fill_gradient' in q:
            q['fill_gradient']={**q['fill_gradient'],'stops':[v[0] for v in q['fill_gradient']['stops']]}
        items.append(q)
    return {'output':s['output'],'items':items}
def resolved(value,roles,view):
    if not value:return 'none'
    if value.startswith('@'):
        role,token=value[1:].split('.');value=roles[role][token]
    return view_color(value,view)
def bounds(p):
    t=p['type']
    if t=='rect':return [p['x'],p['y'],p['x']+p['w'],p['y']+p['h']]
    if t in ('circle','ellipse'):
        rx=p.get('rx',p.get('r'));ry=p.get('ry',p.get('r'))
        return [p['x']-rx,p['y']-ry,p['x']+rx,p['y']+ry]
    if t in ('polygon','line'):pts=p['points']
    elif t=='path':pts=[list(cmd[i:i+2]) for cmd in p['commands'] for i in range(1,len(cmd),2)]
    else:return None
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
def export_scene(s,out,loaded,library,view='normal'):
    validate_spec(s);out=Path(out);roles=resolve_roles(s,library)
    w=s['output']['view_width'];h=s['output']['view_height'];mm=s['output']['width_mm'];scale=mm*72/25.4/w
    root=ET.Element(tag('svg'),{'width':f'{mm}mm','height':f'{mm*h/w}mm','viewBox':f'0 0 {w} {h}'})
    defs=ET.SubElement(root,tag('defs'))
    ET.SubElement(root,tag('title')).text=s['scientific_message']
    ET.SubElement(root,tag('desc')).text=s.get('alt_text',s['scientific_message'])
    ET.SubElement(root,tag('metadata')).text=json.dumps({'figure_id':s['figure_id'],'evidence_status':s['evidence_status'],
      'semantic_digest':digest(semantic_payload(s)),'view':view},ensure_ascii=False)
    rl_config.useA85=0
    c=canvas.Canvas(str(out/'figure.pdf'),pagesize=(w*scale,h*scale),pageCompression=1,invariant=1)
    c.setTitle(s['scientific_message']);c.setAuthor('Scientific Figure Studio — DEMO' if s.get('demo') else 'Scientific Figure Studio')
    reports=[];segments=[]
    for p in s['items']:
        t=p['type'];fill=resolved(p.get('fill','none'),roles,view);stroke=resolved(p.get('stroke','none'),roles,view)
        sw=p.get('stroke_width',1);alpha=p.get('opacity',1)
        group=ET.SubElement(root,tag('g'),{'id':p['id'],'data-entity':p.get('entity',''),'data-role':p.get('role',''),'data-relation':p.get('relation',''),
            'data-logical-id':p.get('logical_id',''),'data-object-part':p.get('object_part','')})
        attr={'fill':fill,'stroke':stroke,'stroke-width':str(sw),'opacity':str(alpha)}
        gradient=p.get('fill_gradient')
        if gradient:
            gid='gradient-'+p['id'];ga={'id':gid,'gradientUnits':'userSpaceOnUse','color-interpolation':'sRGB'}
            if gradient['kind']=='radial':
                ga.update({k:str(gradient[k]) for k in ('cx','cy','r')});ga.update(fx=ga['cx'],fy=ga['cy'])
                gn=ET.SubElement(defs,tag('radialGradient'),ga)
            else:
                ga.update({k:str(gradient[k]) for k in ('x1','y1','x2','y2')});gn=ET.SubElement(defs,tag('linearGradient'),ga)
            for position,color in gradient['stops']:ET.SubElement(gn,tag('stop'),{'offset':str(position),'stop-color':resolved(color,roles,view)})
            attr['fill']='url(#'+gid+')'
        if p.get('dash'):attr['stroke-dasharray']=' '.join(map(str,p['dash']))
        c.saveState();c.setLineWidth(sw*scale)
        if fill!='none':c.setFillColor(fill)
        if stroke!='none':c.setStrokeColor(stroke)
        c.setFillAlpha(alpha);c.setStrokeAlpha(alpha);c.setDash([x*scale for x in p.get('dash',[])])
        f=int(fill!='none');st=int(stroke!='none');bb=bounds(p);rec={'id':p['id'],'type':t,'bounds':bb,'entity':p.get('entity'),'relation':p.get('relation')}
        def paint_gradient(path):
            c.saveState();c.clipPath(path,stroke=0,fill=0)
            colors=[resolved(v[1],roles,view) for v in gradient['stops']];positions=[v[0] for v in gradient['stops']]
            if gradient['kind']=='radial':c.radialGradient(gradient['cx']*scale,(h-gradient['cy'])*scale,gradient['r']*scale,colors,positions)
            else:c.linearGradient(gradient['x1']*scale,(h-gradient['y1'])*scale,gradient['x2']*scale,(h-gradient['y2'])*scale,colors,positions)
            c.restoreState()
            if st:c.drawPath(path,stroke=1,fill=0)
        if t=='rect':
            ET.SubElement(group,tag(t),dict(attr,x=str(p['x']),y=str(p['y']),width=str(p['w']),height=str(p['h']),rx=str(p.get('radius',0))))
            if gradient:
                path=c.beginPath();path.roundRect(p['x']*scale,(h-p['y']-p['h'])*scale,p['w']*scale,p['h']*scale,p.get('radius',0)*scale);paint_gradient(path)
            else:c.roundRect(p['x']*scale,(h-p['y']-p['h'])*scale,p['w']*scale,p['h']*scale,p.get('radius',0)*scale,stroke=st,fill=f)
        elif t in ('ellipse','circle'):
            rx=p.get('rx',p.get('r'));ry=p.get('ry',p.get('r'))
            ET.SubElement(group,tag('ellipse'),dict(attr,cx=str(p['x']),cy=str(p['y']),rx=str(rx),ry=str(ry)))
            if gradient:
                path=c.beginPath();path.ellipse((p['x']-rx)*scale,(h-p['y']-ry)*scale,2*rx*scale,2*ry*scale);paint_gradient(path)
            else:c.ellipse((p['x']-rx)*scale,(h-p['y']-ry)*scale,(p['x']+rx)*scale,(h-p['y']+ry)*scale,stroke=st,fill=f)
        elif t in ('polygon','line','path'):
            if t=='path':commands=p['commands']
            else:commands=[['M',*p['points'][0]]]+[['L',*q] for q in p['points'][1:]]+([['Z']] if t=='polygon' else [])
            d=' '.join(' '.join(map(str,cmd)) for cmd in commands);ET.SubElement(group,tag('path'),dict(attr,d=d))
            path=c.beginPath();last=None
            for cmd in commands:
                if cmd[0]=='M':path.moveTo(cmd[1]*scale,(h-cmd[2])*scale);last=cmd[1:3]
                elif cmd[0]=='L':
                    path.lineTo(cmd[1]*scale,(h-cmd[2])*scale)
                    if p.get('relation'):segments.append({'id':p['id'],'from':last,'to':cmd[1:3]})
                    last=cmd[1:3]
                elif cmd[0]=='C':path.curveTo(cmd[1]*scale,(h-cmd[2])*scale,cmd[3]*scale,(h-cmd[4])*scale,cmd[5]*scale,(h-cmd[6])*scale);last=cmd[5:7]
                elif cmd[0]=='Z':path.close()
                else:raise ValueError('Unsupported path operator')
            if gradient:paint_gradient(path)
            else:c.drawPath(path,stroke=st,fill=f)
        elif t=='text':
            size=p.get('size',16);leading=p.get('leading',size*1.3);align=p.get('align','left')
            node=ET.SubElement(group,tag('text'),dict(attr,**{'font-size':str(size),'text-anchor':'start','{http://www.w3.org/XML/1998/namespace}space':'preserve'}))
            rects=[];families=set()
            for i,line in enumerate(p['text'].split('\n')):
                runs=font_runs(line,loaded);metrics=[pdfmetrics.getAscentDescent(f['name'],size) for f,part in runs] or [(0,0)]
                asc=max(a for a,d in metrics);desc=min(d for a,d in metrics)
                x=p['x'];y=p['y']+i*leading;width=text_width(line,size,loaded)
                left=x-width*(.5 if align=='center' else 1 if align=='right' else 0)
                rects.append([left,y-asc,left+width,y-desc])
                cursor=left
                for font,part in runs:
                    families.add(font['family'])
                    ET.SubElement(node,tag('tspan'),{'x':str(cursor),'y':str(y),'font-family':font['family']}).text=part
                    c.setFont(font['name'],size*scale);c.drawString(cursor*scale,(h-y)*scale,part)
                    cursor+=pdfmetrics.stringWidth(part,font['name'],size)
            rec.update({'line_bounds':rects,'bounds':[min(x[0] for x in rects),min(x[1] for x in rects),max(x[2] for x in rects),max(x[3] for x in rects)],
              'font_pt':size*scale,'text':p['text'],'max_width':p.get('max_width'),
              'foreground':fill,'declared_background':resolved(p.get('background','#FFFFFF'),roles,view),
              'contrast':contrast(fill,resolved(p.get('background','#FFFFFF'),roles,view)),'glyph_check':'PASS','font':sorted(families)})
        c.restoreState();reports.append(rec)
    # Pretty-print whitespace inside mixed-font SVG text can change visible spacing.
    c.showPage();c.save()
    ET.ElementTree(root).write(out/'figure.svg',encoding='utf-8',xml_declaration=True)
    manifest={'version':2,'figure_id':s['figure_id'],'spec_sha256':digest(s),'semantic_digest':digest(semantic_payload(s)),
      'geometry_digest':digest(geometry_payload(s)),'source_refs':s.get('source_refs',[]),'demo':s.get('demo',False),
      'count_constraints':s.get('count_constraints',[]),
      'semantic_constraints':audit_semantics(s),'placement_width_mm':s['output'].get('placement_width_mm'),
      'entities':s['entities'],'relations':s['relations'],'width_mm':mm,'height_mm':mm*h/w,'view_width':w,'view_height':h,
      'scale_pt_per_unit':scale,'depth':s.get('depth',{}),'roles':roles,'view':view,'objects':reports,'relation_segments':segments,
      'editability':{'text':'SVG text nodes; PDF subset-embedded font text','objects':'separate vector primitives with stable IDs','embedded_raster':False},
      'gradient_export':{'count':sum('fill_gradient' in p for p in s['items']),'backends':'native SVG gradients and native PDF shading clipped to the same shape','interpolation':'encoded sRGB / PDF DeviceRGB','physical_lighting':False},
      'fonts':{k:{a:b for a,b in v.items() if a!='font'} for k,v in loaded.items()},
      'files':{n:sha(out/n) for n in ('figure.svg','figure.pdf')},'visual_review':'NOT_RUN','scientific_author_acceptance':False,'journal_eligibility':'UNVERIFIED'}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'figure_spec.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest
