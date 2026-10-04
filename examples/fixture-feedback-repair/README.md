# 夹具图：合并正确指向、大标记与分点

唯一选定作品在 `output/selected/`。`article.md` 是既有英文全文，已引用同目录两张最终图，并包含两段准确图注和完整 48 行表格；同时交 CSV、独立 `captions.md`、alt text、坐标映射与 SVG/PDF/PNG。图 1 为 160 × 100 mm，图 2 为 160 × 80 mm。所有值和机制是固定 constructed DEMO，未运行实验。本例是知道既有反馈之后的开发修复。

图 1 保留 Pin 引线接触实际销钉圆右缘的修复；装配说明明确为 `Center right pin`。其余组装关系未改，不增加爆炸视图。

图 2 合并旧版的大轮廓与新版的分点收益：空心圆恢复 15 pt²、菱形恢复 12 pt²、描边均为 0.8 pt，实际 SVG 符号 path 与旧大标记版相同。T1/T2 保持独立水平区域，在其中只移动无物理意义的 x 位置，并使用原有面板间空白增加可用横向宽度；画布、字体、纵轴范围和所有 y 值不变。密集组不再用缩小符号换取分点。

代价是同次安装在不同面板的 x 位置可能不同。正式 Figure 2 图注已说明横向偏移不具物理尺度或安装顺序含义；记录身份通过原始 CSV 与 `plot_coordinates.json` 保留。不能按相同 x 位置跨面板配对安装。

全部 96 个实际 SVG 标记中心按原始源行核对，均对应 48 行数据的两项最大值；CSV 字节和 48 行表字段完整。联合通过数仍为 T1 的 6/0/6/6、T2 的 0/0/6/0，各分母 6。实际圆/菱形轮廓最小间隙为 0.231465 pt，菱形间为 0.676459 pt；这只是无重叠的几何检查。正常、灰度和 deuteranopia 模拟的 96 dpi 图已实际打开，独立 SVG 导入亦已查看；没有把这些记录当作独立读者或真人测试。

`captions.md` 只含两段 `Figure N. ` 正式图注。以 `Figure 2 compares ...` 开始的结果解释仍在完整正文，未混入图注文件。正文除正式图注外与评前选稿相同。过程失败和较差候选保留在开发档案，不放入本包 selected。

`checks/numeric-and-glyph-audit.json` 给出全部实际点、源值、符号和表格检查；`checks/portable-rebuild.json` 给出异目录重建；`REPORT.md` 及 `after-review-comparison.pdf` 保留修订依据和 160 mm 原尺寸对照。Word 入稿、独立复审及作者接受仍另验。

## 重建

保持 `source/`、`input/` 同级；`source/article_final.md` 是正文生成输入。需要 Python、Matplotlib、NumPy、Pillow、pypdf，不需联网或图像 API。

```text
python -B -X utf8 source/build.py --revision final --out NEW_DIR
```

直接在 `NEW_DIR` 生成两图、全文和数据；不要覆盖非空输出目录。如 Matplotlib 位于已有单独路径，使用 `rebuild.ps1 -Python PYTHON -MatplotlibPath MODULE_ROOT -Output NEW_DIR`，脚本暂设模块路径并在结束后恢复。此次使用已有 Matplotlib runtime 的 DejaVu Sans；PDF 嵌字，SVG 显示需匹配字体。仅复制源和输入的异目录重建已实际执行，图像、PDF、正文、两段图注、CSV、表格及坐标文件逐字节一致。
