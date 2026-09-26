# 层板文字局部精修

原始结构任务见 [source.md](source.md)。本例检验成熟度问题可以用局部精修解决，不强迫每轮换构图。三层板保持数量、上下顺序、几何和字重，调整 L1 与 L3 的文字明暗；L2 的白字在深色面上保持不变。

`python build.py --font FONT.ttf --bold-font BOLD.ttf --pdftoppm PATH --out NEW_DIR` 实际导出两版可编辑 SVG、PDF 和 PNG。Python 依赖 ReportLab，字体和 Poppler 由宿主提供。使用 `audit_svg_labels.py ... --canvas-background "#FFFFFF"` 检查时，L2 的背景必须识别为深色矩形而不是画布白色。

当前成品位于 [before](exports/before/figure.svg) 与 [after](exports/after/figure.svg)。示例由维护模型生成和自审，不是独立盲生成测试。它证明一次受控样式修复和有限背景识别，不证明材料机制或所有 SVG 都能自动审阅。
