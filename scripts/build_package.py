"""从同一份源码生成技能 ZIP 与公开试用包；不安装、不上传、不调用模型。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, unquote
import zipfile

HOSTS = ('codex', 'claude-code', 'claude', 'workbuddy')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_first_run(root):
    spec = importlib.util.spec_from_file_location('package_first_run', root / 'scripts/first_run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_zip(path, files):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def build(root, out, hosts=HOSTS):
    root, out = Path(root).resolve(), Path(out).resolve()
    if not hosts or set(hosts) - set(HOSTS):
        raise ValueError('未知或空宿主列表。')
    if out.exists() or out == root or root in out.parents:
        raise ValueError('安装包目录必须是仓库外的新目录。')
    config = json.loads((root / 'package-files.json').read_text('utf-8'))
    raw = (root / 'SKILL.md').read_text('utf-8')
    name = re.search(r'^name:\s*(\S+)\s*$', raw, re.M).group(1)
    version = re.search(r'version:\s*"([^"]+)"', raw).group(1)
    sources = {}
    for entry in config['include']:
        path = (root / entry).resolve()
        if root not in path.parents or not path.exists():
            raise ValueError('打包清单缺少或越界：' + entry)
        for item in sorted(path.rglob('*')) if path.is_dir() else [path]:
            if item.is_symlink():
                raise ValueError('打包清单不接受符号链接：' + str(item))
            if item.is_file() and '__pycache__' not in item.parts and item.suffix not in ('.pyc', '.pyo'):
                sources[item.relative_to(root).as_posix()] = item.read_bytes()
    if 'SKILL.md' not in sources or 'LICENSE' not in sources:
        raise ValueError('缺少技能入口或许可证。')
    base_url = config['repository_url'].rstrip('/')
    rewritten = []

    def rewrite_links(rel, data):
        text = data.decode('utf-8-sig')

        def link(target):
            if not target or target.startswith('#') or re.match(r'^[A-Za-z][\w+.-]*:', target):
                return target
            target = target.strip('<>')
            path_text, _, anchor = target.partition('#')
            p = ((root / rel).parent / unquote(path_text)).resolve()
            if p != root and root not in p.parents:
                raise ValueError(f'越界引用：{rel} -> {target}')
            if not p.exists():
                raise ValueError(f'失效引用：{rel} -> {target}')
            local = p.relative_to(root).as_posix()
            if local in sources or any(k.startswith(local.rstrip('/') + '/') for k in sources):
                return target
            url = base_url + ('/tree/main/' if p.is_dir() else '/blob/main/') + quote(local, safe='/')
            rewritten.append({'source': rel, 'target': target, 'public_url': url})
            return url + ('#' + anchor if anchor else '')

        # 示例代码中的占位路径不作为链接；正文保留必要依赖，历史展示链接指向公开仓库。
        parts = re.split(r'(```.*?```)', text, flags=re.S)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r'(\]\()([^\s)]+)(\))', lambda m: m[1] + link(m[2]) + m[3], parts[i])
            parts[i] = re.sub(r'((?:src|href)=")([^"]+)(")', lambda m: m[1] + link(m[2]) + m[3], parts[i])
        return ''.join(parts).encode('utf-8')

    packaged = {rel: rewrite_links(rel, data) if rel.endswith('.md') else data for rel, data in sources.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.skill-package-', dir=out.parent) as temp:
        stage = Path(temp)
        reports = {}
        for host in hosts:
            files = dict(packaged)
            if host == 'workbuddy':
                # 只在适配包增加宿主元信息；正文与其他包完全同源。
                first, front, body = files['SKILL.md'].decode('utf-8').split('---', 2)
                description = re.search(r'^description:\s*(.+)$', front, re.M).group(1)
                extra = {'display_name': config['display_name'], 'description_zh': description,
                         'description_en': config['description_en'], 'version': version, 'author': 'zlsjtj'}
                front += ''.join(f'{key}: {json.dumps(value, ensure_ascii=False)}\n' for key, value in extra.items())
                files['SKILL.md'] = ('---' + front + '---' + body).encode('utf-8')
            manifest = {'name': name, 'version': version, 'host': host,
                        'source_entry_sha256': sha(sources['SKILL.md']),
                        'files': {key: {'source_sha256': sha(sources[key]), 'package_sha256': sha(value)} for key, value in sorted(files.items())},
                        'online_examples': rewritten, 'host_execution': 'NOT_RUN_BY_PACKAGER'}
            files['package-manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            filename = f'{name}-{host}.zip'
            write_zip(stage / filename, {name + '/' + key: value for key, value in files.items()})
            reports[filename] = {'sha256': sha((stage / filename).read_bytes()), 'bytes': (stage / filename).stat().st_size,
                                 'host': host, 'files': len(files), 'host_execution': 'NOT_RUN_BY_PACKAGER'}
        helper = load_first_run(root)
        trial = stage / 'trial'
        helper.prepare(trial, root=root, host='claude', portable=True)
        # 相对路径任务适用于任何已启用本技能的宿主；不携带维护者的环境清单。
        trial_files = {f'{name}-try/' + p.relative_to(trial).as_posix(): p.read_bytes() for p in trial.rglob('*') if p.is_file()}
        trial_name = f'{name}-first-use.zip'
        write_zip(stage / trial_name, trial_files)
        reports[trial_name] = {'sha256': sha((stage / trial_name).read_bytes()), 'bytes': (stage / trial_name).stat().st_size,
                               'purpose': 'RAW_MATERIALS_ONLY', 'generation': 'NOT_RUN'}
        out.mkdir()
        for filename in reports:
            (out / filename).write_bytes((stage / filename).read_bytes())
        (out / 'packages.json').write_text(json.dumps({'skill': name, 'version': version, 'packages': reports}, ensure_ascii=False, indent=2), encoding='utf-8')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--host', choices=(*HOSTS, 'all'), default='all')
    args = parser.parse_args()
    try:
        result = build(Path(__file__).resolve().parents[1], args.out, HOSTS if args.host == 'all' else (args.host,))
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
