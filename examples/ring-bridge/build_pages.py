from pathlib import Path
import argparse,json
from build_documents import build
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent
if a.out.exists():p.error('Output directory must not exist')
a.out.mkdir(parents=True);s=json.loads((root/'document-input.json').read_text(encoding='utf8'))
for mode in ['clean','review']:
    build(a.out/(mode+'.docx'),s['title'],s['paragraph'],s['caption'],root/s['image'],mode=='review',s['caption']!=s['baseline_caption'],s['paragraph']!=s['baseline_paragraph'])
