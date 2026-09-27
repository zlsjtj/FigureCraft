"""Run the documented source/build/render/check chain, never committed exports."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    for n in ['font','pdftoppm']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);root=Path(__file__).resolve().parents[1];rows=[];py=[sys.executable,'-B','-X','utf8']
    cmds=[['generate',root/'examples/material-polished-v17/build_material_v17.py','--out',a.out/'source']]
    for variant in ['A','B']:
        cmds.extend([[f'render-{variant}',root/'scripts/render_figure.py',a.out/f'source/scene_{variant}.json','--out',a.out/variant,'--font',a.font,'--pdftoppm',a.pdftoppm,'--qa-views'],[f'check-{variant}',root/'scripts/check_figure.py',a.out/variant,'--placement-width-mm','160']])
    for name,*args in cmds:
        cmd=py+list(map(str,args));r=subprocess.run(cmd,cwd=a.out,capture_output=True,text=True,encoding='utf8',errors='replace');rows.append({'name':name,'command':cmd,'status':'PASS' if r.returncode==0 else 'MISSING_DEPENDENCY' if 'ModuleNotFoundError' in r.stderr else 'FAIL','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    exports={f.relative_to(a.out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in a.out.rglob('*') if f.suffix in ['.svg','.pdf','.png']}
    status='PASS' if all(r['status']=='PASS' for r in rows) and all((a.out/v/'figure.svg').is_file() for v in ['A','B']) else 'FAIL'
    data={'status':status,'count':len(rows),'tests':rows,'fresh_exports':exports,'visual_review':'NOT_RUN_BY_SCRIPT'};(a.out/'results.json').write_text(json.dumps(data,indent=2),encoding='utf8');return int(status!='PASS')
if __name__=='__main__':raise SystemExit(main())
