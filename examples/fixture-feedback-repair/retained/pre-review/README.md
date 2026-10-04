# 夹具反馈修复：不能止于指出三个问题

选定作品为 `output/selected/`：既有英文短文引用两张修后图，包含完整48行表、CSV、两段正式图注和 alt text。全为固定构造 DEMO，未运行实验。原首稿、原上轮终稿及原独立评语在 `retained/`；本次已知道这些评语，明确属于开发修复。

1. Pin 引线原来停在槽面内；仅把近端从 x=127 改到 x=125.5，接触原销圆右边（圆心123.5、半径2，均为示意坐标）。实际 SVG 差异在 `checks/fixture1-svg.diff`，其余形状与装配时序保留。
2. 结果图中近值菱形相互覆盖。六次安装现在用固定的横向记录列，T1/T2 保持独立符号和位置，同一安装在两个指标面板中保持相同横向顺序。仅改变无物理尺度的横向位置及标记大小，不移动数值轴坐标。代价是标记更小、类别内宽度更大；160 mm、灰度与色觉模拟已实际查看。最小点中心间距3.2907 pt，大于3.196 pt的最宽包络；这个数不代替视觉查看。
3. 独立图注抽取只匹配 `Figure N. `，不再把 `Figure 2 compares …` 正文结果段混入；该段仍留在完整短文。不是删除科学内容。

全部96个**实际导出SVG**数据点逐一核对48行CSV的纵坐标；表行及CSV保留，联合合格数仍为T1的6/0/6/6、T2的0/0/6/0，各分母6。源数据、实际点坐标、短文保留、图注数量及销端点检查分别记录，不用“有96个图元”代替“96个值正确且可辨”。原始表中的热行程与断裂值也完整保留，不把两张指标图当作全部数据。

## 重建

使用既有 Matplotlib 项目，不换成新画图引擎。需要 Python、Matplotlib、NumPy、Pillow、pypdf；DejaVu Sans 由该 Matplotlib runtime 提供，PDF嵌字，SVG仍需匹配字体。无需联网或图像 API。

```text
python -B source/build.py --revision final --out NEW_DIR
```

如 Matplotlib 位于独立的已有目录，可使用 `rebuild.ps1 -Python PYTHON -MatplotlibPath MODULE_ROOT -Output NEW_DIR`；它只为该次进程设置模块搜索路径并恢复环境。源码和 `input/`、`source/article_final.md` 一起搬移，输出不能覆盖非空目录。实际从另一个目录执行了搬移重建，图像、PDF、CSV、短文、图注与点坐标记录逐字节一致，见 `checks/portable-rebuild.json`。

失败没有当成完整交付：初次模块路径未配置；两次贪心点排布无法满足间距并在导出前报错，随后选择较简单的固定记录列。开发档案保留失败目录，例子不把它们放入 selected。已实际查看最终 PNG、独立 PDF 渲染、独立 LibreOffice SVG 导入及灰度/单条件色觉图。Word 入稿、真人审美和作者认可另验，不从此例推广所有题材的稳定质量。
