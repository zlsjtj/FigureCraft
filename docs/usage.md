# FigureCraft 进阶使用与验证

第一次使用可先走[短任务入口](first-use.md)；想先看效果，可按问题选[三个代表案例](examples.md)。

[返回首页](../README.md) · [多宿主安装](install.md) · [安装包与本轮验证](multihost-validation.md)

这里收录依赖、脚本命令和检查方法。命令从仓库根目录运行；输出目录应为新目录。先通过宿主模型完成写作或构图，再用这些工具执行受控修改和导出。

技能 ZIP 包含当前安装、试用和依赖说明，可直接运行包内脚本。下文的 `tests/` 回归命令用于完整源码仓库；上传包不附整套测试。未收录的拓展示例链接指向 GitHub，查看它们需要网络；本地候选新增的下载链接须等对应文件发布后才能在线使用。已有 ZIP 可直接安装，首次材料也可用包内 `scripts/first_run.py` 准备。

## 先确认执行环境

如果只是使用宿主完成任务，直接交给它 TASK.md 与材料即可。下面的命令用于手动运行脚本；准备材料不需要安装整套依赖。

```text
python -c "import sys; print(sys.executable)"
```

先看这条命令实际指向哪里。本机就曾指向 LibreOffice 自带的 Python：材料准备成功，绘图却缺少包。若是其他软件的内置环境，先选用宿主提供的运行时或独立 Python；不要直接往办公软件目录安装依赖。`ModuleNotFoundError` 时，应在**执行脚本的同一 Python 环境**中检查包，而不是反复用另一个 pip 安装。

使用自己管理的独立 Python 时，推荐新建隔离环境。Windows PowerShell 示例（先确认 `python` 是你选定的解释器）：

```powershell
python -m venv ../FigureCraft-env
$skillPython = (Resolve-Path '../FigureCraft-env/Scripts/python.exe').Path
& $skillPython -m pip install -r requirements-core.txt
& $skillPython scripts/first_run.py --out ../FigureCraft-try
```

不需要激活环境；后面的 `python ...` 命令都改为 `& $skillPython ...`。macOS / Linux 使用同一环境的 `bin/python`。已由宿主准备好依赖时可直接使用其解释器，无需重复创建环境。字体、LibreOffice 和 Poppler 仍是单独的原生依赖；找不到 `pdftoppm` 时提供实际路径，不能把 PDF 已生成当成 PNG 也已导出。

## 运行示例

需要 Python，以及自己提供的可用字体。PNG 导出需要 Poppler 的 `pdftoppm`；字体和原生工具不随仓库分发。

```powershell
python -m pip install -r requirements-core.txt
$figureFont = (Join-Path $env:WINDIR 'Fonts/arial.ttf')
$figureCjk = (Join-Path $env:WINDIR 'Fonts/msyh.ttc')
$figureRaster = (Get-Command pdftoppm).Source
python scripts/probe_runtime.py --font $figureFont --cjk-font $figureCjk --pdftoppm $figureRaster --out runtime.json
python examples/material-polished-v17/build_material_v17.py --out material-source
python scripts/render_figure.py material-source/scene_A.json --out material-A --font $figureFont --pdftoppm $figureRaster --qa-views
python scripts/check_figure.py material-A --placement-width-mm 160
```

命令在仓库目录执行，输出目录应为新目录。其他系统替换成实际字体及工具路径。`--qa-views` 输出灰度和选定色觉模拟，仍需看图；字体覆盖以实际文本为准。Windows 的 Arial 不覆盖所有数学符号，含下标的测试使用 Segoe UI。

渲染器接收场景 JSON，不直接从自然语言推断科学关系。新图先读材料、确定结构，再编写场景或沿用已有绘图代码。接口见[场景规格](../references/figure-spec.md)和[对象组件](../references/scene-components.md)。

已有 SVG 可直接使用 `audit_svg_labels.py`，不必改成场景 JSON。它检查实际字号、有限直线穿字和声明的标签区域；CSS、曲线等未覆盖内容仍待审，见[使用方法](../references/existing-svg-review.md)。

## 检查与复用

```powershell
python tests/run_all_tests.py --out test-output/current --font (Join-Path $env:WINDIR 'Fonts/segoeui.ttf') --cjk-font $figureCjk --label-font $figureFont --bold-font (Join-Path $env:WINDIR 'Fonts/arialbd.ttf') --pdftoppm $figureRaster
python tests/run_svg_label_tests.py --out test-output/svg-labels --font $figureFont --bold-font (Join-Path $env:WINDIR 'Fonts/arialbd.ttf')
python -m unittest discover -s tests -p "test_*.py"
python scripts/measure_label_load.py figure.svg --width-mm 160 --out label-load.json
```

统一入口已包含语法、原八组回归、SVG标签测试、自动发现的 `test_*.py` 和README材料示例的源码生成/渲染/检查；后两条单独测试命令用于局部复验。原先 run_all_tests.py 只覆盖八组，README另列的单元测试没有被它调用，这个缺口已修复。缺依赖、失败、超时和跳过分别记录；技术通过不意味着科学、视觉或作者审阅通过。具体执行见 [当前记录](../provenance/current-validation.md)。

技术检查、科学内容审阅和视觉审阅分别报告。`status` 是旧技术状态字段；判断完整状态应看 `overall_status`。缺少科学或视觉审阅时保留 `REVIEW_REQUIRED`，脚本不会替作者确认图片。

`examples/` 包含独立场景和示意数据，`templates/` 提供语义契约及审阅模板。重复局部图、装饰面和图例绑定原对象；量化图保持二维。机制图主标签按实际尺寸以 10–11 pt 为起点，小于 8 pt 的情况需要修复或注明。

## 来源与边界

当前支持有限可检查的矢量 2.5D，不能自动证明科学含义，也不覆盖任意三维实体、所有 PDF 编辑器和全部色觉条件。每次改图仍需检查最终入稿页面。

PDF 字号检查器来自固定版本的 nature-skills，原始许可证和 NOTICE 保留在 `vendor/`，其他来源见[来源说明](../provenance/upstream-sources.md)。参考截图和字体未随仓库发布，配色标注不代表任何期刊的官方规范。许可状态见 [LICENSE.md](licensing.md)。

公开仓库保留当前通用代码、示例和测试；本机路径、私人论文、完整代理日志和重复历史输出留在本地归档。

[共享参考与独立记录案例](../examples/common-reference-demo/README.md)保留原有两种构图；[继续开发的成图](../examples/common-reference-demo/dev/REVIEW.md)把对象辨识和就近标签结合起来。开发成图与独立新任务的效果分开记录，没有将新版选作全面优胜者。

[箱角解锁新材料试用](../examples/bin-latch/README.md)保存普通提示、旧技能、新技能的首次产物与匿名比较。新版的状态对照更直接，但并非全面胜出；反馈后修复单独记录。

[两路共用放置记录](../examples/paired-placement/README.md)展示如何从处理框转向对象变化，并保留同尺寸前后图、取舍理由和生成源码。
