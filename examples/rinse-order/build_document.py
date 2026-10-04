"""Fixed document adapter for the three-arm generation comparison.

It applies identical typography and places the submitted figure before Results.
It does not rewrite any generated prose or caption.
"""
from pathlib import Path
import argparse,re,hashlib,json
from docx import Document
from docx.shared import Mm,Pt,RGBColor
from docx.enum.text import WD_COLOR_INDEX,WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def runs(p,s,review=False):
    for chunk in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)',s):
        bold=chunk.startswith('**') and chunk.endswith('**')
        italic=chunk.startswith('*') and chunk.endswith('*') and not bold
        value=chunk[2:-2] if bold else chunk[1:-1] if italic or (chunk.startswith('`') and chunk.endswith('`')) else chunk
        r=p.add_run(value);r.bold=True if bold else None;r.italic=True if italic else None
        if review:r.font.highlight_color=WD_COLOR_INDEX.YELLOW

def main():
    a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--caption',type=Path,required=True)
    a.add_argument('--image',type=Path,required=True);a.add_argument('--alt',type=Path);a.add_argument('--figure-before-heading');a.add_argument('--output',type=Path,required=True);a.add_argument('--review',action='store_true');v=a.parse_args()
    if v.output.exists():raise ValueError('Output exists')
    d=Document();s=d.sections[0];s.page_width=Mm(210);s.page_height=Mm(297);s.top_margin=s.bottom_margin=Mm(19);s.left_margin=s.right_margin=Mm(25)
    for name in ('Normal','Title','Heading 1','Heading 2','Caption'):
        st=d.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor.from_string('000000');st.font.size=Pt(10.5)
        st.paragraph_format.space_after=Pt(6);st.paragraph_format.line_spacing=1.10
        st._element.get_or_add_rPr().append(OxmlElement('w:lang'));st._element.rPr[-1].set(qn('w:val'),'en-US')
    d.styles['Title'].font.size=Pt(17);d.styles['Title'].font.bold=True
    d.styles['Heading 1'].font.size=Pt(12);d.styles['Heading 1'].font.bold=True
    d.styles['Heading 2'].font.size=Pt(11);d.styles['Heading 2'].font.bold=True
    d.styles['Caption'].font.size=Pt(9.5);d.styles['Caption'].font.bold=False;d.styles['Caption'].font.italic=False
    for style in d.styles:
        for border in style._element.findall('.//'+qn('w:pBdr')):
            border.getparent().remove(border)
    inserted=False
    caption_text=v.caption.read_text('utf8').strip()
    def normalized(s):return re.sub(r'\s+',' ',s.replace('*','').replace('`','')).strip()
    def figure():
        nonlocal inserted
        p=d.add_paragraph();p.paragraph_format.keep_with_next=True;pic=p.add_run().add_picture(str(v.image),width=Mm(160))
        if v.alt:pic._inline.docPr.set('descr',v.alt.read_text('utf8').strip())
        text=v.caption.read_text('utf8').strip()
        # Caption files must contain the caption alone, not its audit/alt text.
        text=re.sub(r'^#+\s*(?:Figure caption|Caption)\s*\n+','',text,flags=re.I)
        cap=d.add_paragraph(style='Caption');cap.paragraph_format.keep_together=True;runs(cap,text,v.review);inserted=True
    for block in re.split(r'\n\s*\n',v.input.read_text('utf8').strip()):
        if re.match(r'^!\[',block) or normalized(block)==normalized(caption_text):continue
        m=re.match(r'^(#{1,3})\s+([^\n]+)$',block)
        if m:
            title=m[2]
            if re.fullmatch(r'Figure\s+\d+',title,re.I):continue
            if not inserted and (title==v.figure_before_heading if v.figure_before_heading else re.search(r'result|discussion',title,re.I)):figure()
            p=d.add_paragraph(style='Title' if len(m[1])==1 else 'Heading 1' if len(m[1])==2 else 'Heading 2');runs(p,title,v.review)
        elif block.startswith('|'):
            rows=[list(map(str.strip,line.strip().strip('|').split('|'))) for line in block.splitlines() if line.startswith('|')]
            rows=[row for row in rows if not all(re.fullmatch(r':?-+:?',cell) for cell in row)]
            assert rows and all(len(row)==len(rows[0]) for row in rows)
            table=d.add_table(rows=0,cols=len(rows[0]));table.style='Light Shading Accent 1'
            table.autofit=False
            widths=[20,20,17,21,27,20,18,17] if len(rows[0])==8 else [160/len(rows[0])]*len(rows[0])
            assert abs(sum(widths)-160)<.01
            for col,width in zip(table.columns,widths):col.width=Mm(width)
            for i,row in enumerate(rows):
                cells=table.add_row().cells
                for j,(c,value,width) in enumerate(zip(cells,row,widths)):
                    c.width=Mm(width)
                    mar=OxmlElement('w:tcMar')
                    for edge in ('left','right'):
                        val=OxmlElement('w:'+edge);val.set(qn('w:w'),'40');val.set(qn('w:type'),'dxa');mar.append(val)
                    c._tc.get_or_add_tcPr().append(mar)
                    runs(c.paragraphs[0],value,v.review)
                    c.paragraphs[0].paragraph_format.space_after=Pt(2)
                    # This short demonstration table fits on one page. Keep its
                    # caption and rows together, including the repeated header.
                    c.paragraphs[0].paragraph_format.keep_with_next=i<len(rows)-1
                    if i>0 and j>=2:c.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.RIGHT
                    for run in c.paragraphs[0].runs:run.font.size=Pt(9);run.bold=i==0
                props=table.rows[-1]._tr.get_or_add_trPr();props.append(OxmlElement('w:cantSplit'))
                if i==0:props.append(OxmlElement('w:tblHeader'))
        else:
            for segment in [block.replace('\n',' ')]:
                p=d.add_paragraph();runs(p,segment,v.review)
                if re.match(r'^Table\s+\d',normalized(segment)):p.paragraph_format.keep_with_next=True
    if not inserted:figure()
    v.output.parent.mkdir(parents=True,exist_ok=True);d.save(v.output)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    v.output.with_suffix('.source.json').write_text(json.dumps({'text':sha(v.input),'caption':sha(v.caption),'image':sha(v.image),'adapter':sha(Path(__file__)),'output':sha(v.output),'review':'yellow new authored text; not native track changes' if v.review else 'clean','renderer':'pending'},indent=2),'utf8')
    print(v.output)
if __name__=='__main__':main()
