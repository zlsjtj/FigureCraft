# 第一次用：从材料画一张图

先用公开的两路图像放置材料，做一张 160 × 100 mm 机制图。任务没有预先给出布局，成品和评阅不放入输入。

## 1. 准备材料

按[首页](../README.md#开始使用)安装后，在 PowerShell 运行：

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
python (Join-Path $skillRoot 'scientific-figure-studio/scripts/first_run.py') --out './FigureCraft-try'
```

`python` 要指向可用的 Python 3；若本机命令是 `python3`，相应替换。输出目录必须不存在，并放在技能文件夹外。命令只复制原始说明、草稿和结果表，生成 `TASK.md`；**不调用模型、不绘图，也不安装依赖**。材料全部是原创教学构造值。

## 2. 交给 Codex

在一个新的 Codex 会话中，把路径换成上一步打印的绝对路径：

```text
请执行 C:/你的试用目录/FigureCraft-try/TASK.md 中的首次试用任务。
```

Codex 应先判断这张图要解释什么，再决定对象、关系与标签，输出源码、SVG/PDF/PNG、英文图注和简短中文选择说明。输出放入独立 `output/`，原始材料保留。

准备命令只需 Python 标准库；现有导出流程使用 ReportLab、Pillow、NumPy、pypdf，另需可用字体和 Poppler。`environment.json` 只是查找记录，未找到可能是程序不在 PATH 上；找到也不等于已导出成功。[依赖与工具说明](usage.md)提供后续命令。字体应使用你有权使用的文件，不随仓库分发。

## 3. 在实际尺寸下看

用 PDF 阅读器按实际大小查看，或将图以 160 mm 宽插入文档。两路输入与输出能对应吗？共用关系和处理动作会不会读混？没有长句提示时，主要关系是否仍然清楚？细节不应靠缩小标签塞进去。

完成后再看[公开案例](../examples/paired-placement/README.md)。它保留了不同构图及选择理由；不要求新生成图逐像素复刻。比较对象关系和阅读顺序，不只比较颜色。

## 只想重建现成图？

这与让技能重新生成不同。进入仓库中的 `examples/paired-placement`，先把字体和 Poppler 路径换成自己的，再运行：

```powershell
python source/build.py --out rebuilt --variant vertical --font /path/to/regular.ttf --bold-font /path/to/bold.ttf --pdftoppm /path/to/pdftoppm
```

这会按已有源码重建选定构图。`rebuilt` 必须是新目录；Windows 可使用 `C:/Windows/Fonts/arial.ttf` 与 `arialbd.ttf`，但仍需确认文件存在及使用权限。输出可用于检查依赖和导出，不证明模型已经理解了新任务。

准备器的保护性检查：`python tests/test_first_run.py`（在仓库根目录）。它也已纳入现有单元测试发现入口。[验证记录](first-use-validation.md)分别记录任务准备和固定源码重建。
