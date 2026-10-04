"""Re-render a retained exact scene without recreating an earlier authoring turn."""
import argparse, json
from pathlib import Path
import drawing_backend as d
p=argparse.ArgumentParser()
p.add_argument('scene',type=Path)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--font',required=True)
p.add_argument('--bold-font',required=True)
p.add_argument('--pdftoppm',required=True)
a=p.parse_args()
if a.out.exists():raise SystemExit('Choose a new output path.')
d.configure(a.font,a.bold_font,a.pdftoppm)
s=d.Scene('retained')
s.items=json.loads(a.scene.read_text(encoding='utf-8'))['items']
d.render(s,a.out)
