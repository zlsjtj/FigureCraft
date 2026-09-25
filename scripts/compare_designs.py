"""Portable SVG comparison with bounded change classification, never aesthetic scoring."""
from pathlib import Path
import argparse,base64,hashlib,html,json,math,re,xml.etree.ElementTree as ET
G=('x','y','x1','y1','x2','y2','width','height','cx','cy','r','rx','ry','d','points','transform')
SHAPES={'rect','circle','ellipse','path','polygon','polyline','line'}
# These constructs can change the rendered result outside the inspected attributes.
# Report that boundary rather than treating an unrecognised change as style-only.
UNINSPECTED={'use','image','foreignObject','textPath','clipPath','mask','filter','marker','symbol','style','animate','animateTransform','set'}
LENGTH=re.compile(r'^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z%]*)\s*$')
MM_PER_UNIT={'':25.4/96,'px':25.4/96,'mm':1,'cm':10,'in':25.4,'pt':25.4/72,'pc':25.4/6,'q':0.25}

def positive_mm(value):
    value=float(value)
    if not math.isfinite(value) or value<=0:raise ValueError('Placement width must be a finite positive number of millimetres')
    return value

def absolute_length(value):
    match=LENGTH.fullmatch(value or '')
    if not match:return None
    number=float(match[1]);unit=match[2].lower()
    if not math.isfinite(number) or number<=0 or unit not in MM_PER_UNIT:return None
    return number*MM_PER_UNIT[unit]

def placement_info(source,width_mm):
    """Compute a declared viewport and bounded font scaling, not rendered typography."""
    root=ET.fromstring(source['raw']);limits=[]
    design_width=absolute_length(root.get('width'));design_height=absolute_length(root.get('height'))
    try:
        vb=[float(x) for x in re.split(r'[\s,]+',(root.get('viewBox') or '').strip())]
        if len(vb)!=4 or not all(math.isfinite(x) for x in vb) or vb[2]<=0 or vb[3]<=0:vb=None
    except ValueError:vb=None
    if vb:
        ratio=vb[2]/vb[3];user_width=vb[2];basis='viewBox'
    elif design_width is not None and design_height is not None:
        ratio=design_width/design_height;user_width=design_width*96/25.4;basis='absolute_viewport_without_valid_viewBox'
        limits.append('No valid viewBox; aspect ratio uses declared absolute width/height and 96 CSS px per inch.')
    else:
        ratio=user_width=None;basis='UNKNOWN'
        limits.append('No valid viewBox or complete absolute viewport; height and user-unit font scaling are unknown. Browser intrinsic fallback is not verified.')
    if design_width is None or design_height is None:
        limits.append('One or both source dimensions are absent, relative or unsupported; original physical size is not established.')
    css_unknown=any(e.tag.rsplit('}',1)[-1]=='style' or 'style' in e.attrib or 'class' in e.attrib for e in root.iter()) or b'<?xml-stylesheet' in source['raw']
    fonts=[]
    def visit(e,font=None,transformed=False,nested=False):
        tag=e.tag.rsplit('}',1)[-1];font=e.get('font-size',font)
        transformed=transformed or bool(e.get('transform'))
        nested=nested or (tag=='svg' and e is not root)
        if tag in ('text','tspan'):
            direct=''.join([e.text or '']+[c.tail or '' for c in e]).strip()
            if direct:
                reasons=[];size_mm=absolute_length(font)
                if css_unknown:reasons.append('CSS or external stylesheet may override font and geometry')
                if transformed:reasons.append('Element or ancestor transform is not resolved')
                if nested:reasons.append('Nested SVG viewport is not resolved')
                if size_mm is None:reasons.append('Font size is absent, relative or unsupported')
                if user_width is None:reasons.append('User-unit viewport scale is unknown')
                pt=None if reasons else size_mm*96/25.4*width_mm/user_width*72/25.4
                fonts.append({'element':tag,'text':direct,'text_scope':'direct_text_nodes_only','inherited_or_local_font_size':font,
                              'placement_font_pt':pt,'status':'UNKNOWN' if reasons else 'COMPUTED_NOT_RENDER_VERIFIED','limits':reasons})
        for child in e:visit(child,font,transformed,nested)
    visit(root)
    known=[f['placement_font_pt'] for f in fonts if f['placement_font_pt'] is not None]
    return {'design':{'width':root.get('width'),'height':root.get('height'),'absolute_width_mm':design_width,'absolute_height_mm':design_height,'viewBox':vb},
            'placement':{'width_mm':width_mm,'height_mm':width_mm/ratio if ratio else None,'aspect_ratio_width_over_height':ratio,'aspect_ratio_basis':basis,
                         'width_scale_from_declared_source':width_mm/design_width if design_width else None,'mm_per_user_unit':width_mm/user_width if user_width else None},
            'font_scaling':{'status':'PARTIAL_OR_UNKNOWN' if any(f['status']=='UNKNOWN' for f in fonts) else 'COMPUTED_NOT_RENDER_VERIFIED' if fonts else 'NO_DIRECT_TEXT',
                            'known_font_count':len(known),'unknown_font_count':len(fonts)-len(known),'minimum_known_font_pt':min(known) if known else None,'entries':fonts},
            'limits':limits+['CSS mm set a browser reference size; screen zoom, display density and scaling mean they are not a calibrated physical ruler.',
                             'Computed font sizes do not verify font substitution, glyph bounds, legibility, scientific meaning or aesthetics.']}
def inspect(p):
    raw=p.read_bytes();root=ET.fromstring(raw)
    if root.tag.rsplit('}',1)[-1]!='svg':raise ValueError(f'Not an SVG: {p}')
    shapes=[];textpos=[];texts=[];uninspected=set()
    def visit(e,ancestors=()):
        tag=e.tag.rsplit('}',1)[-1]
        if tag in UNINSPECTED:uninspected.add(tag)
        if 'style' in e.attrib or 'class' in e.attrib:uninspected.add('CSS_style_or_class')
        if tag=='svg' and e is not root:uninspected.add('nested_svg_viewport')
        transform=ancestors+((e.get('transform'),) if e.get('transform') else ())
        if tag in SHAPES:shapes.append((tag,tuple((a,e.get(a)) for a in G if a!='transform' and e.get(a) is not None),transform))
        if tag in ('text','tspan'):
            textpos.append((tag,tuple((a,e.get(a)) for a in ('x','y','dx','dy','text-anchor','font-size') if e.get(a) is not None),transform))
        if tag=='text':texts.append(''.join(e.itertext()))
        for c in e:visit(c,transform)
    visit(root)
    # Keep drawing order: coincident shapes can occlude differently.
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'viewBox':root.get('viewBox'),'width':root.get('width'),'height':root.get('height'),'object_geometry':shapes,'text_placement':textpos,'texts':texts,'uninspected_features':sorted(uninspected),'raw':raw}
def compare(before,after):
    objects=before['object_geometry']!=after['object_geometry'] or before['viewBox']!=after['viewBox']
    textpos=before['text_placement']!=after['text_placement']
    size=(before['width'],before['height'])!=(after['width'],after['height'])
    unknown=sorted(set(before.get('uninspected_features',[])+after.get('uninspected_features',[])))
    same=before['sha256']==after['sha256']
    category='IDENTICAL_BYTES' if same else 'OBJECT_GEOMETRY_CHANGED' if objects else 'TEXT_PLACEMENT_CHANGED' if textpos else 'OUTPUT_SIZE_CHANGED' if size else 'UNCLASSIFIED_RENDER_CHANGE' if unknown else 'LABEL_STYLE_OR_METADATA_ONLY'
    return {'classification':category,'object_geometry_changed':objects,'text_placement_changed':textpos,'output_size_changed':size,'text_content_changed':before['texts']!=after['texts'],'geometry_coverage':'PARTIAL' if unknown else 'SUPPORTED_ATTRIBUTES_ONLY','uninspected_features':unknown,'technical_parsing':'PASS','composition_distinctness':'REVIEW_REQUIRED','effectiveness':'REVIEW_REQUIRED','scientific_review':'REVIEW_REQUIRED'}
def run(baseline,candidates,out,placement_width_mm=None):
    # Reject invalid placement before touching files or creating a directory.
    if placement_width_mm is not None:placement_width_mm=positive_mm(placement_width_mm)
    if out.exists():raise FileExistsError(f'Refusing existing output: {out}')
    sources=[inspect(p) for p in [baseline]+candidates]
    results=[compare(sources[0],c) for c in sources[1:]]
    if placement_width_mm is not None:
        for source in sources:source['sizing']=placement_info(source,placement_width_mm)
    # Validate all files before creating any result directory.
    out.mkdir(parents=True)
    def safe(s):return {k:v for k,v in s.items() if k not in ('raw','object_geometry','text_placement')}
    receipt={'status':'COMPARISON_CREATED_REVIEW_REQUIRED','scope':'Bounded SVG attribute comparison, including line endpoints and ancestor transforms. Physical width/height changes are separate. Unsupported rendering features are listed and unknown-only changes stay unclassified; semantic numeric equivalence, CSS, references, clipping and general rendered collision are not evaluated. Geometry changes do not prove a different composition or improved aesthetics.','baseline':safe(sources[0]),'candidates':[{'artifact':safe(s),'comparison':r} for s,r in zip(sources[1:],results)]}
    receipt['display']={'mode':'UNIFORM_CSS_MM_WIDTH' if placement_width_mm is not None else 'RESPONSIVE_LEGACY','placement_width_mm':placement_width_mm,
                        'physical_ruler_verified':False,'note':'CSS millimetres are browser reference units, not a calibrated screen ruler. Inspect the exported paper at its actual placement size separately.'}
    (out/'comparison.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=[]
    for i,s in enumerate(sources):
        label='Baseline' if i==0 else f'Candidate {i}'
        data=base64.b64encode(s['raw']).decode('ascii')
        size_style='';size_note=''
        if placement_width_mm is not None:
            height=s['sizing']['placement']['height_mm'];h=f'{height:.12g}mm' if height is not None else 'auto'
            size_style=f' style="width:{placement_width_mm:.12g}mm;min-width:{placement_width_mm:.12g}mm;max-width:none;height:{h};flex:none"'
            size_note='<p>Aspect ratio: '+html.escape(s['sizing']['placement']['aspect_ratio_basis'])+'. Font scaling is bounded; see comparison.json.</p>'
        cards.append(f'<section><h2>{label}: {html.escape(Path(s["path"]).name)}</h2><img{size_style} alt="{label}" src="data:image/svg+xml;base64,{data}">{size_note}<details><summary>Extracted labels</summary><pre>{html.escape(chr(10).join(s["texts"]))}</pre></details></section>')
    layout='main{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:28px}section{min-width:0}img{width:100%;height:auto}'
    notice=''
    if placement_width_mm is not None:
        layout=f'main{{display:flex;gap:28px;overflow-x:auto;align-items:flex-start}}section{{flex:0 0 auto;width:{placement_width_mm:.12g}mm;box-sizing:content-box}}img{{display:block;max-width:none}}'
        notice=f'<p>All figures use {placement_width_mm:.12g} CSS mm width. Scroll horizontally if needed; figures are not reduced to fit. Screen CSS mm are not a calibrated ruler. Unknown aspect ratios use browser intrinsic sizing and remain unverified.</p>'
    (out/'comparison.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Scientific figure comparison</title><style>body{font:16px system-ui;color:#202a33;margin:32px}section{border:1px solid #ddd;padding:20px}h2{font-size:18px}pre{white-space:pre-wrap}'+layout+'</style><h1>Scientific figure comparison</h1><p>Same science must be verified separately. Structural difference does not establish improvement.</p>'+notice+'<main>'+''.join(cards)+'</main></html>',encoding='utf-8')
    return receipt
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,action='append',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--placement-width-mm',type=positive_mm);a=ap.parse_args()
    r=run(a.baseline,a.candidate,a.out,a.placement_width_mm)
    print(json.dumps({'status':r['status'],'changes':[c['comparison']['classification'] for c in r['candidates']]},ensure_ascii=False))
if __name__=='__main__':main()
