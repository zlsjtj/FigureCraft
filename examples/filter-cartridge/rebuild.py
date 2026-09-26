"""Rebuild the packaged final figure from a verified source into a new directory."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--skill-root',type=Path,required=True)
p.add_argument('--font',type=Path,required=True)
p.add_argument('--pdftoppm',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();here=Path(__file__).resolve().parent
specfile=here/'figure_spec.json'
if a.out.exists():raise SystemExit('Refuse to overwrite output')
s=json.loads(specfile.read_text(encoding='utf-8'))
for source in s['source_refs']:
    path=here/source['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
        raise SystemExit('Source content hash differs: '+str(path))
cmd=[sys.executable,str(a.skill_root/'scripts/render_figure.py'),str(specfile),'--out',str(a.out),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--qa-views','--placement-width-mm','160']
r=subprocess.run(cmd);raise SystemExit(r.returncode)
