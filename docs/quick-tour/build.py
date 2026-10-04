"""从公开文件重新导出导览画面与 32 秒 GIF；不是技能生成效果测试。"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser', required=True, help='Chrome / Chromium 可执行文件')
parser.add_argument('--node', default='node', help='Node 可执行文件')
parser.add_argument('--pdftoppm', help='PaperCraft PDF 预览需要 Poppler')
args = parser.parse_args()
cmd = [args.node, str(ROOT/'render.cjs'), '--browser', args.browser]
if args.pdftoppm: cmd += ['--pdftoppm', args.pdftoppm]
run = subprocess.run(cmd, check=True, capture_output=True, encoding='utf-8')
checks = json.loads(run.stdout.strip())
frames = [Image.open(ROOT/f'assets/step-{i}.png').convert('RGB') for i in range(1,5)]
assert all(f.size==(1120,760) for f in frames)
# 保留每一整幅浏览器画面，不裁切科学对象或改绘原图。
palette = [f.quantize(colors=256) for f in frames]
palette[0].save(ROOT/'tour.gif', save_all=True, append_images=palette[1:],
                duration=[8000]*4, loop=0, disposal=2, optimize=False)
shutil.copyfile(ROOT/'assets/step-2.png', ROOT/'poster.png')
with Image.open(ROOT/'tour.gif') as gif:
    duration=0
    for i in range(gif.n_frames):
        gif.seek(i);duration+=gif.info.get('duration',0)
    assert gif.n_frames==4 and duration==32000
sources={}
html=(ROOT/'index.html').read_text('utf-8')
for value in re.findall(r'(?:href|src)="([^"]+)"', html):
    if value.startswith(('http:', 'https:', '#')): continue
    path=(ROOT/value).resolve()
    if not path.exists(): raise FileNotFoundError(value)
    if path.is_file() and value!='README.md':
        sources[value]=hashlib.sha256(path.read_bytes()).hexdigest()
checks.update({'source_sha256':sources,'gif_sha256':hashlib.sha256((ROOT/'tour.gif').read_bytes()).hexdigest(),
               'scope':'固定公开案例的展示重建；不评价技能在新任务上的生成质量'})
(ROOT/'build-record.json').write_bytes((json.dumps(checks,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'gif':str(ROOT/'tour.gif'),'frames':4,'duration_seconds':32,'size_bytes':(ROOT/'tour.gif').stat().st_size},ensure_ascii=False))
