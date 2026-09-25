"""Bounded checks of our manifest and exports; unknown geometry is never PASS."""
import argparse,json,math,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from semantic_audit import audit_semantics

def overlaps(a,b,margin=0):return min(a[2],b[2])-max(a[0],b[0])>margin and min(a[3],b[3])-max(a[1],b[1])>margin
def segment_rect(a,b,r):
    # Liang–Barsky clipping, with inset used by caller to ignore grazing edges.
    x,y=a;dx=b[0]-x;dy=b[1]-y;lo,hi=0.,1.
    for p,q in [(-dx,x-r[0]),(dx,r[2]-x),(-dy,y-r[1]),(dy,r[3]-y)]:
        if p==0:
            if q<0:return False
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
        if lo>hi:return False
    return True
def check(folder,placement_width_mm=None):
    folder=Path(folder);mp=folder/'manifest.json'
    if not mp.is_file():return {'status':'NOT_AUDITABLE','technical_status':'NOT_AUDITABLE','overall_status':'REVIEW_REQUIRED','reason':'Studio manifest not supplied; use actual SVG/PDF tooling and manual review'}
    m=json.loads(mp.read_text(encoding='utf-8'));findings=[]
    for name,sha in m['files'].items():
        p=folder/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:findings.append({'level':'FAIL','check':'export_hash','object':name})
    if findings:return {'status':'FAIL','technical_status':'FAIL','overall_status':'FAIL','findings':findings,'author_acceptance':False}
    svg=ET.parse(folder/'figure.svg').getroot();ns={'s':'http://www.w3.org/2000/svg'}
    svg_ids=[g.get('id') for g in svg.findall('s:g',ns)]
    if sorted(svg_ids)!=sorted(o['id'] for o in m['objects']):findings.append({'level':'FAIL','check':'export_object_set'})
    for rule in m.get('count_constraints',[]):
        if 'item_ids' in rule and (len(rule['item_ids'])!=rule['expected'] or any(svg_ids.count(id)!=1 for id in rule['item_ids'])):findings.append({'level':'FAIL','check':'declared_object_count','object':rule['name']})
    spec_path=folder/'figure_spec.json'
    semantic=audit_semantics(json.loads(spec_path.read_text(encoding='utf-8'))) if spec_path.is_file() else {
        'status':'REVIEW_REQUIRED','findings':[{'level':'REVIEW_REQUIRED','check':'scene_spec_absent'}], 'object_counts':[], 'directed_relations':[]}
    findings.extend(f for f in semantic['findings'] if f['level']=='FAIL')
    if svg.findall('.//s:image',ns):findings.append({'level':'REVIEW_REQUIRED','check':'embedded_raster'})
    text=m['objects'];texts=[x for x in text if x['type']=='text'];w=m['view_width'];h=m['view_height']
    placement=placement_width_mm if placement_width_mm is not None else m.get('placement_width_mm')
    if placement is not None and (not isinstance(placement,(int,float)) or not math.isfinite(placement) or placement<=0):raise ValueError('Placement width must be a finite positive millimetre value')
    placed_fonts=[]
    for o in text:
        b=o['bounds']
        if b and (b[0]<-.1 or b[1]<-.1 or b[2]>w+.1 or b[3]>h+.1):findings.append({'level':'FAIL','check':'page_bounds','object':o['id']})
        if o['type']=='text':
            if o['font_pt']<8:findings.append({'level':'FAIL','check':'draft_font_floor_8pt','object':o['id'],'pt':o['font_pt']})
            if placement is not None:
                placed_pt=o['font_pt']*placement/m['width_mm'];placed_fonts.append(placed_pt)
                if placed_pt<8:findings.append({'level':'FAIL','check':'placement_font_floor_8pt','object':o['id'],'pt':placed_pt,'placement_width_mm':placement})
            if o['contrast']<4.5:findings.append({'level':'FAIL','check':'declared_background_text_contrast','object':o['id'],'ratio':o['contrast']})
            if o.get('max_width') and any(b[2]-b[0]>o['max_width']+.1 for b in o['line_bounds']):findings.append({'level':'FAIL','check':'label_slot','object':o['id']})
    for i,a in enumerate(texts):
        for b in texts[i+1:]:
            if any(overlaps(x,y,1) for x in a['line_bounds'] for y in b['line_bounds']):findings.append({'level':'FAIL','check':'text_text','objects':[a['id'],b['id']]})
    for line in m['relation_segments']:
        for t in texts:
            for box in t['line_bounds']:
                r=[box[0]+2,box[1]+2,box[2]-2,box[3]-2]
                if segment_rect(line['from'],line['to'],r):findings.append({'level':'FAIL','check':'straight_relation_text','objects':[line['id'],t['id']]});break
    try:
        pdf_start=len(findings)
        pdf=PdfReader(folder/'figure.pdf');page=pdf.pages[0]
        actual=[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72]
        if len(pdf.pages)!=1 or any(abs(a-b)>.02 for a,b in zip(actual,[m['width_mm'],m['height_mm']])):findings.append({'level':'FAIL','check':'PDF_dimensions','actual_mm':actual})
        if not page.extract_text().strip():findings.append({'level':'FAIL','check':'PDF_searchable_text'})
        pdfstatus='FAIL' if len(findings)>pdf_start else 'PASS'
    except Exception as e:pdfstatus='NOT_AUDITABLE';findings.append({'level':'REVIEW_REQUIRED','check':'PDF_parse','reason':str(e)})
    raster=m.get('raster',{}).get('status','NOT_RUN')
    if raster=='FAIL':findings.append({'level':'FAIL','check':'raster_export'})
    technical='FAIL' if any(x['level']=='FAIL' for x in findings) else 'REVIEW_REQUIRED' if findings else 'PASS'
    countstatus='FAIL' if any(x['check']=='declared_object_count' for x in findings) or any(x['status']=='FAIL' for x in semantic['object_counts']) else 'REVIEW_REQUIRED' if not semantic['object_counts'] or any(x['status']!='PASS' for x in semantic['object_counts']) else 'PASS'
    relationstatus='FAIL' if any(x['status']=='FAIL' for x in semantic['directed_relations']) else 'REVIEW_REQUIRED' if any(x['status']!='PASS' for x in semantic['directed_relations']) else 'PASS' if semantic['directed_relations'] else 'NOT_APPLICABLE'
    placementstatus='FAIL' if any(x['check']=='placement_font_floor_8pt' for x in findings) else 'PASS' if placement is not None and placed_fonts else 'REVIEW_REQUIRED'
    return {'status':technical,'status_meaning':'Backward-compatible alias of technical_status; use overall_status for readiness',
      'technical_status':technical,'scientific_review_status':'REVIEW_REQUIRED','visual_review_status':'REVIEW_REQUIRED',
      'overall_status':'FAIL' if technical=='FAIL' or semantic['status']=='FAIL' else 'REVIEW_REQUIRED',
      'scope':'Exact export hashes; emitted-object geometry and font metrics, declared-background contrast, PDF dimensions/text. Not a general rendered collision detector.',
      'figure_id':m['figure_id'],'findings':findings,'semantic_constraints':semantic,
      'placement':{'status':placementstatus,'width_mm':placement,'minimum_font_pt':min(placed_fonts) if placed_fonts else None,'scope':'Declared scaled font sizes; inspect actual document pages for embedding effects'},
      'checks':{'glyph_coverage':'PASS' if all(t.get('glyph_check')=='PASS' for t in texts) else 'REVIEW_REQUIRED','SVG_parse':'PASS','PDF':pdfstatus,
      'declared_object_counts':countstatus,'directed_relations':relationstatus,'placement_size':placementstatus,'raster_export':raster,
      'curved_path_collisions':'NOT_AUDITABLE','generic_PDF_collisions':'NOT_RUN','scientific_meaning':'REVIEW_REQUIRED','visual_quality':'REVIEW_REQUIRED',
      'physical_print_or_all_displays':'NOT_RUN'},'author_acceptance':False}
def compare(a,b):
    result={k:a[k]==b[k] for k in ('semantic_digest','geometry_digest')}
    return {'status':'PASS' if all(result.values()) else 'FAIL','scope':'Color-only invariants','invariants':result,
      'palette_changed':a['roles']!=b['roles'],'source_spec_sha256':a['spec_sha256'],'target_spec_sha256':b['spec_sha256']}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--compare',type=Path);p.add_argument('--out',type=Path);p.add_argument('--placement-width-mm',type=float);a=p.parse_args()
    try:
        if a.compare:
            audits=[check(a.compare,a.placement_width_mm),check(a.folder,a.placement_width_mm)]
            result=compare(json.loads((a.compare/'manifest.json').read_text(encoding='utf-8')),json.loads((a.folder/'manifest.json').read_text(encoding='utf-8')))
            result['export_checks']=[q['status'] for q in audits]
            if any(q['status']!='PASS' for q in audits):result['status']='FAIL';result['details']=audits
        else:result=check(a.folder,a.placement_width_mm)
        if a.out:
            if a.out.exists():raise ValueError('QA output already exists')
            a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2));return {'PASS':0,'FAIL':1}.get(result['status'],2)
    except (OSError,ValueError,KeyError,ET.ParseError) as e:
        print(json.dumps({'status':'NOT_AUDITABLE','reason':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
