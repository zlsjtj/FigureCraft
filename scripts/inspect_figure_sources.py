"""Inventory actual figure representations and effective placement resolution.

This is a source-availability report, not a curve digitizer, vectorizer, or
scientific validation. Scientific roles and raw-data availability are explicitly
declared in a manifest; a filename or a JPEG's DPI tag is never such evidence.
DOCX coverage is the main document only. Other parts and fallback forms are
reported for review. Requires Pillow for raster metadata and decoded-pixel hashes.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import posixpath
from xml.etree import ElementTree as ET
import zipfile

from PIL import Image, UnidentifiedImageError

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'v': 'urn:schemas-microsoft-com:vml',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def representation(data, suffix=''):
    result = {'sha256': sha(data), 'bytes': len(data)}
    try:
        with Image.open(BytesIO(data)) as im:
            im.load()
            rgb = im.convert('RGBA')
            result.update(representation='raster', format=im.format,
                          pixels=list(im.size), dpi_tag=im.info.get('dpi'),
                          decoded_rgba_sha256=sha(str(im.size).encode()+rgb.tobytes()))
        return result
    except (UnidentifiedImageError, OSError):
        pass
    if suffix.lower() == '.svg':
        root = ET.fromstring(data)
        images = [n for n in root.iter() if n.tag.split('}')[-1] == 'image']
        vector_tags = {'path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line', 'text'}
        counts = {tag: sum(n.tag.split('}')[-1] == tag for n in root.iter()) for tag in vector_tags}
        result.update(representation='mixed-svg' if images else 'vector-svg',
                      raster_nodes=len(images), vector_nodes=counts,
                      editability_note='SVG structure is inspectable; this does not establish raw data or scientific provenance.')
    elif suffix.lower() in {'.csv', '.tsv', '.xlsx', '.json'}:
        result.update(representation='structured-file-unvalidated',
                      editability_note='File type alone does not establish measurement data.')
    else:
        result['representation'] = 'uninspected'
    return result


def effective_dpi(pixels, width_mm, height_mm, crop=None):
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError('Placement dimensions must be positive')
    crop = crop or {}
    horizontal = 1 - (crop.get('l', 0) + crop.get('r', 0)) / 100000
    vertical = 1 - (crop.get('t', 0) + crop.get('b', 0)) / 100000
    if not (0 < horizontal <= 1 and 0 < vertical <= 1):
        raise ValueError('Unsupported crop fractions')
    return [pixels[0]*horizontal*25.4/width_mm, pixels[1]*vertical*25.4/height_mm]


def inspect_docx(path):
    drawings, warnings = [], []
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise ValueError('Corrupt DOCX package')
        root = ET.fromstring(archive.read('word/document.xml'))
        rels = {n.get('Id'): n.attrib for n in ET.fromstring(archive.read('word/_rels/document.xml.rels'))}
        body = root.find('w:body', NS)
        paragraphs = body.findall('w:p', NS)
        drawing_counter = 0
        for paragraph_index, p in enumerate(paragraphs):
            for drawing in p.findall('.//w:drawing', NS):
                drawing_counter += 1
                row = {'drawing_index': drawing_counter, 'body_paragraph_index': paragraph_index}
                blips = drawing.findall('.//a:blip', NS)
                if len(blips) != 1:
                    row['status'] = 'UNSUPPORTED'; drawings.append(row)
                    warnings.append(f'Drawing {drawing_counter}: primary blip count {len(blips)}')
                    continue
                rel = rels.get(blips[0].get('{'+NS['r']+'}embed'))
                if not rel or rel.get('TargetMode') == 'External':
                    row['status'] = 'UNSUPPORTED'; drawings.append(row)
                    warnings.append(f'Drawing {drawing_counter}: missing/external image')
                    continue
                part = posixpath.normpath(posixpath.join('word', rel['Target']))
                if not part.startswith('word/media/'):
                    raise ValueError('Image target is outside word/media')
                row.update(part=part, embedded=representation(archive.read(part), Path(part).suffix))
                extent = drawing.find('.//wp:extent', NS)
                if extent is not None:
                    row['placement_mm'] = [int(extent.get(k))/36000 for k in ('cx', 'cy')]
                    crop_node = drawing.find('.//a:srcRect', NS)
                    crop = {k: int(v) for k, v in crop_node.attrib.items()} if crop_node is not None else {}
                    row['crop'] = crop
                    if 'pixels' in row['embedded']:
                        row['effective_dpi'] = effective_dpi(row['embedded']['pixels'], *row['placement_mm'], crop)
                        pwidth, pheight = row['embedded']['pixels']
                        row['aspect_ratio_difference_fraction'] = row['placement_mm'][0]/row['placement_mm'][1]/(pwidth/pheight)-1
                else:
                    warnings.append(f'Drawing {drawing_counter}: missing placement dimensions')
                row['status'] = 'INSPECTED'
                drawings.append(row)
        all_count = len(root.findall('.//w:drawing', NS))
        if all_count != drawing_counter:
            warnings.append(f'{all_count-drawing_counter} drawings in tables/textboxes or other non-top-level paragraphs require separate inventory')
        for feature, selector in [('VML', './/v:imagedata'), ('AlternateContent', './/mc:AlternateContent')]:
            if root.findall(selector, NS):
                warnings.append(feature+' requires separate representation audit')
        alternate = [n for n in root.iter() if n.tag.endswith('}svgBlip')]
        if alternate:
            warnings.append(f'{len(alternate)} SVG alternate representations require the existing integration audit')
        for name in archive.namelist():
            if name.startswith(('word/header', 'word/footer')) and name.endswith('.xml'):
                content = archive.read(name)
                if b'drawing' in content or b'imagedata' in content:
                    warnings.append(name+' contains an image; main-document inventory excludes it')
    return {'path': str(Path(path).resolve()), 'sha256': sha(Path(path).read_bytes()),
            'drawings': drawings, 'warnings': warnings,
            'paragraph_index_convention': 'zero-based top-level body paragraphs; drawing indices are one-based within those paragraphs'}


def inspect_sources(docx, sources, declaration=None):
    spec = declaration or {}
    assets = []
    source_root = Path(sources).resolve()
    declared_assets = spec.get('assets', {})
    for file in sorted(source_root.rglob('*')):
        if not file.is_file():
            continue
        key = file.relative_to(source_root).as_posix()
        asset = {'relative_path': key, **representation(file.read_bytes(), file.suffix)}
        if key in declared_assets:
            asset['declaration'] = declared_assets[key]
        assets.append(asset)
    document = inspect_docx(docx)
    by_path = {a['relative_path']: a for a in assets}
    declarations = spec.get('drawings', [])
    indices = [d['drawing_index'] for d in declarations]
    if len(indices) != len(set(indices)):
        raise ValueError('Duplicate drawing declaration')
    for drawing in document['drawings']:
        embedded = drawing.get('embedded', {})
        drawing['byte_identical_sources'] = [a['relative_path'] for a in assets if a['sha256'] == embedded.get('sha256')]
        drawing['pixel_identical_sources'] = [a['relative_path'] for a in assets if a.get('decoded_rgba_sha256') and a['decoded_rgba_sha256'] == embedded.get('decoded_rgba_sha256')]
        declared = next((d for d in declarations if d['drawing_index'] == drawing['drawing_index']), None)
        if declared:
            drawing['declaration'] = declared
            if 'source_file' in declared:
                source = by_path.get(declared['source_file'])
                if source is None:
                    raise ValueError('Declared source file is missing: '+declared['source_file'])
                drawing['declared_source_sha256'] = source['sha256']
                if source['sha256'] == embedded.get('sha256'):
                    drawing['source_identity_status'] = 'BYTE_MATCH'
                elif source.get('decoded_rgba_sha256') and source['decoded_rgba_sha256'] == embedded.get('decoded_rgba_sha256'):
                    drawing['source_identity_status'] = 'PIXEL_MATCH_DIFFERENT_BYTES'
                else:
                    drawing['source_identity_status'] = 'DECLARED_NOT_BYTE_MATCH_REVIEW_REQUIRED'
                if source.get('pixels') and drawing.get('placement_mm'):
                    drawing['declared_source_pixels'] = source['pixels']
                    drawing['declared_source_dpi_at_current_placement'] = effective_dpi(source['pixels'], *drawing['placement_mm'], drawing.get('crop'))
                    if embedded.get('pixels'):
                        pairs = list(zip(source['pixels'], embedded['pixels']))
                        if all(a == b for a, b in pairs):
                            relation = 'SAME_PIXEL_DIMENSIONS'
                        elif all(a >= b for a, b in pairs):
                            relation = 'LARGER_PIXEL_DIMENSIONS'
                        elif all(a <= b for a, b in pairs):
                            relation = 'SMALLER_PIXEL_DIMENSIONS'
                        else:
                            relation = 'MIXED_PIXEL_DIMENSIONS'
                        drawing['source_resolution_relation'] = relation
                        drawing['source_resolution_note'] = 'Pixel dimensions do not establish image identity or recovered detail; compare actual source content.'
        else:
            drawing['source_identity_status'] = 'UNDECLARED'
    unknown = set(indices) - {d['drawing_index'] for d in document['drawings']}
    if unknown:
        raise ValueError('Declared drawing indices do not exist: '+str(sorted(unknown)))
    return {'tool_version': '1.0.0', 'overall_status': 'REVIEW_REQUIRED',
            'source_root': str(source_root), 'assets': assets, 'document': document,
            'availability_statement': spec.get('availability_statement'),
            'limits': ['No numerical observations are recovered from raster curves.',
                       'DPI is calculated from real pixels and physical placement, not metadata tags or file size.',
                       'Declared roles, correspondence and data availability require source/author evidence.',
                       'An SVG with image nodes is mixed, not full vector artwork.',
                       'Aspect, crop, fonts and readability still require actual page review.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docx', required=True, type=Path)
    parser.add_argument('--sources', required=True, type=Path)
    parser.add_argument('--declarations', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output already exists; choose a new path')
    declaration = json.loads(args.declarations.read_text(encoding='utf-8-sig')) if args.declarations else None
    result = inspect_sources(args.docx, args.sources, declaration)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'output': str(args.out), 'drawings': len(result['document']['drawings']),
                      'assets': len(result['assets']), 'overall_status': result['overall_status']}))


if __name__ == '__main__':
    main()
