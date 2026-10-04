# 怎样让机制图里的对象和关系更容易看懂？

图里步骤齐全，读者仍要沿着框和长句来回找关系。FigureCraft 先判断画面最需要讲清什么，再安排对象、连接、层次和配色。

## 让输入和结果直接对应

这个案例有两路图像。它们各自重采样，却读取同一份放置记录。图最需要回答的是：**什么共同使用，什么分别处理？**

[![两路输入在上、各自输出在下，共用记录位于中央](../examples/paired-placement/selected/figure.png)](../examples/paired-placement/selected/figure.png)

*原创构造示例；图像、坐标和条件用于说明关系。*

原图让处理框、分支和计算步骤占据主体。改图把每路输入与对应结果上下排列，共用记录留在中间。读者可以沿着同一路对象看见变化，再看两路之间共享了什么。

<details>
<summary>展开原图，比较两种组织方式</summary>

[![原图：处理框、分支和重采样流程占据主体](../examples/paired-placement/before/figure.png)](../examples/paired-placement/before/figure.png)

</details>

## 让连线也有明确分工

无箭头支线表示读取同一记录，向下箭头表示重采样。图内保留关键条件与一组坐标，图注承接完整读图规则和适用边界。

两版都是 160 × 100 mm，最低字号 9 pt。改图重新组织了读图路径；图注约从 135 词增至 170 词，承担了更多解释。共用记录也不意味着两路图像数据相同，或全局位置一定正确。

**[SVG 图源](../examples/paired-placement/selected/figure.svg)** · [PDF](../examples/paired-placement/selected/figure.pdf) · [图注](../examples/paired-placement/selected/caption.txt) · [前后对照与重建方法](../examples/paired-placement/README.md)

画连续结构时，可以用整体与局部展开；画装配关系时，可以用剖面和状态变化。[卷绕结构](../examples/co-wound-laminate/README.md)与[装配剖面](../examples/cross-lap-trial/README.md)展示了另外两种画法。

## 用你自己的材料试一次

提供对象、关系、必要数值和旧图，先重画一张机制图：

```text
使用 scientific-figure-studio，根据材料重画这张机制图。
先判断读者最需要看懂的关系，再选择构图、对象和必要标签。
保持科学含义和数据不变，按实际入稿宽度检查。
交付可编辑图源、SVG/PDF/PNG、图注和前后对照。
```

**[下载安装](https://github.com/zlsjtj/FigureCraft/releases/latest)** · [拿公开材料试用](first-use.md) · [32 秒作品导览](quick-tour/tour.gif) · [项目首页](https://github.com/zlsjtj/FigureCraft)

导览展示已完成作品；输入材料、不同方案与源码均在案例页。

<details>
<summary>复制一段短介绍，分享给需要画图的人</summary>

```text
机制图已经画满，关系还是难读？FigureCraft 从研究材料出发，先理清对象和关系，再设计构图与语义配色。仓库提供机制图、连续结构和装配剖面的案例，附可编辑图源、SVG/PDF/PNG 与重建脚本。Claude、Codex、WorkBuddy 都有安装入口。
https://github.com/zlsjtj/FigureCraft
```

配图：[下载分享封面](https://raw.githubusercontent.com/zlsjtj/FigureCraft/main/docs/social-preview/social-preview.png)。

</details>
