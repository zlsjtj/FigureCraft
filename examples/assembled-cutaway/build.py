"""Rebuild the selected editable cutaway; historical failures are optional."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--skill',type=Path,default=Path(__file__).resolve().parents[2])
p.add_argument('--out',type=Path,required=True)
p.add_argument('--font',type=Path,required=True)
p.add_argument('--pdftoppm',type=Path,required=True)
p.add_argument('--include-rejected',action='store_true',help='Also rebuild first/alternative, both known to contain scientific depiction errors.')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
here=Path(__file__).resolve().parent
subprocess.run([sys.executable,'-X','utf8','-B',str(here/'author_interface.py'),'--skill',str(a.skill),'--out',str(a.out/'selected.json')],check=True)
source=here/'input/implementation.md'
spec=json.loads((a.out/'selected.json').read_text(encoding='utf-8'))
spec['source_refs']=[{'description':'Original synthetic fixture material','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]
(a.out/'selected.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
for name in (['selected','first','alternative'] if a.include_rejected else ['selected']):
    scene=a.out/'selected.json' if name=='selected' else here/'scenes'/f'{name}.json'
    subprocess.run([sys.executable,'-X','utf8','-B',str(a.skill/'scripts/render_figure.py'),str(scene),'--out',str(a.out/name),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--qa-views'],check=True)
(a.out/'scope.json').write_text(json.dumps({'selected':'selected','historical_rejected_included':a.include_rejected,'fixed_source_rebuild':True,'new_language_generation':False},indent=2),encoding='utf-8')
