"""Run bounded T1–T8 acceptance and negative controls in a NEW directory."""
import argparse,copy,hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--cjk-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);a=p.parse_args()
    a.package=a.package.resolve();a.out=a.out.resolve()
    if a.out.exists():p.error('Test output must be new')
    a.out.mkdir(parents=True);sys.path.insert(0,str(a.package/'scripts'))
    from palette_tools import validate_library,recolor,semantic_payload,digest,contrast,composite,to_oklab,from_oklab,hx,encoded
    from figure_core import geometry_payload,validate_spec
    from check_figure import check,compare
    from make_examples import quantitative
    from probe_runtime import probe
    results=[];logs=[]
    def record(id,okay,detail):results.append({'id':id,'status':'PASS' if okay else 'FAIL','detail':detail})
    def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
    def run(args,env=None):
        cmd=[sys.executable,*map(str,args)];r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,env=env)
        logs.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
    def rejected(call):
        try:call();return False
        except (ValueError,KeyError):return True
    lib=load(a.package/'assets/reference_palettes.json');validation=validate_library(lib)
    bad=copy.deepcopy(lib);bad['palettes'][0]['colors'][0]['hex']='#000000';bad_result=validate_library(bad)
    record('T1',validation['count']==25 and validation['status']=='PASS' and bad_result['status']=='FAIL',{'good':validation,'bad':bad_result,'source_untouched':bad!=lib})
    record('color_math',abs(contrast('#FFFFFF','#000000')-21)<1e-9 and composite('#000000','#FFFFFF',.5)=='#808080' and abs(to_oklab('#FF0000')[0]-.627955)<1e-5,'Independent anchors: black/white 21:1, encoded-sRGB half alpha #808080, Oklab red L=0.627955')
    specs={'A':'mechanism/A.json','B':'mechanism/B.json','C':'mechanism/C.json','D':'mechanism/D.json','I4':'mechanism/I4.json','hardware':'hardware/registers.json','material':'material/section.json','quantitative':'quantitative/paired.json','labels-crowded':'labels/crowded.json','labels-repaired':'labels/repaired.json'}
    rendered={};source={}
    for id,rel in specs.items():
        source[id]=load(a.package/'examples'/rel);dest=a.out/'rendered'/id
        r=run([a.package/'scripts/render_figure.py',a.package/'examples'/rel,'--out',dest,'--font',a.font,'--cjk-font',a.cjk_font,'--pdftoppm',a.pdftoppm,'--qa-views'])
        if (dest/'manifest.json').is_file():rendered[id]=load(dest/'manifest.json')
        record('render_'+id,r.returncode==(1 if id=='labels-crowded' else 0),{'exit_code':r.returncode,'expected':1 if id=='labels-crowded' else 0,'output':str(dest)})
    if len(rendered)!=10:
        record('remaining_T2_T8',False,'Rendering incomplete; no fabricated continuation of checks')
    else:
        diff=compare(rendered['D'],rendered['I4']);record('T2',diff['status']=='PASS' and diff['palette_changed'],diff)
        s=source['hardware'];groups=[]
        for panel in range(3):
            cells=[x for x in s['items'] if x.get('cell_snapshot')==panel]
            groups.append({'total':len(cells),'occupied':sum(x['occupied'] for x in cells)})
        # Count named logical cells, never their decorative side faces.
        if groups[0]['total']==0:
            groups=[]
            for panel in range(3):
                cells=[x for x in s['items'] if x['id'].startswith(f'cell-{panel}-') and x['type']=='rect']
                groups.append({'total':len(cells),'occupied':sum(x.get('occupied',False) for x in cells)})
        record('T3',groups==[{'total':32,'occupied':19},{'total':32,'occupied':7},{'total':32,'occupied':28}],{'counted_cells':groups,'capacity_not_speedup':s['caption'],'locked':s['locked_values']})
        mat=source['material'];svg=ET.parse(a.out/'rendered/material/figure.svg');ns={'s':'http://www.w3.org/2000/svg'}
        cores=[x for x in mat['items'] if x['id'].startswith('core-') and x['type']=='circle' and not x.get('decorative_depth')]
        record('T4',len(cores)==6 and len(svg.findall('.//s:text',ns))>0 and len(svg.findall('.//s:image',ns))==0 and mat['depth']['mode'].startswith('D1_') and '2_5d' in mat['depth']['mode'],{'overview_cores':len(cores),'native_text_nodes':len(svg.findall('.//s:text',ns)),'embedded_raster':len(svg.findall('.//s:image',ns)),'depth_mode':mat['depth']['mode'],'occlusion':'Agent visual review required; this is not a geometry proof or D2'})
        q=source['quantitative'];d=q['data'];times=[(r['control_ms'],r['candidate_ms']) for r in d];changes=[round(r['change_percent'],8) for r in d]
        marks=[x for x in q['items'] if 'data_value' in x]
        record('T5',times==[(10.,8.),(10.,10.),(10.,12.)] and changes==[-20.,0.,20.] and len(marks)==6,{'times':times,'changes_percent':changes,'marks':len(marks),'source_sha256':q['data_sha256'],'uncertainty':'No uncertainty supplied or drawn'})
        b=check(a.out/'rendered/labels-crowded');g=check(a.out/'rendered/labels-repaired')
        old={x['id']:x for x in source['labels-crowded']['items'] if x['type']=='text'};new={x['id']:x for x in source['labels-repaired']['items'] if x['type']=='text'}
        preserved=all(old[k]['text'].replace('\n','')==new[k]['text'].replace('\n','') and old[k]['size']==new[k]['size'] for k in old)
        record('T6',b['status']=='FAIL' and g['status']=='PASS' and preserved,{'crowded_findings':b['findings'],'repaired_status':g['status'],'font_size_and_characters_preserved':preserved,'redundancy':'circle/square + direct text'})
        theme=load(a.package/'examples/mechanism/I4-theme.json');t=copy.deepcopy(theme);t['items']=[]
        record('T7',diff['status']=='PASS' and rejected(lambda:recolor(source['D'],t)) and source['D']['exact_labels']==source['I4']['exact_labels'],{'hash_compare':diff,'theme_geometry_injection':'REJECTED','actual_svg_bytes_differ':(a.out/'rendered/D/figure.svg').read_bytes()!=(a.out/'rendered/I4/figure.svg').read_bytes()})
        r=run([a.package/'scripts/check_figure.py',a.out/'rendered/I4','--compare',a.out/'rendered/D'])
        record('compare_exports',r.returncode==0,json.loads(r.stdout))
        env=dict(os.environ);env['PATH']='';r=run([a.package/'scripts/render_figure.py',a.package/'examples/mechanism/D.json','--out',a.out/'no-optional-runtime','--font',a.font,'--pdftoppm',a.out/'intentionally-absent.exe'],env)
        m=load(a.out/'no-optional-runtime/manifest.json') if (a.out/'no-optional-runtime/manifest.json').is_file() else {}
        capabilities=probe();record('T8',r.returncode==0 and m.get('raster',{}).get('status')=='NOT_RUN' and capabilities['optional_3d']['status']=='NOT_RUN' and capabilities['image_API']['status']=='NOT_RUN',{'PATH':'empty for actual core subprocess','core_exit':r.returncode,'raster':m.get('raster'),'D2':capabilities['optional_3d'],'image_API':capabilities['image_API']})
        sem=[digest(semantic_payload(source[x])) for x in 'ABCD'];ab=geometry_payload(source['A'])==geometry_payload(source['B'])
        c_no_depth=copy.deepcopy(source['C']);c_no_depth['items']=[x for x in c_no_depth['items'] if not x.get('decorative_depth')]
        bc=geometry_payload(c_no_depth)==geometry_payload(source['B'])
        record('design_ABCD',len(set(sem))==1 and ab and bc and geometry_payload(source['C'])!=geometry_payload(source['D']),{'same_content':len(set(sem))==1,'A_B_same_geometry':ab,'B_C_only_decorative_geometry_added':bc,'C_D_layout_changes':True,'user_study':'NOT_RUN'})
        # Content tampering, missing data, and false output success must be detected.
        wrong=copy.deepcopy(source['D']);wrong['relations'][0]['to']='not-an-entity'
        record('invalid_relation',rejected(lambda:validate_spec(wrong)),'Unknown relation endpoint rejected before export')
        short=copy.deepcopy(source['D']);short['items']=[x for x in short['items'] if x['id']!='round-0']
        record('missing_object',rejected(lambda:validate_spec(short)),'Deleting a declared counted object is rejected; arbitrary numeric prose is still not automatically proven')
        badcsv=a.out/'DEMO_zero.csv';badcsv.write_text('case,control_ms,candidate_ms\nZ,0,1\n',encoding='utf-8')
        missingcsv=a.out/'DEMO_missing.csv';missingcsv.write_text('case,control_ms,candidate_ms\nM,10,\n',encoding='utf-8')
        record('invalid_data',rejected(lambda:quantitative(badcsv)) and rejected(lambda:quantitative(missingcsv)),'Zero denominator and missing observation explicitly rejected; no silent filtering')
        r=run([a.package/'scripts/render_figure.py',a.package/'examples/mechanism/D.json','--out',a.out/'rendered/D','--font',a.font])
        record('overwrite_guard',r.returncode==2,'Existing output directory rejected')
        audit=a.package/'vendor/nature-figure/audit_pdf_text.py'
        r=run([audit,a.out/'rendered/material/figure.pdf','--min-pt','8','--json'])
        record('upstream_font_audit',r.returncode==0,json.loads(r.stdout) if r.returncode==0 else r.stderr)
        from reportlab import rl_config
        from reportlab.pdfgen import canvas
        rl_config.useA85=0;pdf=a.out/'DEMO_tiny_type.pdf';c=canvas.Canvas(str(pdf));c.setFont('Helvetica',5);c.drawString(50,50,'DEMO small text');c.save()
        r=run([audit,pdf,'--min-pt','8','--json']);record('upstream_font_negative_control',r.returncode==1,'5pt text must fail the explicitly selected 8pt floor')
    result={'status':'PASS' if all(x['status']=='PASS' for x in results) else 'FAIL','scope':'Executable bounded core tests; not author approval or generic scientific proof','tests':results,'author_acceptance':False,'visual_review':'REVIEW_REQUIRED','not_run':['D2 backend','external image API','Matplotlib','R','general PDF collisions','all CVD conditions','physical print','journal acceptance']}
    (a.out/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(a.out/'commands.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'tests':len(results),'failed':[x['id'] for x in results if x['status']=='FAIL'],'record':str(a.out/'acceptance.json')},ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
