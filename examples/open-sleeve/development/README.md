# 同一套筒的整体与间隙

本例在既有单视图、双视图及匿名评语基础上开发，不能当作未知任务的首次胜出。几何和160×95 mm版面固定。旧单视图集中显示完整形体，旧双视图更容易看清非接触关系；这次让较大的斜视图负责形状，小轴向投影负责间隙，并把开口标签锚到缺失角区。

首稿的38度俯视使内芯上端与后内缘近似相切。一次自修改为48度，保留全部尺寸、方位和滚转；再调整三处标注。首稿与最终稿均保留，实际过程见 [自审记录](first-review.md)。相机角度是本例选择，不是通用推荐。增加辅助图的代价是仍需一次视图对应，未声称每项审美都优于单图。

依赖：Python、NumPy、Pillow、ReportLab、pypdf、Poppler，以及显式提供的Arial常规/粗体或兼容字体。在仓库根目录运行；输出目录必须为新目录：

```powershell
python examples/open-sleeve/development/build_figure.py --input examples/open-sleeve/development/input.md --out output/sleeve-development --revision final --font <regular.ttf> --bold-font <bold.ttf> --pdftoppm <pdftoppm.exe>
```

首稿可将 `--revision final` 改为 `--revision first`；历史首稿源文件另保存在 first。SVG/PDF含表面位图及可独立编辑的轴向矢量、文字、引线。改曲面形状须修改源码并重建，不能宣称全矢量。字体9/10.5 pt；数值、网格与连接性检查只覆盖它们声明的范围，模型读图不是作者认可。
