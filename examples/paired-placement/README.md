# 两路图像，共用一份放置记录

这张图要让读者看出：两路输入各自重采样，却读取同一份放置记录。**图像、坐标和条件均为原创构造示例，不是实验结果。**

![两路输入在上、各自输出在下，共用记录居中](selected/figure.png)

[SVG](selected/figure.svg) · [PDF](selected/figure.pdf) · [PNG](selected/figure.png) · [图注](selected/caption.txt) · [绘图源码](source/build.py)

## 为什么这样摆

每路输入与结果上下对应，读者可以沿对象追踪变化。中央记录通过无箭头支线表示共同引用；向下箭头表示重采样。图内保留选择条件和一组坐标例子，完整读图规则与适用边界放在图注。

<details>
<summary>查看原图：处理框和分支占据主体</summary>

![原图中的处理框、分支和重采样流程](before/figure.png)

</details>

两版均为 160 × 100 mm，最低字号 9 pt。改图减少了来回找对象的需要，但图注约从 135 词增至 170 词；这项取舍没有被记作“所有文字都减少”。

## 自己试一次

[下载原始材料并调用技能](../../docs/first-use.md)，或查看[原始条件](source/inputs/)。前者由所用模型重新设计；下面的脚本重建本页选定图。

## 重建

需要Python、reportlab、pypdf、Pillow、numpy、Arial正常/粗体字体和Poppler。输入在source/inputs，生成器参数化且不依赖私有文稿。

```powershell
python -B source/build.py --out rebuilt --variant vertical --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
python -B source/verify.py --root . --rendered rebuilt --rebuild-out verification-rebuilt --receipt verification.json --font ARIAL_TTF --bold-font ARIAL_BOLD_TTF --pdftoppm PDFTOPPM
```

输出目录必须不存在；导出SVG、矢量PDF、PNG、灰度及选定色觉模拟、图注和替代文本。固定源码已跨目录重建；自然语言创作与模型审阅是另一层验证。本例是开发后作品，今后不再作为未见材料。

第二条命令核对19项具体几何与语义条件，并从源码再生成一份文件，与第一份的7个导出文件逐一比对。它不评价美观程度，也不把固定源码重建当作技能自主创作的证明。

<details>
<summary>候选比较与评阅范围</summary>

这是原创MosaicPair构造演示，不是实验图像或研究结果。科学任务是两路tile读取同一份放置记录，分别重采样到各自mosaic。图内没有规定的掩膜形状不补画。

原图让配准、回退和处理框占据主体；新图让输入与其放置后的对象上下对应，共用记录置于中央。对两个不同构图进行匿名模型比较后，选择成对上下结构，再吸收另一候选的read t标签与共同坐标例子。普通支线表示引用，箭头表示重采样。读者可直接跟踪对象的位置变化。

两版均160×100 mm，最低9 pt，没有缩字或扩大画布。代价是图注由约135词增至约170词，用于承接选择规则、未知掩膜和适用边界。图形变清楚不等于全文文字都变少。首评与定向复验保留，没有真人审美认可。

</details>
