# 同一接口如何展开：已知反馈后的开发例

选定图是 `output/selected/`，160×100 mm；它与 `caption.md`、`alt_text.md`、`figure_spec.json` 一起交付。全部事实来自固定构造 DEMO `input/notes.md`，未运行物理或计算实验。此例继续修复 `edge-state-scene` 的读图代价，不覆盖早例、旧首测或独立评语。

旧图保留 W0 左、W1 右，但复制路径需向左跟踪；源边、slot 副本、ghost、数值边界是相似条带，no-match 条件悬置。`retained/prior-selected` 保留旧图。新 A 仍围绕空间邻接，B 则保留四分块整体定位，并按使用顺序展开同一接口，W0 局部明确旋转 180°。两版相同科学事实、相同尺寸，实际图在 `retained/first`；`candidate-comparison.pdf` 第 1 页对照 A/B，第 2 页对照 B 首稿与所选修复。

选 B 后自修：16 标签避开释放虚线，接到实际匹配检查的失败支路；接受更新的边界明确为 east edge，用金色与蓝色副本区别，slot 是装着值的容器。读取复制、匹配、使用时顺序更直接。代价是多一处旋转说明，查空间邻接要看整体定位图；这不意味着局部旋转总是更好。需要独立读者检验16的失败是否被误读为17的失败，不能只以作者熟悉机制为通过。

这次原始五张 JPEG 均已实际打开，来源哈希及观察记录在 `checks/reference-observation.json`。学习对象层级、共同边界和整体/局部分工，没有复用医学机制或复制图片。正常色、灰度和单一 deuteranopia 模拟均由生成代理查看；三种状态仍靠容器、位置和名称区分。外来 SVG 检查四个网格/文字接触疑点实际由后绘制白底遮住，原待审结果保留；独立 LibreOffice SVG 导入也已查看。浏览器文件协议不可用，未作浏览器兼容声明。

## 重建

需要 Python、ReportLab、pypdf、Pillow、NumPy、Poppler，以及明确可用的字体。把 `source/` 和 `input/` 一起移动即可，从任意工作目录运行；输出路径必须不存在。

```text
python -B source/build.py --revision selected --out NEW_DIR --font FONT.ttf --bold-font BOLD.ttf --pdftoppm PATH_TO_PDFTOPPM
```

`--revision first` 重建两个开发候选。选定图的图注、alt text 与规格从 `input/` 复制；数值不是从图中反推。PDF 全矢量且嵌字，SVG 为可编辑图元与文本，PNG 为渲染。搬移后源码实际运行，SVG/PNG/场景及文字附件 SHA 完全一致；PDF 的创建时间和文档 ID 可变，页内容流与文本完全一致。此为固定源码重建，不是新的自然语言生成或作者认可。
