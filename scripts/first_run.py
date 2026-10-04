"""准备一个独立的首次试用目录；不调用模型、不安装依赖。"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile

DEMO = {'title': '根据材料画一张机制图',
 'skill': 'scientific-figure-studio',
 'source': 'examples/paired-placement/source/inputs',
 'files': ['rough.md', 'notes.md', 'results.csv'],
 'modules': ['reportlab', 'pypdf', 'PIL', 'numpy'],
 'task': '请阅读 rough.md、notes.md 和 results.csv，自主确定最需要由这张机制图讲清的关系。只做一张 160 × 100 mm '
         '的图，不重写论文，也不另做结果图。区分输入已给出的科学关系与可以自主选择的构图，不引入材料没有提供的物理位置关系。\n'
         '\n'
         '交付可编辑图源、可重建脚本、SVG/PDF/PNG、简短英文图注和中文选择说明。按实际尺寸查看标签与对象关系；如用了混合矢量/位图，说明可编辑范围。材料中的数据与失败条件保持不变，不用缩小字号掩盖拥挤。'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    modules = {}
    for name in DEMO['modules']:
        try:
            found = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            found = False
        modules[name] = 'FOUND_NOT_EXECUTED' if found else 'NOT_FOUND'
    programs = {name: shutil.which(name) for name in ('soffice', 'pdftoppm')}
    if os.name == 'nt' and not programs['soffice']:
        candidate = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'LibreOffice/program/soffice.exe'
        if candidate.is_file():
            programs['soffice'] = str(candidate)
    return {'python': sys.executable, 'modules': modules, 'programs': programs,
            'status': 'DISCOVERY_ONLY', 'render_execution': 'NOT_RUN',
            'note': '仅查找当前 Python 的模块和 PATH 上的程序（另查 Windows 常见 LibreOffice 路径）。未找到不代表本机没有；找到也不代表已成功运行。字体须在生成前确认。'}


HOSTS = ('codex', 'claude-code', 'claude', 'workbuddy')


def task_text(root, out, host='codex', portable=False):
    if host not in HOSTS:
        raise ValueError('未知宿主：' + host)
    portable = portable or host == 'claude'
    skill = DEMO['skill']
    invocation = ('$' + skill) if host == 'codex' else ('/' + skill) if host == 'claude-code' else skill
    location = ('先使用已安装的 `' + skill + '` 技能，读取其实际 SKILL.md。\n') if portable else ('先读取并使用这个目录的技能：`' + str(root / 'SKILL.md') + '`。\n')
    paths = ('输入为本任务包中的 `input/`（或本次上传的同名附件）；输出写入本次工作区的新 `output/`，交付可下载文件。\n') if portable else ('输入目录：`' + str(out / 'input') + '`\n输出目录：`' + str(out / 'output') + '`（新建）。\n')
    return ('# 首次试用：' + DEMO['title'] + '\n\n'
            '以下材料都是原创教学构造值，不是真实科研结果。请保留 DEMO 标记。\n\n'
            + location + '调用标识：`' + invocation + '`。仅使用下方原始材料，不先读取仓库里的成品、评阅或改写答案。\n\n'
            + paths + '\n' + DEMO['task'] + '\n\n'
            '先确认当前执行环境的 Python 包、字体与渲染程序。environment.json 只是准备记录，不是运行通过。'
            '保留输入文件；缺少工具时说明确切缺项，不把未渲染文件写成已验收。\n')


def prepare(out, root=None, host='codex', portable=False):
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    out = Path(out).resolve()
    if out == root or root in out.parents:
        raise ValueError('试用目录应在技能文件夹外，避免混入输入或已安装技能。')
    if out.exists():
        raise ValueError('输出目录已存在；请换一个新名字，已有内容不会覆盖。')
    source = root / DEMO['source']
    files = [source / name for name in DEMO['files']]
    for path in [root / 'SKILL.md', *files]:
        if not path.is_file():
            raise ValueError('缺少试用材料：' + str(path))
    task = task_text(root, out, host, portable)
    out.parent.mkdir(parents=True, exist_ok=True)
    # A sibling staging directory avoids exposing a half-copied input pack.
    with tempfile.TemporaryDirectory(prefix='.first-use-', dir=out.parent) as temporary:
        stage = Path(temporary)
        (stage / 'input').mkdir()
        for path in files:
            shutil.copy2(path, stage / 'input' / path.name)
        hashes = {path.name: digest(path) for path in files}
        assert hashes == {p.name: digest(p) for p in (stage / 'input').iterdir()}
        receipt = {'status': 'PREPARED_ONLY', 'skill': DEMO['skill'], 'host': host,
                   'skill_entry_sha256': digest(root / 'SKILL.md'),
                   'helper_sha256': digest(Path(__file__)), 'input_sha256': hashes,
                   'generation': 'NOT_RUN', 'human_review': 'NOT_RUN'}
        (stage / 'TASK.md').write_text(task, encoding='utf-8')
        for name, data in [('environment.json', {'status': 'NOT_PROBED', 'note': '可搬移任务包；请在实际宿主环境检查依赖。'} if portable or host == 'claude' else environment()), ('preparation.json', receipt)]:
            (stage / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # mkdir is exclusive even on POSIX, so concurrent runs cannot replace an existing directory.
        out.mkdir()
        try:
            for path in stage.iterdir():
                shutil.move(str(path), str(out / path.name))
        except Exception:
            # Only remove the directory created by this invocation.
            shutil.rmtree(out)
            raise
    return receipt



def environment_summary(record):
    """Explain preparation vs. execution without prescribing a machine-wide install."""
    if record.get('status') == 'NOT_PROBED':
        return '上传任务未检查本机环境；请在实际执行任务的宿主中确认依赖。'
    lines = ['准备脚本所用 Python：' + record['python']]
    missing = [name for name, state in record['modules'].items() if state == 'NOT_FOUND']
    if missing:
        lines.append('此环境未找到部分生成/检查依赖：' + ', '.join(missing) + '。')
        lines.append('材料已备齐，可交给宿主；生成前请选定实际执行环境。不要直接往办公软件自带的 Python 中安装依赖。')
    else:
        lines.append('已找到所列模块，但尚未导入或执行；字体与导出程序仍需实际检查。')
    lines.append('详情见 environment.json；手动运行工具前先看 docs/usage.md。')
    return '\n'.join(lines)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='技能目录之外的新文件夹')
    parser.add_argument('--host', choices=HOSTS, default='codex', help='调用宿主；默认 codex，保留旧命令')
    args = parser.parse_args()
    try:
        prepare(args.out, host=args.host)
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    print('已准备原始材料和 TASK.md：' + str(args.out.resolve()))
    print('把 TASK.md 与原始材料交给 ' + args.host + ' 执行。此命令未改稿、未绘图、未安装依赖。')
    print(environment_summary(json.loads((args.out / 'environment.json').read_text('utf-8'))))


if __name__ == '__main__':
    main()
