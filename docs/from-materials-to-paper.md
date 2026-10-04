# 让一张科研图把整体与局部连起来

三层材料一起卷绕，再伸出一个相邻接触的平直尾端。图既要交代整体形态，也要让读者看见层序。这个案例展示 FigureCraft 怎样在同一几何下比较构图，并把选定方案做成可继续修改的图件。

[![三层共卷，局部放大同一尾端角部](../examples/co-wound-editorial/selected/figure.png)](../examples/co-wound-editorial/README.md)

*原创几何示意；没有实测尺寸、传输过程或性能含义。曲面为位图，标签和引线为矢量。*

## 局部先要回答“来自哪里”

前图已经能分清三种颜色，但放大的尾端面像一条独立色带。现在局部直接取自同一尾端的角部：三层顶面与端面一起出现，轮廓能与整体选区对应，虚线再说明放大关系。

<details>
<summary>展开前图，比较局部如何表达</summary>

![前图：直立主体与尾端平面色条](../examples/co-wound-laminate/selected/figure.png)

</details>

三层和支承管的顶点、厚度及两圈路径没有改变。局部是重复放大的同一位置，没有剥开材料或增加一组层。

## 用构图与光照解释形体

直立方案便于看轴向；斜置方案更突出完整轮廓，外层曲面与平尾的转接也更清楚。这张图选择斜置，同时保留候选供比较。首稿的引线较拥挤，最后按标签实际落点的顺序整理。

画布保持 160 × 95 mm，标签为 10–11 pt。光照只帮助看清表面，不编码实测场量。若要逐圈核对所有路径，端视图比这张透视图更合适。

**[打开前后图与候选](../examples/co-wound-editorial/README.md)** · [Python 图源](../examples/co-wound-editorial/build_figure.py) · [SVG](../examples/co-wound-editorial/selected/figure.svg) · [PDF](../examples/co-wound-editorial/selected/figure.pdf) · [实际入稿 PDF](../examples/co-wound-editorial/document/clean.pdf)

修改几何、相机与光照后，可运行源码重建曲面；SVG 中的文字与引线可单独修改。

## 对象不同，构图也应不同

[共享记录案例](../examples/paired-placement/README.md)用共同引用支线与处理箭头区分“共用什么、分别处理什么”；[装配剖面案例](../examples/cross-lap-trial/README.md)沿剖切位置解释互补缺口。它们适合不同问题，不必套进同一个框图。

## 自己试一次

[按客户端安装](install.md)，再[下载公开材料画一张机制图](first-use.md)。试用材料是另一个关系表达任务，完成后再与案例对照。有自己的材料时，可以这样发任务：

```text
使用 scientific-figure-studio，根据材料重画这张机制图。
先判断读者最需要看懂的关系，再选择构图、对象和必要标签。
保持科学含义和数据不变，按实际入稿宽度检查。
交付可编辑图源、SVG/PDF/PNG、图注和前后对照，保留原文件。
```

拿到图后，先看对象、标签与关系能否读对，再看原尺寸下的层次和阅读负担。[反馈一处具体效果或问题](https://github.com/zlsjtj/FigureCraft/issues/new?template=usage.yml)，有允许公开的小图就能讨论。

<details>
<summary>复制短介绍，分享这个案例</summary>

```text
FigureCraft 是一套科研绘图技能：先理清研究对象和关系，再选择构图、造型与语义配色。机制、卷绕结构和装配剖面各有完整案例，能直接看前后图、方案取舍和实际入稿效果。

图件附源码、SVG/PDF/PNG 和重建方法。提供 Claude、Codex、WorkBuddy 安装入口，原创部分采用 MIT 许可。可以先下载公开材料，画一张图试试。
https://github.com/zlsjtj/FigureCraft
```

配图用[完整卷绕图](https://raw.githubusercontent.com/zlsjtj/FigureCraft/main/examples/co-wound-editorial/selected/figure.png)，并注明“原创几何示意，曲面由源码重建，标签为矢量”。需要展示其他画法，可用[装配与剖面](https://raw.githubusercontent.com/zlsjtj/FigureCraft/main/examples/cross-lap-trial/selected/figure.png)。

</details>
