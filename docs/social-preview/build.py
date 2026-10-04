"""从已选定的封面原图导出网页和分享图片，不重新生成或修饰画面。"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).with_name('artwork.png'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('请使用一个尚不存在的输出目录。')
    with Image.open(args.source) as image:
        if image.width != image.height * 2 or image.width < 1280:
            parser.error('需要至少 1280 像素宽、比例为 2:1 的定稿。')
        image.load()
        args.out.mkdir(parents=True)
        # 只做格式导出；不重绘、不裁剪、不改布局，也不把图片封装成伪矢量源。
        rgb = image.convert('RGB')
        rgb.save(args.out / 'social-preview.jpg', quality=95, subsampling=0, optimize=True)
        if (args.out / 'social-preview.jpg').stat().st_size >= 1_000_000:
            raise ValueError('分享图超过 1 MB；请明确选择新的导出参数。')
        for width in (400, 640):
            rgb.resize((width, width // 2), Image.Resampling.LANCZOS).save(
                args.out / f'preview-{width}.png')
        dimensions = list(image.size)
    shutil.copy2(args.source, args.out / 'social-preview.png')
    record = {
        'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'exporter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dimensions': dimensions,
        'generation': 'OpenAI built-in image_gen; original brand illustration',
        'source_kind': 'raster image with archived prompt; not editable scientific vector artwork',
        'export': 'JPEG quality 95, no cropping; PNG master copied unchanged',
        'files': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in args.out.iterdir() if p.is_file()},
    }
    (args.out / 'build-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(args.out), 'size': dimensions, 'jpeg_bytes': (args.out / 'social-preview.jpg').stat().st_size}))


if __name__ == '__main__':
    main()
