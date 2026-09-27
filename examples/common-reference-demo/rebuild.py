"""Rebuild the frozen teaching scene with explicit runtime paths."""
from pathlib import Path
import argparse,subprocess,sys
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--skill-dir',type=Path,default=root.parents[1]);p.add_argument('--font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True);a=p.parse_args()
subprocess.run([sys.executable,'-B','-X','utf8',str(a.skill_dir/'scripts/render_figure.py'),str(root/'figure_spec.json'),'--out',str(a.out),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--dpi','300','--qa-views'],check=True)
