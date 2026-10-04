"""Compare a rebuilt figure with the preserved selected artwork; no host paths."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageChops
from pypdf import PdfReader
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--skill',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refuse overwrite')
    root=Path(__file__).resolve().parent;expected=root/'figures'/'object-selected';actual=a.candidate/'rendered'
    im0=Image.open(expected/'figure.png').convert('RGB');im1=Image.open(actual/'figure.png').convert('RGB')
    png_equal=im0.size==im1.size and ImageChops.difference(im0,im1).getbbox() is None
    p0=PdfReader(expected/'figure.pdf');p1=PdfReader(actual/'figure.pdf')
    same_pages=len(p0.pages)==len(p1.pages)==1
    same_text=same_pages and all(x.extract_text()==y.extract_text() for x,y in zip(p0.pages,p1.pages))
    same_stream=same_pages and all(x.get_contents().get_data()==y.get_contents().get_data() for x,y in zip(p0.pages,p1.pages))
    same_size=same_pages and all(x.mediabox==y.mediabox for x,y in zip(p0.pages,p1.pages))
    qa=json.loads((actual/'qa.json').read_text(encoding='utf-8'))
    original=json.loads((root/'artifact_provenance.json').read_text(encoding='utf-8'))
    input_equal=all(sha(root/'input'/n)==h for n,h in original['raw_input_sha256'].items())
    passed=all([png_equal,same_text,same_stream,same_size,input_equal,qa['technical_status']=='PASS'])
    receipt={'status':'PASS' if passed else 'FAIL','kind':'PORTABLE_PACKAGING_REBUILD_NOT_NEW_GENERATION','input_bytes_preserved':input_equal,
      'png_pixel_equal':png_equal,'png_size_px':list(im1.size),'png_sha256':sha(actual/'figure.png'),
      'pdf_page_count_equal':same_pages,'pdf_page_size_equal':same_size,'pdf_text_equal':same_text,'pdf_drawing_stream_equal':same_stream,
      'pdf_sha256':sha(actual/'figure.pdf'),'pdf_byte_identity_required':False,'pdf_note':'Creation timestamps and document IDs are metadata, not drawing content.',
      'technical_status':qa['technical_status'],'author_acceptance':False,'python_version':sys.version.split()[0],
      'actual_skill_hashes':{str(p.relative_to(a.skill)).replace('\\','/'):sha(p) for p in [a.skill/'SKILL.md',a.skill/'references'/'drawing-and-depth.md',a.skill/'scripts'/'render_figure.py',a.skill/'scripts'/'figure_core.py',a.skill/'scripts'/'relation_components.py']},
      'packaging_changes_only':['relative default input/baseline paths','example-root source references','public receipts without host absolute paths']}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['status','png_pixel_equal','pdf_text_equal','pdf_drawing_stream_equal','input_bytes_preserved']}));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
