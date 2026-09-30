"""Create a standalone geometric DEMO page; no editing of existing research."""
from pathlib import Path
import argparse, hashlib, json
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_COLOR_INDEX

def build(image, title, body, caption, out, baseline=None):
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc=Document(); sec=doc.sections[0]
    sec.page_width=Mm(210); sec.page_height=Mm(297)
    sec.left_margin=sec.right_margin=Mm(25)
    sec.top_margin=sec.bottom_margin=Mm(22)
    normal=doc.styles['Normal']; normal.font.name='Arial'; normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(7)
    normal.paragraph_format.line_spacing=1.1
    h=sec.header.paragraphs[0].add_run('Original geometric DEMO — no measurements or performance claims')
    h.font.size=Pt(8); h.font.color.rgb=RGBColor.from_string('697887')
    old=set(p.text for p in Document(baseline).paragraphs) if baseline else set()
    for text,kind in [(title,'title'),(body,'body')]:
        p=doc.add_paragraph(); r=p.add_run(text)
        if kind=='title':r.bold=True;r.font.size=Pt(17)
        if baseline and text not in old:r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(9)
    p.add_run().add_picture(str(image),width=Mm(160))
    p=doc.add_paragraph();r=p.add_run(caption)
    r.font.size=Pt(9)
    if baseline and caption not in old:r.font.highlight_color=WD_COLOR_INDEX.YELLOW
    doc.save(out)
    record={'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
      'docx_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'image_width_mm':160,
      'yellow':'Changed text relative to before.docx; image changes require visual comparison. Not native tracked changes.',
      'protected_objects':'New original DEMO, no inherited equations, fields or revisions.'}
    out.with_suffix('.json').write_text(json.dumps(record,indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--title',required=True)
    p.add_argument('--body',type=Path,required=True);p.add_argument('--caption',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',type=Path)
    a=p.parse_args();build(a.image,a.title,a.body.read_text(encoding='utf-8').strip(),a.caption.read_text(encoding='utf-8').strip(),a.out,a.baseline)
