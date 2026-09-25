"""Run the eight real suites in a new directory with explicit local runtimes."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    for n in ('font','cjk-font','pdftoppm'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);root=Path(__file__).resolve().parents[1]
    common=['--package',str(root),'--font',str(a.font),'--cjk-font',str(a.cjk_font),'--pdftoppm',str(a.pdftoppm)]
    cases=[('core','run_acceptance.py',common,'acceptance.json'),('semantic','run_semantic_acceptance.py',common,'acceptance.json'),
           ('comparison','run_comparison_tests.py',[],'results.json'),('scene-api','run_scene_api_tests.py',['--font',str(a.font),'--pdftoppm',str(a.pdftoppm)],'results.json'),
           ('components','run_component_tests.py',[],'results.json'),('surfaces','run_surface_tests.py',['--font',str(a.font)],'results.json'),
           ('slices','run_slice_tests.py',['--font',str(a.font)],'results.json'),('openings','run_opening_tests.py',[],'results.json')]
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    before={str(f.relative_to(root)):sha(f) for folder in ('scripts','tests') for f in (root/folder).glob('*.py')}
    rows=[]
    for name,script,extra,result in cases:
        cmd=[sys.executable,'-B','-X','utf8',str(root/'tests'/script),'--out',str(a.out/name),*extra]
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        row=dict(suite=name,command=cmd,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,script_sha256=sha(root/'tests'/script))
        rp=a.out/name/result
        if rp.is_file():
            data=json.loads(rp.read_text(encoding='utf-8'));row.update(result=result,result_sha256=sha(rp),count=data.get('count',data.get('total',len(data.get('tests',[])))))
        else:row.update(result=None,count=0)
        rows.append(row)
    after={str(f.relative_to(root)):sha(f) for folder in ('scripts','tests') for f in (root/folder).glob('*.py')}
    record={'status':'PASS' if all(r['exit_code']==0 for r in rows) and before==after else 'FAIL',
            'total':sum(r['count'] for r in rows),'version':'1.7.0','source_unchanged':before==after,
            'source_hashes':before,'suites':rows,'effect_review':'NOT_TESTED_BY_SUITES','author_acceptance':'PENDING'}
    (a.out/'test-summary.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'status':record['status'],'total':record['total'],'source_unchanged':record['source_unchanged']}));return int(record['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
