"""Regression for 1.1 semantic constraints, placement and honest status reporting."""
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('package','out','font','cjk-font','pdftoppm'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.package=a.package.resolve();a.out=a.out.resolve()
    if a.out.exists():p.error('Test output must be new')
    a.out.mkdir(parents=True);sys.path.insert(0,str(a.package/'scripts'))
    from semantic_audit import audit_semantics
    from check_figure import check,compare
    from figure_core import validate_spec
    from pypdf import PdfReader,PdfWriter
    results=[];commands=[]
    def record(name,ok,detail):results.append({'id':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    def run(arguments):
        cmd=[sys.executable,*map(str,arguments)]
        r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        commands.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
    base=json.loads((a.package/'templates/semantic_scene.json').read_text(encoding='utf-8'))
    def render(name,spec,font=None,raster=None,extra=()):
        source=a.out/(name+'.json');write(source,spec);dest=a.out/name
        r=run([a.package/'scripts/render_figure.py',source,'--out',dest,'--font',font or a.font,
               '--cjk-font',a.cjk_font,'--pdftoppm',raster or a.pdftoppm,'--qa-views',*extra]);return r,dest
    r,good=render('good',base)
    qa=check(good)
    record('valid_semantic_scene',r.returncode==0 and qa['technical_status']=='PASS' and qa['checks']['declared_object_counts']=='PASS' and qa['checks']['directed_relations']=='PASS',qa)
    record('separate_review_status',qa['overall_status']=='REVIEW_REQUIRED' and qa['scientific_review_status']=='REVIEW_REQUIRED' and qa['visual_review_status']=='REVIEW_REQUIRED' and not qa['author_acceptance'],'Technical PASS does not claim scientific/visual/author acceptance')
    record('placement_160mm',qa['placement']['status']=='PASS' and qa['placement']['width_mm']==160 and qa['placement']['minimum_font_pt']>=8,qa['placement'])
    def negative(name,mutate,expected):
        spec=copy.deepcopy(base);mutate(spec);r,dest=render(name,spec)
        record(name,r.returncode==2 and expected in r.stderr and not (dest/'figure.svg').exists(),{'exit_code':r.returncode,'expected_check':expected,'stderr':r.stderr})
    def extra(s):
        cell=copy.deepcopy(next(x for x in s['items'] if x['id']=='cell-source'));cell.update(id='cell-extra',logical_id='extra-cell');s['items'].append(cell)
    negative('extra_object',extra,'logical_object_set')
    negative('missing_object',lambda s:s.update(items=[x for x in s['items'] if x['id']!='cell-target']),'logical_object_set')
    negative('wrong_occupancy',lambda s:next(x for x in s['items'] if x['id']=='cell-source').update(occupied=False),'logical_state')
    negative('wrong_occupancy_visual',lambda s:next(x for x in s['items'] if x['id']=='cell-source').update(fill='#FFFFFF'),'state_visual_encoding')
    negative('reversed_relation',lambda s:next(x for x in s['items'] if x['id']=='transfer-line')['points'].reverse(),'directed_relation_endpoints')
    negative('reversed_arrow',lambda s:next(x for x in s['items'] if x['id']=='transfer-head').update(points=[[463,165],[480,157],[480,173]]),'arrow_direction_or_geometry')
    def duplicated_primary(s):
        cell=copy.deepcopy(next(x for x in s['items'] if x['id']=='cell-source'));cell['id']='cell-copy';s['items'].append(cell)
    negative('duplicate_primary',duplicated_primary,'duplicate_logical_primary')
    mixed=copy.deepcopy(base)
    mixed['items'].extend([
        {'id':'cell-detail','type':'rect','x':100,'y':120,'w':20,'h':20,'fill':'@storage.fill','logical_id':'source-cell','object_part':'detail'},
        {'id':'cell-legend','type':'rect','x':60,'y':120,'w':20,'h':20,'fill':'@storage.fill','object_part':'legend'}])
    r,dest=render('detail-and-legend',mixed)
    record('decoration_detail_legend_excluded',r.returncode==0 and check(dest)['checks']['declared_object_counts']=='PASS','One source side, repeated source detail and legend do not create storage cells')
    r,small=render('too-small-placement',base,extra=('--placement-width-mm','90'))
    q=check(small);record('small_placement_rejected',r.returncode==1 and q['placement']['status']=='FAIL' and q['technical_status']=='FAIL',q['placement'])
    legacy=json.loads((a.package/'examples/mechanism/D.json').read_text(encoding='utf-8'))
    r,dest=render('legacy',legacy);q=check(dest)
    record('legacy_render_pending_semantics',r.returncode==0 and q['overall_status']=='REVIEW_REQUIRED' and q['checks']['declared_object_counts']=='REVIEW_REQUIRED',{'technical_status':q['technical_status'],'count_check':q['checks']['declared_object_counts'],'overall_status':q['overall_status']})
    corrupt=copy.deepcopy(base);corrupt['relations'][0].pop('geometry');r,dest=render('unknown-relation',corrupt);q=check(dest)
    record('unknown_relation_pending',r.returncode==0 and q['checks']['directed_relations']=='REVIEW_REQUIRED',q['semantic_constraints'])
    changed=copy.deepcopy(base);next(x for x in changed['items'] if x['id']=='source-label')['x']+=10
    r,dest=render('out-of-scope-recolor',changed)
    diff=compare(json.loads((good/'manifest.json').read_text()),json.loads((dest/'manifest.json').read_text()))
    record('recolor_geometry_change_rejected',r.returncode==0 and diff['status']=='FAIL' and not diff['invariants']['geometry_digest'],diff)
    absent=copy.deepcopy(base);absent.update(data_source='absent.csv',data_sha256='0'*64);r,dest=render('missing-data',absent)
    record('missing_data_rejected',r.returncode==2 and 'Source-data file absent' in r.stderr and not dest.exists(),{'exit_code':r.returncode,'stderr':r.stderr})
    r,dest=render('missing-font',base,font=a.out/'missing.ttf')
    record('missing_required_dependency_rejected',r.returncode==2 and 'Font missing' in r.stderr and not dest.exists(),{'exit_code':r.returncode,'stderr':r.stderr})
    r,dest=render('missing-raster',base,raster=a.out/'missing.exe');q=check(dest)
    record('missing_optional_dependency_not_run',r.returncode==0 and q['checks']['raster_export']=='NOT_RUN' and q['overall_status']=='REVIEW_REQUIRED',q['checks'])
    r,pdfbad=render('pdf-dimension-failure',base)
    pdf=PdfReader(pdfbad/'figure.pdf');pdf.pages[0].mediabox.upper_right=(100,100);writer=PdfWriter();writer.add_page(pdf.pages[0]);writer.write(pdfbad/'figure.pdf')
    manifest=json.loads((pdfbad/'manifest.json').read_text());manifest['files']['figure.pdf']=hashlib.sha256((pdfbad/'figure.pdf').read_bytes()).hexdigest();write(pdfbad/'manifest.json',manifest)
    q=check(pdfbad);record('PDF_child_failure_propagates',q['checks']['PDF']=='FAIL' and q['technical_status']=='FAIL' and q['overall_status']=='FAIL',{'checks':q['checks'],'overall':q['overall_status']})
    r,countbad=render('count-failure-status',base)
    spec=json.loads((countbad/'figure_spec.json').read_text());spec['count_constraints'][0]['expected_logical_ids'].append('absent');spec['count_constraints'][0]['expected']=3
    write(countbad/'figure_spec.json',spec);manifest=json.loads((countbad/'manifest.json').read_text());manifest['files']['figure_spec.json']=hashlib.sha256((countbad/'figure_spec.json').read_bytes()).hexdigest();write(countbad/'manifest.json',manifest)
    q=check(countbad);record('count_child_failure_propagates',q['checks']['declared_object_counts']=='FAIL' and q['technical_status']=='FAIL' and q['overall_status']=='FAIL',{'count_status':q['checks']['declared_object_counts'],'overall':q['overall_status']})
    status='PASS' if all(x['status']=='PASS' for x in results) else 'FAIL'
    write(a.out/'acceptance.json',{'version':'1.1.0','status':status,'tests':results,'scope':'Actual subprocess exports plus bounded negative controls; scientific and visual reviews remain separate','author_acceptance':False})
    write(a.out/'commands.json',commands)
    print(json.dumps({'status':status,'tests':len(results),'failed':[x['id'] for x in results if x['status']=='FAIL'],'record':str(a.out/'acceptance.json')}))
    return 0 if status=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
