# 三层共卷：整体与局部使用同一几何

![三层连续卷绕及同一尾端的局部放大](selected/figure.png)

主体展示三层材料共同卷绕，局部沿同一尾端露出层序。虚线连接重复放大的区域，实线将标签接到各自材料。**原创几何演示，没有实测数据、传输机制或性能含义。**

**[PDF 原尺寸](selected/figure.pdf)** · [SVG](selected/figure.svg) · [PNG](selected/figure.png) · [绘图源码](build_figure.py) · [160 mm 入稿 PDF](document/clean.pdf) · [Word](document/clean.docx)

## 从能看清，到更容易看懂

| 前版 | 本版 |
|---|---|
| ![前版：直立主体与平面尾端色条](../co-wound-laminate/selected/figure.png) | ![本版：斜置主体与尾端角部](selected/figure.png) |

前版尾端截面能区分颜色，但像一块独立色条。现在局部取自同一网格的角部：三层顶面和尾端同时出现，与整体的选区更容易对应。斜置主体留出完整轮廓，光照让外层曲面与平尾的转接可辨。

三层和支承管的顶点、厚度、两圈路径均未改变。没有剥开材料，也没有增加层。画布仍为 **160 × 95 mm**，标签为 **10–11 pt**；改进不靠扩大画布或缩小字。

## 两个构图，为什么选这个

| 构图 | 优点与代价 |
|---|---|
| [直立候选](candidates/upright.png) | 轴向容易辨认，顶部层序清楚；主体略显细长，尾端与局部的联系较弱。 |
| [斜置首稿](candidates/diagonal-first.png) | 整体轮廓更突出，曲面转接更明显；首稿标签引线过密。 |
| [最终斜置版](selected/figure.png) | 保留主体与角部视图，按实际落点顺序整理 A/B/C 引线；直立方向不如前一方案直接。 |

这里的选择服务于“整体与同一尾端”的阅读目标。若任务要核对每一圈路径，应另选端视图，不能仅靠这张透视示意。

## 重建图与 Word

在仓库根目录运行，输出目录必须尚不存在：

```powershell
python examples/co-wound-editorial/build_figure.py --out editorial-rebuilt --skill . --font C:/Windows/Fonts/arial.ttf --bold-font C:/Windows/Fonts/arialbd.ttf --pdftoppm <pdftoppm完整路径>
python examples/co-wound-laminate/build_document.py --image editorial-rebuilt/figure.png --title "Three layers, one continuous winding" --body examples/co-wound-editorial/body.txt --caption editorial-rebuilt/caption.txt --out editorial-rebuilt/clean.docx
```

加 `--variant upright` 可生成直立候选。依赖 NumPy、Pillow、ReportLab、python-docx 与 Poppler；Word 转 PDF 另用 LibreOffice 或你的文档工具。

几何复用本仓库 [build_laminate.py](../co-wound-laminate/build_laminate.py)，表面由 [surface_renderer.py](../../scripts/surface_renderer.py)重建。SVG/PDF 的标签和线条为矢量，曲面是位图；修改曲面需改源码并重新生成，不是逐面可编辑的全矢量文件。这里用三维网格投影和简单光照，不是物理场仿真。

<details>
<summary>检查范围和保留记录</summary>

[灰度](selected/grayscale.png) · [一种近似色觉预览](selected/deuteranopia-approx.png) · [生成参数](selected/record.json) · [本轮核对](validation.json)

已比较顶点及材料身份、实际输出尺寸、标签归属和同一尾端的对应；检查精确交付的 Word/PDF。视觉选择属于维护者的模型辅助检查，没有真人盲测或作者审美认可。灰度和近似色觉预览不等于完整无障碍测试。

本例是对已有公开构造案例的继续设计，不作为未见材料上的独立技能测试。旧图与旧文档保留在 [co-wound-laminate](../co-wound-laminate/README.md)。

</details>
