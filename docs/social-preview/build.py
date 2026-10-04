"""从可编辑布局生成仓库分享页；引用原始图元，不重新生成科研对象。"""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from html import escape


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_image(root, node):
    path = (root / node['source']).resolve()
    if root not in path.parents:
        raise ValueError('图源超出仓库目录')
    element = ET.parse(path).find(f".//*[@id='{node['id']}']")
    if element is None or element.tag.split('}')[-1] != 'image':
        raise ValueError('未找到指定图像对象')
    uri = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href')
    if not uri.startswith('data:image/png;base64,'):
        raise ValueError('只接受原图中的内嵌 PNG')
    data = base64.b64decode(uri.split(',', 1)[1], validate=True)
    # 沿用原 SVG 的显示宽高比，原始像素不做裁切、换色或重绘。
    width = node['height'] * float(element.get('width')) / float(element.get('height'))
    return data, uri, width, {'source': node['source'], 'object_id': node['id'],
                            'source_sha256': sha(path.read_bytes()), 'pixel_file_sha256': sha(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--font', type=Path, required=True, help='支持中文的 TrueType 字体，可为 TTC')
    parser.add_argument('--bold-font', type=Path, required=True)
    parser.add_argument('--latin-font', type=Path, required=True)
    parser.add_argument('--latin-bold-font', type=Path, required=True)
    parser.add_argument('--pdftoppm', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    out = args.out.resolve()
    if out.exists() or out == root or root in out.parents:
        parser.error('输出须为仓库外的新目录；不覆盖已有文件。')
    for path in (args.font, args.bold_font, args.latin_font, args.latin_bold_font, args.pdftoppm):
        if not path.is_file():
            parser.error('找不到依赖：' + str(path))
    try:
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.colors import HexColor
        from reportlab.lib.utils import ImageReader
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        parser.error(f'缺少 {exc.name}；请在执行此脚本的 Python 中安装 reportlab、pypdf。')

    layout_path = here / 'layout.json'
    layout = json.loads(layout_path.read_text('utf-8'))
    width, height = layout['width'], layout['height']
    fonts = {'regular': args.font, 'bold': args.bold_font,
             'latin': args.latin_font, 'latin-bold': args.latin_bold_font}
    families = {}
    for key, path in fonts.items():
        registered = TTFont('Share-' + key, str(path), subfontIndex=0)
        pdfmetrics.registerFont(registered)
        family = registered.face.familyName
        families[key] = family.decode('utf-8') if isinstance(family, bytes) else str(family)
    sources = {rel: sha((root / rel).read_bytes()) for rel in layout['sources']}
    images, text_bounds = [], []
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.social-preview-', dir=out.parent) as temporary:
        stage = Path(temporary)
        pdf = Canvas(str(stage / 'social-preview.pdf'), pagesize=(width, height), pageCompression=1, invariant=1)
        pdf.setTitle(layout['title'])
        pdf.setAuthor('zlsjtj')
        pdf.setSubject(layout['description'])
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
               '<title>' + escape(layout['title']) + '</title>', '<desc>' + escape(layout['description']) + '</desc>']
        background = layout['background']
        pdf.setFillColor(HexColor(background))
        pdf.rect(0, 0, width, height, stroke=0, fill=1)
        svg.append(f'<rect width="{width}" height="{height}" fill="{background}"/>')
        for node in layout['nodes']:
            kind, x, y = node['type'], node['x'], node['y']
            if kind == 'rect':
                w, h, fill = node['width'], node['height'], node['fill']
                pdf.setFillColor(HexColor(fill))
                pdf.rect(x, height-y-h, w, h, stroke=0, fill=1)
                svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
            elif kind == 'line':
                stroke, line_width = node['stroke'], node['width']
                pdf.setStrokeColor(HexColor(stroke))
                pdf.setLineWidth(line_width)
                pdf.line(x, height-y, node['x2'], height-node['y2'])
                svg.append(f'<path d="M{x},{y} L{node["x2"]},{node["y2"]}" stroke="{stroke}" stroke-width="{line_width}"/>')
            elif kind == 'text':
                text, size, font, fill = node['text'], node['size'], node['font'], node['fill']
                name = 'Share-' + font
                span = pdfmetrics.stringWidth(text, name, size)
                if x < 0 or x + span > width-30 or y-size < 0 or y > height-25:
                    raise ValueError('文字超出安全区域：' + text)
                text_bounds.append({'text': text, 'x': x, 'baseline': y, 'width': span, 'size': size})
                pdf.setFont(name, size)
                pdf.setFillColor(HexColor(fill))
                pdf.drawString(x, height-y, text)
                weight = '700' if 'bold' in font else '400'
                family = escape(families[font], quote=True)
                svg.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>')
            elif kind == 'svg-image':
                data, uri, w, provenance = source_image(root, node)
                h = node['height']
                if x < 0 or y < 0 or x+w > width or y+h > height:
                    raise ValueError('原图对象越界')
                pdf.drawImage(ImageReader(io.BytesIO(data)), x, height-y-h, width=w, height=h, mask='auto')
                svg.append(f'<image id="source-{escape(node["id"])}" x="{x}" y="{y}" width="{w}" height="{h}" href="{uri}"/>')
                images.append(provenance)
            else:
                raise ValueError('未知图元：' + kind)
        pdf.showPage()
        pdf.save()
        svg.append('</svg>')
        (stage / 'social-preview.svg').write_text('\n'.join(svg) + '\n', encoding='utf-8')
        run = subprocess.run([str(args.pdftoppm.resolve()), '-png', '-singlefile', '-scale-to-x', str(width),
                              '-scale-to-y', str(height), str(stage / 'social-preview.pdf'), str(stage / 'social-preview')],
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
        if run.returncode:
            raise RuntimeError(run.stderr)
        png = (stage / 'social-preview.png').read_bytes()
        if png[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', png[16:24]) != (width, height):
            raise ValueError('PNG 输出尺寸不符')
        if len(png) >= 1_000_000:
            raise ValueError('PNG 超过分享图的 1 MB 限制')
        extracted = PdfReader(stage / 'social-preview.pdf').pages[0].extract_text()
        for node in layout['nodes']:
            if node['type'] == 'text' and node['text'] not in extracted:
                raise ValueError('PDF 丢失文字：' + node['text'])
        record = {'title': layout['title'], 'layout_sha256': sha(layout_path.read_bytes()),
                  'source_files': sources, 'source_images': images, 'png_size': [width, height],
                  'png_bytes': len(png), 'text_bounds': text_bounds,
                  'font_sha256': {k: sha(p.read_bytes()) for k, p in fonts.items()},
                  'font_families': families, 'pdf_text_checked': True,
                  'files': {p.name: sha(p.read_bytes()) for p in stage.iterdir()},
                  'scope': '既有公开案例的分享排版，不是新的科研成果、技能新生成或用户转化验证；SVG 文字编辑需要相应字体。',
                  'visual_review': 'NOT_PERFORMED_BY_SCRIPT', 'published': False}
        (stage / 'build-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        out.mkdir()
        for p in stage.iterdir():
            shutil.copyfile(p, out / p.name)
    print(json.dumps({'output': str(out), 'size': [width, height], 'png_bytes': len(png)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
