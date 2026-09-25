"""Actual export regression for custom Scene text color and line width."""
from pathlib import Path
import argparse,json,subprocess,sys,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from make_examples import Scene
def run(out,font,pdftoppm):
    out.mkdir(parents=True,exist_ok=False)
    s=Scene('scene-api-regression','DEMO of editable drawing API; no research result',height=180)
    s.text('label','Custom color',40,70,size=24,fill='#123456')
    s.line('custom-line',[[40,110],[400,110]],stroke='#345678',stroke_width=3)
    s.finish(out/'input.json')
    cmd=[sys.executable,str(ROOT/'scripts/render_figure.py'),str(out/'input.json'),'--out',str(out/'rendered'),'--font',str(font),'--pdftoppm',str(pdftoppm)]
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
    receipt={'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    (out/'command.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    if p.returncode:raise RuntimeError(receipt)
    root=E.fromstring((out/'rendered/figure.svg').read_bytes())
    color=any(e.tag.endswith('}text') and ''.join(e.itertext())=='Custom color' and e.get('fill','').upper()=='#123456' for e in root.iter())
    width=any(e.get('stroke','').upper()=='#345678' and float(e.get('stroke-width','0'))==3 for e in root.iter())
    rows=[{'case':'custom_text_fill_survives_vector_export','status':'PASS' if color else 'FAIL'},{'case':'custom_line_width_survives_vector_export','status':'PASS' if width else 'FAIL'}]
    data={'passed':sum(x['status']=='PASS' for x in rows),'total':2,'results':rows,'scope':'Two reproduced API argument-collision regressions, not scientific or visual certification'}
    (out/'results.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data));return data['passed']==2
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True);a=ap.parse_args();raise SystemExit(0 if run(a.out,a.font,a.pdftoppm) else 1)
