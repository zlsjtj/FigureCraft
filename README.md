# FigureCraft｜科研绘图与配色

FigureCraft 根据科学对象、关系和数据组织图形。它用于机制图、数组与寄存器图、分层材料、包覆与剖面、定量结果及整套论文配图，交付可编辑源、SVG、PDF、PNG 和检查记录；混合表面的可编辑范围单独说明。

当前内容版本 **1.21.0**，调用标识 **`$scientific-figure-studio`**。这一版保留首稿与候选的得失，补齐[开口套筒的合并修复](examples/open-sleeve/development/README.md)。范围见[1.21验收](provenance/validation-1.21.md)，不以版本号证明审美达标。

前一轮未推送时的[本地记录](provenance/local-video-20261001.md)保留其历史状态。本次另有[U形护架新材料试用](examples/u-guard/README.md)，其剩余读图问题与改善并列记录。

## 本轮改动

1.20把整体与局部视图的选择落实到[共卷层合带](examples/co-wound-laminate/README.md)：局部要显露主视图遮住的关系，不能只把同一个表面放大。保留首稿、两种构图、同源几何和实际入稿。另用未参与开发的[悬桥结构](examples/suspended-ribbon/README.md)对照旧、新技能；截面使悬空关系更直接，单视图则更凝练，最终取舍与反馈修复如实保留。

此前[快照状态](examples/snapshot-state/README.md)、[连续表面入口](references/surface-rendering.md)等仍可使用。[1.20验收](provenance/validation-1.20.md)区分源码重建、新材料生成、模型评阅和作者认可。图形能力有具体增量，尚未证明在所有新题材上稳定达到同样完成度。

![同一几何的整体与尾端裁切，原创DEMO](examples/co-wound-laminate/selected/figure.png)

## 其他示例

以下是原创结构示意，包含六个包覆颗粒、两层支撑和同一颗粒的局部视图。尺寸为示意值，不表示实验结果。

![整体与斜剖面](examples/material-polished-v17/A/figure.png)

![涂层开口与完整曲面内核](examples/material-polished-v17/B/figure.png)

A 同时切开涂层和内核；B 只打开涂层，保留内核曲面。两者使用不同几何，局部放大不会算成新增颗粒。[源脚本](examples/material-polished-v17/build_material_v17.py)与导出的 SVG 均可编辑。这是矢量 2.5D，不是三维实体仿真。

## 安装与调用

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
git clone https://github.com/zlsjtj/FigureCraft.git (Join-Path $skillRoot 'scientific-figure-studio')
```

已有同名目录时先备份。在新会话中显式调用，例如：

> 使用 $scientific-figure-studio 重画这张机制图。先核对对象、关系和数量，再设计构图与语义配色。按 160 mm 入稿宽度检查字号，保留源文件，给出实际前后对照和未解决项。

160 mm 只是这个例子的目标尺寸，应按实际版式调整。只换色的请求会锁定内容和布局；重设计可以改变构图，但不能擅自补科学机制或测量值。

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

渲染器接收场景 JSON，不直接从自然语言推断科学关系。新图先读材料、确定结构，再编写场景或沿用已有绘图代码。接口见[场景规格](references/figure-spec.md)和[对象组件](references/scene-components.md)。

已有 SVG 可直接使用 `audit_svg_labels.py`，不必改成场景 JSON。它检查实际字号、有限直线穿字和声明的标签区域；CSS、曲线等未覆盖内容仍待审，见[使用方法](references/existing-svg-review.md)。

## 检查与复用

```powershell
python tests/run_all_tests.py --out test-output/current --font (Join-Path $env:WINDIR 'Fonts/segoeui.ttf') --cjk-font $figureCjk --label-font $figureFont --bold-font (Join-Path $env:WINDIR 'Fonts/arialbd.ttf') --pdftoppm $figureRaster
python tests/run_svg_label_tests.py --out test-output/svg-labels --font $figureFont --bold-font (Join-Path $env:WINDIR 'Fonts/arialbd.ttf')
python -m unittest discover -s tests -p "test_*.py"
python scripts/measure_label_load.py figure.svg --width-mm 160 --out label-load.json
```

统一入口已包含语法、原八组回归、SVG标签测试、自动发现的 `test_*.py` 和README材料示例的源码生成/渲染/检查；后两条单独测试命令用于局部复验。原先 run_all_tests.py 只覆盖八组，README另列的单元测试没有被它调用，这个缺口已修复。缺依赖、失败、超时和跳过分别记录；技术通过不意味着科学、视觉或作者审阅通过。具体执行见 [当前记录](provenance/current-validation.md)。

技术检查、科学内容审阅和视觉审阅分别报告。`status` 是旧技术状态字段；判断完整状态应看 `overall_status`。缺少科学或视觉审阅时保留 `REVIEW_REQUIRED`，脚本不会替作者确认图片。

`examples/` 包含独立场景和示意数据，`templates/` 提供语义契约及审阅模板。重复局部图、装饰面和图例绑定原对象；量化图保持二维。机制图主标签按实际尺寸以 10–11 pt 为起点，小于 8 pt 的情况需要修复或注明。

## 来源与边界

当前支持有限可检查的矢量 2.5D，不能自动证明科学含义，也不覆盖任意三维实体、所有 PDF 编辑器和全部色觉条件。每次改图仍需检查最终入稿页面。

PDF 字号检查器来自固定版本的 nature-skills，原始许可证和 NOTICE 保留在 `vendor/`，其他来源见[来源说明](provenance/upstream-sources.md)。参考截图和字体未随仓库发布，配色标注不代表任何期刊的官方规范。许可状态见 [LICENSE.md](LICENSE.md)。

公开仓库保留当前通用代码、示例和测试；本机路径、私人论文、完整代理日志和重复历史输出留在本地归档。

[共享参考与独立记录案例](examples/common-reference-demo/README.md)保留原有两种构图；[继续开发的成图](examples/common-reference-demo/dev/REVIEW.md)把对象辨识和就近标签结合起来。开发成图与独立新任务的效果分开记录，没有将新版选作全面优胜者。

[箱角解锁新材料试用](examples/bin-latch/README.md)保存普通提示、旧技能、新技能的首次产物与匿名比较。新版的状态对照更直接，但并非全面胜出；反馈后修复单独记录。
