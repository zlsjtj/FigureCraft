"""从冻结场景重建三种候选；不是又一次自然语言生成试验。"""
from pathlib import Path
import argparse,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--skill',type=Path,default=Path(__file__).resolve().parents[2])
p.add_argument('--font',type=Path,required=True)
p.add_argument('--pdftoppm',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--selected-only',action='store_true')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
for name in (['selected'] if a.selected_only else ['first','alternative','selected']):
 subprocess.run([sys.executable,'-X','utf8','-B',str(a.skill/'scripts/render_figure.py'),str(Path(__file__).resolve().parent/'scenes'/f'{name}.json'),'--out',str(a.out/name),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--qa-views'],check=True)
