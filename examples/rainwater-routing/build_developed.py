"""Development repair: category-recognition contours versus saved abstract nodes.

Uses exactly the established DEMO topology and three-policy data. Roof/tank
contours identify categories, not measured geometry or liquid quantities.
"""
import argparse,copy,csv,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    example_root=Path(__file__).resolve().parent
    p.add_argument('--baseline',type=Path,default=example_root/'baseline_spec.json')
    p.add_argument('--input',type=Path,default=example_root/'input')
    for name in ['skill','out','font','pdftoppm']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--opaque-exterior',action='store_true')
    a=p.parse_args()
    if a.out.exists():raise SystemExit('Refuse overwrite')
    a.out.mkdir(parents=True)
    s=json.loads(a.baseline.read_text(encoding='utf-8'))
    rows=list(csv.DictReader((a.input/'interval_results.csv').open(encoding='utf-8-sig')))
    assert len(rows)==24
    policies=['FIXED_THIRD','DELAYED_TENTH','FIXED_TENTH']
    assert [round(sum(float(r['spill_l']) for r in rows if r['policy']==policy)) for policy in policies]==[28,7,2]
    s['figure_id']='rainwater_object_development'
    s['development_status']='DEVELOPMENT_REPAIR_AFTER_INITIAL_DELIVERY; not an independent first pass'
    s['development_parent']={'file':'baseline_spec.json','sha256':sha(a.baseline)}
    s['depth']={'mode':'D1_category_contours_and_D0_quantities','affects_quantitative_encoding':False}
    s['layout']['archetype']='recognizable_source_and_storage_contours_above_unchanged_comparison'
    s['geometry_contract']={'recognition_only':['roof silhouettes','tank cylindrical silhouettes','subtle surface shading'],
      'scientific_boundaries':['three distinct source branches','one diverter','two separate tanks','no intertank connection','complementary central fractions'],
      'quantitative_encoding':['zero-based spill bars','explicit capacities/initial volumes','explicit final free volumes'],
      'not_encoded':['roof area or slope','tank dimensions or cross-section','liquid surface height','pipe dimensions','physical installation layout']}
    s['source_reference_base']='example_root'
    s['source_refs']=[{'path':'input/'+n,'sha256':sha(a.input/n)} for n in ['README_DEMO.md','rough_paragraphs_v0.md','routing_and_operation_record.md','interval_results.csv','construct_transfer.py']]
    s['data_sha256']=sha(a.input/'interval_results.csv')
    (a.out/'interval_results.csv').write_bytes((a.input/'interval_results.csv').read_bytes())
    old={x['id']:x for x in s['items']}
    # Preserve the quantitative panel byte-for-byte in its scene representation.
    result_ids=[x['id'] for x in s['items'] if x['id'] in ['panel-divider','panel-b','schedule-head','spill-head','free-head','free-subhead','bound'] or x['id'].startswith(('grid-','tick-','policy-','alpha-','bar-','spill-value-','headroom-'))]
    result_before={k:copy.deepcopy(old[k]) for k in result_ids}
    remove={f'roof-{k}' for k in 'ABC'}|{f'roof-name-{k}' for k in 'ABC'}|{f'roof-flow-{k}' for k in 'ABC'}|{'tank-W','tank-E'}
    s['items']=[x for x in s['items'] if x['id'] not in remove]
    new=[]
    for k,cx,rate in [('A',130,20),('B',450,30),('C',770,10)]:
        # The shared roof ridge joins two simple planes; no walls, fixtures,
        # gutters or roof-area scale are introduced.
        ox=cx-130
        left=[[25+ox,118],[80+ox,80],[112+ox,65],[57+ox,103]]
        right=[[80+ox,80],[130+ox,124],[162+ox,109],[112+ox,65]]
        common={'entity':k,'logical_id':k,'role':'source','stroke':'#718690','stroke_width':1.6}
        new.append(dict(id='roof-'+k,type='polygon',points=left,fill='#CDDCE2',object_part='primary',**common))
        new.append(dict(id='roof-'+k+'-second-face',type='polygon',points=right,fill='#E8F0F3',object_part='decoration',**common))
        new.append(dict(id='roof-name-'+k,type='text',text=f'Roof {k} · {rate} L/min',x=cx-30,y=56,size=18,align='center',fill='#243B46',background='#FFFFFF',entity=k,logical_id=k,object_part='decoration'))
    for k,cx,color,pale in [('W',205,'#347FA8','#E1F1F8'),('E',695,'#967019','#FAF1D9')]:
        left,right=cx-120,cx+120;role='west' if k=='W' else 'east'
        body=[['M',left,200],['L',left,260],['C',left,279,right,279,right,260],['L',right,200],['Z']]
        common={'entity':k,'logical_id':k,'role':role,'stroke':color,'stroke_width':2}
        new.append(dict(id='tank-'+k,type='path',commands=body,fill=pale,object_part='primary',
          fill_gradient={'kind':'linear','x1':left,'y1':230,'x2':right,'y2':230,'stops':[[0,pale],[.30,'#FFFFFF'],[1,pale]]},**common))
        top_fill='#EDF2F4' if a.opaque_exterior else pale
        new.append(dict(id='tank-'+k+'-top',type='ellipse',x=cx,y=200,rx=120,ry=12,fill=top_fill,object_part='decoration',**common))
    # Place the recognition contours behind the existing names and connections.
    s['items'][1:1]=new
    # Bind flow endpoints to the new exterior contours. No new flow is added.
    sys.path.insert(0,str(a.skill/'scripts'))
    from relation_components import relation_path
    replacements={
      'A-W':[[130,124],[130,191]],'C-E':[[770,124],[770,191]],'B-D':[[450,124],[450,135]],
      'D-W':[[436,149],[280,149],[280,191]],'D-E':[[464,149],[620,149],[620,191]],
      'W-load':[[140,272],[140,291]],'W-spill':[[290,272],[290,291]],
      'E-load':[[640,272],[640,291]],'E-spill':[[790,272],[790,291]]}
    for rid,pts in replacements.items():
        rel=next(r for r in s['relations'] if r['id']==rid)
        color=old[rid+'-line']['stroke']
        # Keep existing labels; rebuild only the explicit endpoint/arrow geometry.
        comp=relation_path(rid,semantics='data_flow',points=pts,source_entity=rel['from'],target_entity=rel['to'],meaning=rel['meaning'],color=color,width=2.3,head=8,role='relation')
        s['items']=[x for x in s['items'] if x['id'] not in [rid+'-line',rid+'-head']]
        s['items'].extend(comp['items'])
        s['relations']=[r for r in s['relations'] if r['id']!=rid]+comp['relations']
    for x in s['items']:
        if x['id'].startswith('tank-name-'):x['y']=232
        if x['id'].startswith('tank-volume-'):x['y']=256
    s['caption']='Figure 1. Constructed DEMO of routing-limited rainwater storage. (a) Roof and tank silhouettes identify object categories; their geometry is schematic and does not encode capacity or water level. Exactly three roof branches feed two separate tanks. The single central supply splits into complementary fractions. Tank labels give initial volume / capacity; each tank has its own continuous load and spill drain. (b) The same three independently initialized schedules are compared over four minutes. Bars show total spill and identify the spilling tank in parentheses; the right column shows each tank\'s remaining capacity. Fixed tenth attains the 2 L bound from 72 L net addition and 70 L initial free space. All values are invented; no field measurements or forecast uncertainty are represented.'
    s['alt_text']='Three recognizable roof silhouettes feed one diverter and two distinct storage-tank silhouettes. The central branch remains a single source with complementary splits. All three four-minute spill outcomes and tank-specific free volumes are preserved: 28 L/26 L, 7 L/5 L, and 2 L/0 L. Only generic object recognition uses shallow depth; quantities use explicit numbers and flat bars.'
    s['exact_labels']=[x['text'] for x in s['items'] if x['type']=='text']
    finalitems={x['id']:x for x in s['items']}
    assert all(result_before[k]==finalitems[k] for k in result_ids)
    s['development_checks']={'all_quantitative_panel_items_unchanged':True,'source_rows':24,'relation_count':len(s['relations']),'new_scientific_relations':0,'new_physical_geometry_claims':0,'opaque_neutral_exterior_top':a.opaque_exterior}
    (a.out/'figure_spec.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.out/'caption.md').write_text(s['caption']+'\n',encoding='utf-8')
    (a.out/'alt_text.md').write_text(s['alt_text']+'\n',encoding='utf-8')
    (a.out/'development_checks.json').write_text(json.dumps(s['development_checks'],indent=2),encoding='utf-8')
    command=[sys.executable,'-B',str(a.skill/'scripts'/'render_figure.py'),str(a.out/'figure_spec.json'),'--out',str(a.out/'rendered'),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--placement-width-mm','160','--qa-views']
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
    # Public receipts preserve logical commands/results, not workstation paths.
    aliases=[(str(a.skill.resolve()),'<FigureCraft>'),(str(a.font.resolve()),'<font>'),(str(a.pdftoppm.resolve()),'<pdftoppm>'),(str(a.out.resolve()),'<output>'),(str(a.input.resolve()),'<input>'),(str(a.baseline.resolve()),'<baseline>'),(str(Path(sys.executable).resolve()),'<python>')]
    def public_paths(value):
        if isinstance(value,dict):return {k:public_paths(v) for k,v in value.items()}
        if isinstance(value,list):return [public_paths(v) for v in value]
        if isinstance(value,str):
            for real,alias in aliases:value=value.replace(real,alias).replace(real.replace('\\','/'),alias)
        return value
    for name in ['manifest.json']:
        path=a.out/'rendered'/name
        if path.exists():path.write_text(json.dumps(public_paths(json.loads(path.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2),encoding='utf-8')
    try:result=public_paths(json.loads(run.stdout.strip()))
    except (ValueError,TypeError):result={'stdout_redacted':public_paths(run.stdout)}
    (a.out/'invocation.json').write_text(json.dumps({'command':['python','-B','<FigureCraft>/scripts/render_figure.py','<output>/figure_spec.json','--out','<output>/rendered','--font','<font>','--pdftoppm','<pdftoppm>','--placement-width-mm','160','--qa-views'],'exit_code':run.returncode,'result':result,'stderr':public_paths(run.stderr),'source_sha256':sha(__file__),'packaging_only':True},indent=2),encoding='utf-8')
    print(run.stdout);print(run.stderr);raise SystemExit(run.returncode)
if __name__=='__main__':main()
