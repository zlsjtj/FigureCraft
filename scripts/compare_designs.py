"""Portable SVG comparison with bounded change classification, never aesthetic scoring."""
from pathlib import Path
import argparse,base64,hashlib,html,json,xml.etree.ElementTree as ET
G=('x','y','x1','y1','x2','y2','width','height','cx','cy','r','rx','ry','d','points','transform')
SHAPES={'rect','circle','ellipse','path','polygon','polyline','line'}
# These constructs can change the rendered result outside the inspected attributes.
# Report that boundary rather than treating an unrecognised change as style-only.
UNINSPECTED={'use','image','foreignObject','textPath','clipPath','mask','filter','marker','symbol','style','animate','animateTransform','set'}
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
def run(baseline,candidates,out):
    if out.exists():raise FileExistsError(f'Refusing existing output: {out}')
    sources=[inspect(p) for p in [baseline]+candidates]
    results=[compare(sources[0],c) for c in sources[1:]]
    # Validate all files before creating any result directory.
    out.mkdir(parents=True)
    def safe(s):return {k:v for k,v in s.items() if k not in ('raw','object_geometry','text_placement')}
    receipt={'status':'COMPARISON_CREATED_REVIEW_REQUIRED','scope':'Bounded SVG attribute comparison, including line endpoints and ancestor transforms. Physical width/height changes are separate. Unsupported rendering features are listed and unknown-only changes stay unclassified; semantic numeric equivalence, CSS, references, clipping and general rendered collision are not evaluated. Geometry changes do not prove a different composition or improved aesthetics.','baseline':safe(sources[0]),'candidates':[{'artifact':safe(s),'comparison':r} for s,r in zip(sources[1:],results)]}
    (out/'comparison.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=[]
    for i,s in enumerate(sources):
        label='Baseline' if i==0 else f'Candidate {i}'
        data=base64.b64encode(s['raw']).decode('ascii')
        cards.append(f'<section><h2>{label}: {html.escape(Path(s["path"]).name)}</h2><img alt="{label}" src="data:image/svg+xml;base64,{data}"><details><summary>Extracted labels</summary><pre>{html.escape(chr(10).join(s["texts"]))}</pre></details></section>')
    (out/'comparison.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Scientific figure comparison</title><style>body{font:16px system-ui;color:#202a33;margin:32px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:28px}section{min-width:0;border:1px solid #ddd;padding:20px}h2{font-size:18px}img{width:100%;height:auto}pre{white-space:pre-wrap}</style><h1>Scientific figure comparison</h1><p>Same science must be verified separately. Structural difference does not establish improvement.</p><main>'+''.join(cards)+'</main></html>',encoding='utf-8')
    return receipt
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,action='append',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    r=run(a.baseline,a.candidate,a.out)
    print(json.dumps({'status':r['status'],'changes':[c['comparison']['classification'] for c in r['candidates']]},ensure_ascii=False))
if __name__=='__main__':main()
